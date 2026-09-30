from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from decimal import Decimal
import json
import datetime
import calendar
from datetime import timedelta
from django.db.models import Q, Sum, Count, F
from .models import (
    Product, Category, CashRegister, Shift, Sale, SaleItem, 
    Supplier, SupplierTransaction, StockEntry, StockEntryItem, SystemLog, log_action
)
from .api_client import CSharpApiClient

def get_or_create_active_shift(user=None):
    register, _ = CashRegister.objects.get_or_create(register_code="KASA-01", defaults={'name': 'Kasa 1 (Ana Kasa)', 'is_active': True})
    shift = Shift.objects.filter(cash_register=register, is_closed=False).first()
    if not shift:
        shift = Shift.objects.create(
            cash_register=register,
            cashier=user if (user and user.is_authenticated) else None,
            opening_float=Decimal('500.00'), # Varsayılan 500 TL açılış devir parası
            expected_cash=Decimal('500.00')
        )
    return register, shift


def pos_screen(request):
    """
    Market Kasa Satış Ekranı Ana Görünümü (POS Interface)
    C# .NET 8 Backend API Entegreli Katman
    """
    register, shift = get_or_create_active_shift(request.user)
    quick_buttons = Product.objects.filter(is_quick_button=True, is_active=True).order_by('quick_button_order')
    categories = Category.objects.filter(is_active=True).order_by('display_order')

    context = {
        'register': register,
        'shift': shift,
        'quick_buttons': quick_buttons,
        'categories': categories,
        'cashier_name': (shift.cashier.get_full_name() or shift.cashier.username) if (shift and shift.cashier) else (request.user.get_full_name() or request.user.username if request.user.is_authenticated else "Kasiyer"),
        'csharp_backend_active': True
    }
    return render(request, 'pos_screen.html', context)


def search_barcode(request):
    """
    Barkod ve Terazi/Tartılı Ürün Çözümleme API
    Ultra-Hızlı Yerel Sorgulama (Önce Yerel İndeksli DB, İhtiyaç Halinde C# Fallback)
    Gecikmeyi (3 sn lag) tamamen ortadan kaldırır.
    """
    barcode = request.GET.get('barcode', '').strip()
    if not barcode:
        return JsonResponse({'success': False, 'message': 'Barkod girilmedi.'}, status=400)

    # 1. Yerel Veritabanı Standart ve Koli Barkodu Eşleşmesi (Anında < 1ms)
    product = Product.objects.filter(is_active=True).filter(
        Q(barcode=barcode) | Q(secondary_barcode=barcode)
    ).first()
    if product:
        return JsonResponse({
            'success': True,
            'product': {
                'id': product.id,
                'name': product.name,
                'barcode': product.barcode,
                'sell_price': float(product.sell_price),
                'vat_rate': float(product.vat_rate),
                'unit': product.unit,
                'is_weighted': product.is_weighted,
                'stock_quantity': float(product.stock_quantity),
            },
            'quantity': 1.0,
            'is_weighted_barcode': False
        })

    # 2. Yerel Veritabanı Terazi / Tartılı Barkod Ayrıştırma (27 / 28)
    if len(barcode) == 13 and (barcode.startswith('27') or barcode.startswith('28')):
        product_code = barcode[2:7]
        raw_quantity = barcode[7:12]

        weighted_product = Product.objects.filter(is_weighted=True, is_active=True, barcode__contains=product_code).first()
        if weighted_product:
            try:
                calculated_quantity = round(Decimal(raw_quantity) / Decimal('1000.0'), 3)
                return JsonResponse({
                    'success': True,
                    'product': {
                        'id': weighted_product.id,
                        'name': weighted_product.name,
                        'barcode': weighted_product.barcode,
                        'sell_price': float(weighted_product.sell_price),
                        'vat_rate': float(weighted_product.vat_rate),
                        'unit': weighted_product.unit,
                        'is_weighted': True,
                        'stock_quantity': float(weighted_product.stock_quantity),
                    },
                    'quantity': float(calculated_quantity),
                    'is_weighted_barcode': True
                })
            except (ValueError, ArithmeticError):
                pass

    # 3. İkincil Fallback: C# .NET 8 Web API (Sadece yerelde bulunamazsa)
    try:
        api_result = CSharpApiClient.search_barcode(barcode)
        if api_result and api_result.get('success'):
            return JsonResponse(api_result)
    except Exception:
        pass

    return JsonResponse({'success': False, 'message': 'Barkodlu ürün bulunamadı!'}, status=404)


@csrf_exempt
def process_sale(request):
    """
    Kasada Satışı Tamamlama, Fiş Oluşturma, Stok Düşme ve Kasa Sayacı Güncelleme
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Yalnızca POST istekleri kabul edilir.'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
        items_data = data.get('items', [])
        payment_type = data.get('payment_type', 'NAKIT')
        cash_paid = Decimal(str(data.get('cash_paid', 0)))
        discount_amount = Decimal(str(data.get('discount_amount', 0)))

        if not items_data:
            return JsonResponse({'success': False, 'message': 'Fişte ürün bulunmuyor.'}, status=400)

        register, shift = get_or_create_active_shift(request.user)

        # C# API Satış Çağrısı Denemesi
        csharp_res = CSharpApiClient.process_sale(shift.id, payment_type, cash_paid, discount_amount, items_data)
        if csharp_res:
            return JsonResponse({
                'success': True,
                'receipt_number': csharp_res.get('receiptNumber'),
                'total_amount': float(csharp_res.get('totalAmount', 0)),
                'cash_paid': float(csharp_res.get('cashPaid', 0)),
                'change_given': float(csharp_res.get('changeGiven', 0)),
                'created_at': timezone.now().strftime('%d.%m.%Y %H:%M')
            })

        is_return = bool(data.get('is_return', False))

        # Yerel Django İşlemi (C# API Fallback)
        today_str = timezone.now().strftime('%Y%m%d')
        today_sales_count = Sale.objects.filter(created_at__date=timezone.now().date()).count() + 1
        prefix = "IADE" if is_return else "FIS"
        receipt_number = f"{prefix}-{today_str}-{today_sales_count:04d}"

        subtotal = Decimal('0.00')
        total_vat = Decimal('0.00')

        sale = Sale.objects.create(
            receipt_number=receipt_number,
            shift=shift,
            cashier=request.user if request.user.is_authenticated else None,
            payment_type=payment_type,
            discount_amount=discount_amount,
            cash_paid=cash_paid,
            total_amount=Decimal('0.00'),
            is_return=is_return
        )

        for item_info in items_data:
            product_id = item_info.get('product_id')
            qty = Decimal(str(item_info.get('quantity', 1)))
            product = get_object_or_404(Product, id=product_id)

            # Perakende Satış Standardı: Raf Satış Fiyatı KDV DAHİLDİR.
            # Müşteriden fazla para alınmaz, genel toplam raf fiyatı üzerinden hesaplanır.
            line_total = round(qty * product.sell_price, 2)
            # Fiş ve muhasebe için iç KDV (Matrah) geriye doğru hesaplanır:
            if product.vat_rate > Decimal('0.00'):
                line_subtotal = round(line_total / (Decimal('1.00') + (product.vat_rate / Decimal('100.00'))), 2)
                line_vat = line_total - line_subtotal
            else:
                line_subtotal = line_total
                line_vat = Decimal('0.00')

            subtotal += line_subtotal
            total_vat += line_vat

            SaleItem.objects.create(
                sale=sale,
                product=product,
                product_name=product.name,
                barcode=product.barcode,
                quantity=qty,
                unit_price=product.sell_price,
                vat_rate=product.vat_rate,
                vat_amount=line_vat,
                total_price=line_total
            )

            # Anlık Stok Hareketi:
            # Satış ise stok anında düşer, Müşteri Satış İadesi ise stok anında geri artar!
            if is_return:
                product.stock_quantity += qty
            else:
                product.stock_quantity -= qty
            product.save()

        grand_total = max(Decimal('0.00'), (subtotal + total_vat) - discount_amount)
        sale.subtotal = subtotal
        sale.total_vat = total_vat
        sale.total_amount = grand_total

        # Nakit para üstü hesabı
        if not is_return and payment_type == 'NAKIT' and cash_paid >= grand_total:
            sale.change_given = cash_paid - grand_total
        else:
            sale.change_given = Decimal('0.00')

        sale.save()

        # Vardiya Sayaçlarını Güncelle
        if is_return:
            if payment_type == 'NAKIT':
                shift.total_cash_sales -= grand_total
            elif payment_type == 'KART':
                shift.total_card_sales -= grand_total
            log_action('POS', 'Müşteri Satış İadesi Alındı', f"İade Fişi #{sale.receipt_number} - İade Tutarı: {grand_total} TL ({payment_type})", user=request.user)
        else:
            if payment_type == 'NAKIT':
                shift.total_cash_sales += grand_total
            elif payment_type == 'KART':
                shift.total_card_sales += grand_total
            shift.total_sales_count += 1
            log_action('POS', 'Yeni Satış Yapıldı', f"Satış Fişi #{sale.receipt_number} - Tutar: {grand_total} TL ({payment_type})", user=request.user)

        shift.expected_cash = shift.opening_float + shift.total_cash_sales
        shift.save()

        return JsonResponse({
            'success': True,
            'receipt_number': sale.receipt_number,
            'is_return': is_return,
            'total_amount': float(sale.total_amount),
            'cash_paid': float(sale.cash_paid),
            'change_given': float(sale.change_given),
            'created_at': sale.created_at.strftime('%d.%m.%Y %H:%M')
        })

    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


def receipt_view(request, receipt_number):
    """
    80mm / 58mm Termal Fiş Yazdırma Görünümü
    """
    sale = get_object_or_404(Sale, receipt_number=receipt_number)
    return render(request, 'thermal_receipt.html', {'sale': sale})


def z_report_view(request):
    """
    Gün Sonu Kasa Kapanış Raporu (Z Raporu)
    """
    register, _ = CashRegister.objects.get_or_create(
        register_code="KASA-01", 
        defaults={'name': 'Kasa 1 (Ana Kasa)', 'is_active': True}
    )
    
    shift_id = request.GET.get('shift_id')
    if shift_id:
        shift = get_object_or_404(Shift, id=shift_id)
    else:
        # Önce açık olan aktif vardiyayı getir
        shift = Shift.objects.filter(cash_register=register, is_closed=False).order_by('-opened_at').first()
        # Eğer aktif vardiya yoksa, en son kapatılmış vardiyayı göster (böylece kapalı vardiya incelenebilir)
        if not shift:
            shift = Shift.objects.filter(cash_register=register).order_by('-opened_at').first()
        # Sistemde hiç vardiya yoksa yeni bir tane aç
        if not shift:
            register, shift = get_or_create_active_shift(request.user)

    sales = Sale.objects.filter(shift=shift).order_by('-created_at')
    recent_sales = sales[:50]
    
    # Tüm vardiyalar (geçmiş Z raporlarına geçebilmek için)
    all_shifts = Shift.objects.filter(cash_register=register).order_by('-opened_at')[:20]

    cash_sales = sales.filter(payment_type='NAKIT', is_cancelled=False).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    cash_sales = sales.filter(payment_type='NAKIT', is_cancelled=False).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    card_sales = sales.filter(payment_type='KART', is_cancelled=False).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    total_revenue = cash_sales + card_sales

    # Aktif kasiyer listesi (Yeni vardiya açılışı için)
    cashiers = User.objects.filter(is_active=True).order_by('username')

    context = {
        'shift': shift,
        'register': register,
        'recent_sales': recent_sales,
        'all_shifts': all_shifts,
        'cashiers': cashiers,
        'cash_sales': cash_sales,
        'card_sales': card_sales,
        'total_revenue': total_revenue,
        'sales_count': sales.filter(is_cancelled=False).count(),
        'now': timezone.now(),
    }
    return render(request, 'z_report.html', context)


@csrf_exempt
def close_shift_action(request):
    """
    Vardiyayı Kapatma ve Sayılan Nakit Girişi (Kasiyer Şifresi Doğrulamalı)
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8')) if request.body else {}
            actual_cash = Decimal(str(data.get('actual_cash', 0)))
            notes = data.get('notes', '').strip()
            shift_id = data.get('shift_id')
            password = data.get('password', '').strip()

            if not password:
                return JsonResponse({'success': False, 'message': 'Kasa kapanışını onaylamak için lütfen kasiyer şifrenizi giriniz.'}, status=400)

            register, _ = CashRegister.objects.get_or_create(
                register_code="KASA-01", 
                defaults={'name': 'Kasa 1 (Ana Kasa)', 'is_active': True}
            )

            if shift_id:
                shift = Shift.objects.filter(id=shift_id).first()
            else:
                shift = Shift.objects.filter(cash_register=register, is_closed=False).order_by('-opened_at').first()

            if not shift:
                # Kapanmamış yoksa en son vardiyayı al
                shift = Shift.objects.filter(cash_register=register).order_by('-opened_at').first()

            if not shift:
                return JsonResponse({'success': False, 'message': 'Kapatılacak vardiya bulunamadı.'}, status=400)

            # Kasiyer / Yetkili Şifresi Doğrulama
            is_authorized = False
            if shift.cashier and shift.cashier.check_password(password):
                is_authorized = True
            elif request.user.is_authenticated and request.user.check_password(password):
                is_authorized = True
            else:
                # Herhangi bir yetkili yönetici veya aktif kasiyer şifresi eşleşiyor mu?
                for u in User.objects.filter(is_active=True):
                    if u.check_password(password):
                        is_authorized = True
                        break

            if not is_authorized:
                return JsonResponse({'success': False, 'message': 'Hatalı şifre! Kasiyer şifreniz doğrulanamadı.'}, status=403)

            # Satış tutarlarını eksiksiz hesapla
            cash_sales = Sale.objects.filter(shift=shift, payment_type='NAKIT', is_cancelled=False).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
            card_sales = Sale.objects.filter(shift=shift, payment_type='KART', is_cancelled=False).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
            
            shift.total_cash_sales = cash_sales
            shift.total_card_sales = card_sales
            shift.total_sales_count = Sale.objects.filter(shift=shift, is_cancelled=False).count()
            shift.expected_cash = shift.opening_float + shift.total_cash_sales
            shift.actual_cash = actual_cash
            shift.difference = actual_cash - shift.expected_cash
            shift.closed_at = timezone.now()
            shift.is_closed = True
            if notes:
                shift.notes = notes
            shift.save()

            log_action('POS', 'Z Raporu / Vardiya Kapatıldı', f"Vardiya #{shift.id} Kapatıldı. Beklenen: {shift.expected_cash} TL, Sayılan: {shift.actual_cash} TL, Fark: {shift.difference} TL", user=request.user)

            # C# API Senkronizasyonu (Hata verse bile Django akışını bozmaz)
            try:
                CSharpApiClient.close_shift(shift.id, actual_cash, notes)
            except Exception as ce:
                print(f"[C# API Error] close_shift: {ce}")

            return JsonResponse({
                'success': True,
                'shift_id': shift.id,
                'difference': float(shift.difference),
                'expected_cash': float(shift.expected_cash),
                'actual_cash': float(shift.actual_cash),
                'message': f"Vardiya #{shift.id} başarıyla kapatıldı."
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)
    return JsonResponse({'success': False, 'message': 'Geçersiz metod.'}, status=400)


@csrf_exempt
def open_shift_action(request):
    """
    Yeni Kasa Vardiyası Başlatma (Kasiyer Şifresi Doğrulamalı)
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8')) if request.body else {}
            opening_float = Decimal(str(data.get('opening_float', '500.00') or '500.00'))
            notes = data.get('notes', '').strip()
            cashier_id = data.get('cashier_id')
            password = data.get('password', '').strip()

            if not password:
                return JsonResponse({'success': False, 'message': 'Yeni vardiya başlatmak için lütfen kasiyer şifrenizi giriniz.'}, status=400)

            # Kasiyeri Bul ve Şifresini Doğrula
            cashier = None
            if cashier_id:
                cashier = User.objects.filter(id=cashier_id, is_active=True).first()

            if not cashier and request.user.is_authenticated:
                cashier = request.user

            if not cashier:
                for u in User.objects.filter(is_active=True):
                    if u.check_password(password):
                        cashier = u
                        break

            if not cashier or not cashier.check_password(password):
                return JsonResponse({'success': False, 'message': 'Hatalı şifre! Kasiyer şifresi eşleşmedi.'}, status=403)

            register, _ = CashRegister.objects.get_or_create(
                register_code="KASA-01", 
                defaults={'name': 'Kasa 1 (Ana Kasa)', 'is_active': True}
            )

            # Zaten açık vardiya var mı?
            open_shift = Shift.objects.filter(cash_register=register, is_closed=False).first()
            if open_shift:
                return JsonResponse({
                    'success': True,
                    'shift_id': open_shift.id,
                    'already_open': True,
                    'message': f"Zaten açık bir vardiya var (#{open_shift.id})."
                })

            new_shift = Shift.objects.create(
                cash_register=register,
                cashier=cashier,
                opening_float=opening_float,
                expected_cash=opening_float,
                notes=notes
            )
            log_action('POS', 'Yeni Vardiya Açıldı', f"Vardiya #{new_shift.id} Başlatıldı ({cashier.username}). Devir: {opening_float} TL", user=cashier)

            return JsonResponse({
                'success': True,
                'shift_id': new_shift.id,
                'cashier_name': cashier.get_full_name() or cashier.username,
                'message': f"Vardiya #{new_shift.id} başarıyla açıldı."
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)
    return JsonResponse({'success': False, 'message': 'Geçersiz metod.'}, status=400)


# ==========================================
# KULLANICI OTURUMU (LOGIN & LOGOUT) VIEWS
# ==========================================

def login_view(request):
    """
    Hİ MARKET Özel Modern Giriş Sayfası (Kasiyer & Yönetici)
    """
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect('admin_dashboard')
        return redirect('pos_screen')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        next_url = request.POST.get('next') or request.GET.get('next')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                log_action('SİSTEM', 'Kullanıcı Girişi', f"Kullanıcı '{user.username}' sisteme giriş yaptı.", user=user)
                if next_url:
                    return redirect(next_url)
                if user.is_staff or user.is_superuser:
                    return redirect('admin_dashboard')
                return redirect('pos_screen')
            else:
                messages.error(request, 'Bu kullanıcı hesabı pasif durumdadır.')
        else:
            messages.error(request, 'Kullanıcı adı veya şifre hatalı! Lütfen bilgilerinizi kontrol ediniz.')

    return render(request, 'login.html')


def logout_view(request):
    """
    Hİ MARKET Güvenli Oturum Kapatma
    """
    if request.user.is_authenticated:
        log_action('SİSTEM', 'Kullanıcı Çıkışı', f"Kullanıcı '{request.user.username}' oturumu kapattı.", user=request.user)
        logout(request)
    messages.success(request, 'Oturumunuz başarıyla kapatıldı.')
    return redirect('login_view')


# ==========================================
# YÖNETİM PANALİ (ADMIN & MANAGEMENT) VIEWS
# ==========================================

def admin_dashboard_view(request):
    """
    Grafikli Dashboard & Yönetim Kontrol Paneli
    Tam Doğrulukta Mali Hesaplamalar, Zaman Dilimi Uyumlu Günlük ve Aylık Grafikler
    """
    if not request.user.is_authenticated:
        return redirect(f'/login/?next={request.path}')

    now = timezone.localtime(timezone.now())
    today = now.date()

    # 1. Günlük Satışlar (Bugün)
    today_start = timezone.make_aware(datetime.datetime.combine(today, datetime.time.min))
    today_end = timezone.make_aware(datetime.datetime.combine(today, datetime.time.max))

    today_sales = Sale.objects.filter(created_at__range=(today_start, today_end), is_cancelled=False)
    today_total = today_sales.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
    today_customer_count = today_sales.count()
    today_cash = today_sales.filter(payment_type='NAKIT').aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
    today_card = today_sales.filter(payment_type='KART').aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
    today_other = today_sales.filter(payment_type__in=['PARCALI', 'VERESIYE']).aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')

    # 2. Bu Ayki Satışlar
    month_start = timezone.make_aware(datetime.datetime.combine(today.replace(day=1), datetime.time.min))
    month_sales = Sale.objects.filter(created_at__gte=month_start, is_cancelled=False)
    month_total = month_sales.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
    month_customer_count = month_sales.count()
    month_cash = month_sales.filter(payment_type='NAKIT').aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
    month_card = month_sales.filter(payment_type='KART').aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
    month_other = month_sales.filter(payment_type__in=['PARCALI', 'VERESIYE']).aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')

    # 3. Genel Toplam Metrikler
    all_sales = Sale.objects.filter(is_cancelled=False)
    all_time_total = all_sales.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
    all_customer_count = all_sales.count()
    all_cash = all_sales.filter(payment_type='NAKIT').aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
    all_card = all_sales.filter(payment_type='KART').aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
    all_other = all_sales.filter(payment_type__in=['PARCALI', 'VERESIYE']).aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')

    # 4. Ürün & Stok Durumu
    total_products = Product.objects.filter(is_active=True).count()
    low_stock_products = Product.objects.filter(is_active=True, stock_quantity__lte=F('min_stock_level')).order_by('stock_quantity')
    low_stock_count = low_stock_products.count()
    out_of_stock_count = Product.objects.filter(is_active=True, stock_quantity__lte=0).count()
    total_supplier_balance = Supplier.objects.aggregate(Sum('balance'))['balance__sum'] or Decimal('0.00')

    # 5. Son 14 Günlük Satış Trendi (Günlük Satış & Müşteri Grafiği)
    days_tr = ['Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt', 'Paz']
    daily_labels = []
    daily_revenue = []
    daily_customers = []

    for i in range(13, -1, -1):
        d = today - datetime.timedelta(days=i)
        d_start = timezone.make_aware(datetime.datetime.combine(d, datetime.time.min))
        d_end = timezone.make_aware(datetime.datetime.combine(d, datetime.time.max))

        d_qs = Sale.objects.filter(created_at__range=(d_start, d_end), is_cancelled=False)
        d_rev = d_qs.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
        d_cnt = d_qs.count()

        daily_labels.append(f"{d.strftime('%d.%m')} ({days_tr[d.weekday()]})")
        daily_revenue.append(float(d_rev))
        daily_customers.append(d_cnt)

    # 6. Son 6 Aylık Ciro Grafiği
    months_tr = ['', 'Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
    monthly_labels = []
    monthly_revenue = []
    monthly_customers = []

    for offset in range(5, -1, -1):
        m = today.month - offset
        y = today.year
        while m <= 0:
            m += 12
            y -= 1
        last_day = calendar.monthrange(y, m)[1]
        m_start = timezone.make_aware(datetime.datetime(y, m, 1, 0, 0, 0))
        m_end = timezone.make_aware(datetime.datetime(y, m, last_day, 23, 59, 59, 999999))

        m_qs = Sale.objects.filter(created_at__range=(m_start, m_end), is_cancelled=False)
        m_rev = m_qs.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
        m_cnt = m_qs.count()

        monthly_labels.append(f"{months_tr[m]} {y}")
        monthly_revenue.append(float(m_rev))
        monthly_customers.append(m_cnt)

    # 7. Ödeme Türü Dağılımı (Bugün, Bu Ay ve Genel Kapsamlı Veri)
    payment_stats = {
        'today': {
            'cash': float(today_cash),
            'card': float(today_card),
            'other': float(today_other),
            'total': float(today_cash + today_card + today_other),
        },
        'month': {
            'cash': float(month_cash),
            'card': float(month_card),
            'other': float(month_other),
            'total': float(month_cash + month_card + month_other),
        },
        'all': {
            'cash': float(all_cash),
            'card': float(all_card),
            'other': float(all_other),
            'total': float(all_cash + all_card + all_other),
        }
    }

    payment_labels = ['Nakit Satış', 'Banka / Kredi Kartı', 'Parçalı / Cari']
    payment_data = [float(today_cash), float(today_card), float(today_other)]

    # 8. En Çok Satan 5 Ürün
    top_products = SaleItem.objects.values('product_name').annotate(
        total_qty=Sum('quantity'),
        total_revenue=Sum('total_price')
    ).order_by('-total_qty')[:5]

    # 9. Son Satış Fişleri
    recent_sales = Sale.objects.filter(is_cancelled=False).select_related('cashier').order_by('-created_at')[:5]

    # 10. Son Sistem Logları
    recent_logs = SystemLog.objects.select_related('user').order_by('-created_at')[:8]

    context = {
        # Mali Metrikler
        'today_total': today_total,
        'today_customer_count': today_customer_count,
        'today_cash': today_cash,
        'today_card': today_card,
        'today_other': today_other,
        'month_total': month_total,
        'month_customer_count': month_customer_count,
        'month_cash': month_cash,
        'month_card': month_card,
        'all_time_total': all_time_total,
        'all_customer_count': all_customer_count,
        'total_products': total_products,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'total_supplier_balance': total_supplier_balance,

        # Grafikler (JSON)
        'daily_labels_json': json.dumps(daily_labels),
        'daily_revenue_json': json.dumps(daily_revenue),
        'daily_customers_json': json.dumps(daily_customers),
        'monthly_labels_json': json.dumps(monthly_labels),
        'monthly_revenue_json': json.dumps(monthly_revenue),
        'monthly_customers_json': json.dumps(monthly_customers),
        'payment_labels_json': json.dumps(payment_labels),
        'payment_data_json': json.dumps(payment_data),
        'payment_stats_json': json.dumps(payment_stats),

        # Tablolar
        'top_products': top_products,
        'low_stock_products': low_stock_products[:5],
        'recent_sales': recent_sales,
        'recent_logs': recent_logs,
    }
    return render(request, 'admin/index.html', context)


def supplier_list_view(request):
    """
    Toptancı Carileri Listesi
    """
    search_query = request.GET.get('q', '').strip()
    suppliers = Supplier.objects.prefetch_related('transactions').all()

    if search_query:
        suppliers = suppliers.filter(
            Q(company_name__icontains=search_query) |
            Q(contact_name__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(tax_number__icontains=search_query)
        )

    total_debt = suppliers.filter(balance__gt=0).aggregate(Sum('balance'))['balance__sum'] or Decimal('0.00')
    total_credit = suppliers.filter(balance__lt=0).aggregate(Sum('balance'))['balance__sum'] or Decimal('0.00')

    context = {
        'suppliers': suppliers,
        'search_query': search_query,
        'total_debt': total_debt,
        'total_credit': abs(total_credit),
    }
    return render(request, 'admin/suppliers.html', context)


def supplier_create_view(request):
    """
    Yeni Toptancı Cari Kaydı
    """
    if request.method == 'POST':
        company_name = request.POST.get('company_name', '').strip()
        contact_name = request.POST.get('contact_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        tax_office = request.POST.get('tax_office', '').strip()
        tax_number = request.POST.get('tax_number', '').strip()
        address = request.POST.get('address', '').strip()
        initial_balance = Decimal(request.POST.get('initial_balance', '0.00') or '0.00')
        notes = request.POST.get('notes', '').strip()

        if company_name:
            supplier = Supplier.objects.create(
                company_name=company_name,
                contact_name=contact_name,
                phone=phone,
                email=email,
                tax_office=tax_office,
                tax_number=tax_number,
                address=address,
                balance=initial_balance,
                notes=notes,
                is_active=True
            )
            # Eğer açılış bakiyesi varsa ilk cari hareket kaydı oluştur
            if initial_balance != 0:
                trans_type = 'ALIS' if initial_balance > 0 else 'IADE'
                SupplierTransaction.objects.create(
                    supplier=supplier,
                    transaction_type=trans_type,
                    amount=abs(initial_balance),
                    balance_after=initial_balance,
                    document_no='ACILIS-BAKIYESI',
                    description='Açılış Cari Bakiyesi',
                    user=request.user if request.user.is_authenticated else None
                )

            log_action('SUPPLIER', 'Yeni Toptancı Eklendi', f"{supplier.company_name} (Açılış Bakiyesi: {initial_balance} TL)", user=request.user)
            messages.success(request, f"Toptancı '{company_name}' başarıyla eklendi.")
            return redirect('supplier_list_view')
        else:
            messages.error(request, "Lütfen toptancı firma adını giriniz.")

    return render(request, 'admin/supplier_form.html')


def supplier_payment_view(request, supplier_id):
    """
    Toptancıya Ödeme Yapma / Cari Bakiye Düzeltme
    """
    supplier = get_object_or_404(Supplier, id=supplier_id)
    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount', '0.00'))
        trans_type = request.POST.get('transaction_type', 'ODEME')
        document_no = request.POST.get('document_no', '').strip()
        description = request.POST.get('description', '').strip()

        if amount > 0:
            if trans_type == 'ODEME':
                supplier.balance -= amount
            elif trans_type == 'ALIS':
                supplier.balance += amount
            elif trans_type == 'IADE':
                supplier.balance -= amount
            supplier.save()

            SupplierTransaction.objects.create(
                supplier=supplier,
                transaction_type=trans_type,
                amount=amount,
                balance_after=supplier.balance,
                document_no=document_no,
                description=description,
                user=request.user if request.user.is_authenticated else None
            )

            log_action('SUPPLIER', 'Cari Ödeme/İşlem', f"{supplier.company_name} - {trans_type}: {amount} TL (Yeni Bakiye: {supplier.balance} TL)", user=request.user)
            messages.success(request, f"{supplier.company_name} cari işlem kaydedildi.")

    return redirect('supplier_list_view')


def stock_entry_list_view(request):
    """
    Stok Giriş ve İrsaliye Fişleri Listesi
    """
    search_q = request.GET.get('q', '').strip()
    entry_type = request.GET.get('type')
    supplier_id = request.GET.get('supplier')

    entries = StockEntry.objects.select_related('supplier', 'created_by').prefetch_related('items__product').order_by('-created_at')

    if search_q:
        entries = entries.filter(
            Q(entry_number__icontains=search_q) |
            Q(invoice_number__icontains=search_q) |
            Q(supplier__company_name__icontains=search_q) |
            Q(notes__icontains=search_q)
        )

    if entry_type in ['GIRIS', 'IADE']:
        entries = entries.filter(entry_type=entry_type)

    if supplier_id:
        entries = entries.filter(supplier_id=supplier_id)

    # İstatistikler
    all_entries = StockEntry.objects.all()
    total_entries_count = all_entries.count()
    total_in = all_entries.filter(entry_type='GIRIS').aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
    total_out = all_entries.filter(entry_type='IADE').aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
    total_veresiye = all_entries.filter(entry_type='GIRIS', payment_type='VERESIYE').aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')

    suppliers = Supplier.objects.filter(is_active=True).order_by('company_name')

    context = {
        'entries': entries,
        'suppliers': suppliers,
        'search_q': search_q,
        'selected_type': entry_type,
        'selected_supplier': supplier_id,
        'total_entries_count': total_entries_count,
        'total_in': total_in,
        'total_out': total_out,
        'total_veresiye': total_veresiye,
    }
    return render(request, 'admin/stock_entry_list.html', context)


def stock_entry_create_view(request):
    """
    Yeni Stok Girişi (Fatura / İrsaliye) ve Toptancı İadesi Ekranı
    """
    if request.method == 'POST':
        supplier_id = request.POST.get('supplier_id')
        invoice_number = request.POST.get('invoice_number', '').strip()
        payment_type = request.POST.get('payment_type', 'VERESIYE')
        notes = request.POST.get('notes', '').strip()
        entry_type = request.POST.get('entry_type', 'GIRIS')

        supplier = Supplier.objects.filter(id=supplier_id).first() if supplier_id else None

        prefix = "IADE" if entry_type == 'IADE' else "STK"
        entry_number = f"{prefix}-{timezone.now().strftime('%Y%m%d%H%M%S')}"

        entry = StockEntry.objects.create(
            entry_number=entry_number,
            entry_type=entry_type,
            supplier=supplier,
            invoice_number=invoice_number,
            payment_type=payment_type,
            notes=notes,
            created_by=request.user if request.user.is_authenticated else None
        )

        product_ids = request.POST.getlist('product_id[]')
        quantities = request.POST.getlist('quantity[]')
        units = request.POST.getlist('unit[]')
        list_prices = request.POST.getlist('list_price[]')
        discount_rates = request.POST.getlist('discount_rate[]')
        vat_rates = request.POST.getlist('vat_rate[]')
        buy_prices = request.POST.getlist('buy_price[]')

        total_entry_amount = Decimal('0.00')

        for i, p_id in enumerate(product_ids):
            if not p_id or i >= len(quantities) or not quantities[i]:
                continue
            try:
                product = Product.objects.get(id=p_id)
                qty = Decimal(quantities[i])
                unit = units[i] if (i < len(units) and units[i]) else product.unit
                list_p = Decimal(list_prices[i] or '0.00') if i < len(list_prices) else Decimal('0.00')
                disc_r = Decimal(discount_rates[i] or '0.00') if i < len(discount_rates) else Decimal('0.00')
                vat_r = Decimal(vat_rates[i] or '20.00') if i < len(vat_rates) else Decimal('20.00')

                # Alış Fiyatı (Maliyet) Formülü:
                # Birim Fiyat * (1 - İskonto/100) * (1 + KDV/100)
                if list_p > Decimal('0.00'):
                    disc_factor = Decimal('1.00') - (disc_r / Decimal('100.00'))
                    vat_factor = Decimal('1.00') + (vat_r / Decimal('100.00'))
                    calc_buy_price = round(list_p * disc_factor * vat_factor, 2)
                else:
                    calc_buy_price = Decimal(buy_prices[i] or '0.00') if i < len(buy_prices) else Decimal('0.00')

                total_line = round(qty * calc_buy_price, 2)

                StockEntryItem.objects.create(
                    stock_entry=entry,
                    product=product,
                    quantity=qty,
                    unit=unit,
                    list_price=list_p,
                    discount_rate=disc_r,
                    vat_rate=vat_r,
                    buy_price=calc_buy_price,
                    total_price=total_line
                )

                # Stok & Fiyat Güncelleme (Hiyerarşik Kalıtım)
                if entry_type == 'IADE':
                    # Toptancıya iade: Mal marketten çıktığı için stok DÜŞER!
                    product.stock_quantity -= qty
                    log_action('STOCK', 'Toptancıya İade Çıkışı', f"{product.name} -{qty} {unit} (İade Maliyeti: {calc_buy_price} TL)", user=request.user)
                else:
                    # Normal mal girişi: Stok ARTAR
                    product.stock_quantity += qty
                    if calc_buy_price > Decimal('0.00'):
                        product.buy_price = calc_buy_price
                    if vat_r > Decimal('0.00'):
                        product.vat_rate = vat_r
                    if unit:
                        product.unit = unit
                    # Kalıtım: Ürün ilk kez alınıyorsa veya toptancısı yoksa bu toptancıya bağlanır
                    if supplier and not product.supplier:
                        product.supplier = supplier
                    log_action('STOCK', 'Stok Girişi Yapıldı', f"{product.name} +{qty} {unit} (Alış Fiyatı: {calc_buy_price} TL, KDV: %{vat_r})", user=request.user)

                product.save()
                total_entry_amount += total_line

            except Product.DoesNotExist:
                continue

        entry.total_amount = total_entry_amount
        entry.save()

        # Toptancı cari bakiyesini güncelle
        if supplier and total_entry_amount > 0:
            if entry_type == 'IADE':
                # İade edilen mal tutarı kadar toptancıya olan borcumuz düşer
                supplier.balance -= total_entry_amount
                supplier.save()

                SupplierTransaction.objects.create(
                    supplier=supplier,
                    transaction_type='IADE',
                    amount=total_entry_amount,
                    balance_after=supplier.balance,
                    document_no=invoice_number or entry_number,
                    description=f"Toptancı Mal İadesi #{entry_number}",
                    user=request.user if request.user.is_authenticated else None
                )
                log_action('SUPPLIER', 'Toptancı Mal İadesi', f"{supplier.company_name} - {total_entry_amount} TL (Yeni Bakiye: {supplier.balance} TL)", user=request.user)
            elif payment_type == 'VERESIYE':
                # Veresiye mal alımı toptancı borcunu artırır
                supplier.balance += total_entry_amount
                supplier.save()

                SupplierTransaction.objects.create(
                    supplier=supplier,
                    transaction_type='ALIS',
                    amount=total_entry_amount,
                    balance_after=supplier.balance,
                    document_no=invoice_number or entry_number,
                    description=f"Stok Giriş Fişi #{entry_number}",
                    user=request.user if request.user.is_authenticated else None
                )
                log_action('SUPPLIER', 'Mal Alımı Borç Girişi', f"{supplier.company_name} + {total_entry_amount} TL (Yeni Bakiye: {supplier.balance} TL)", user=request.user)

        if entry_type == 'IADE':
            log_action('STOCK', 'Toptancı İade Fişi Kaydedildi', f"İade Fişi #{entry_number} - Toplam {total_entry_amount} TL", user=request.user)
            messages.success(request, f"Toptancı mal iade fişi #{entry_number} başarıyla kaydedildi ve stoklar düşüldü.")
        else:
            log_action('STOCK', 'Stok Fişi Kaydedildi', f"Fiş #{entry_number} - Toplam {total_entry_amount} TL", user=request.user)
            messages.success(request, f"Stok giriş fişi #{entry_number} başarıyla kaydedildi.")

        return redirect('stock_entry_list')

    suppliers = Supplier.objects.filter(is_active=True).order_by('company_name')
    products = Product.objects.filter(is_active=True).select_related('supplier', 'category').order_by('name')
    categories = Category.objects.filter(is_active=True).order_by('name')
    preselect_product_id = request.GET.get('product_id')

    preselected_product = None
    preselected_supplier_id = None
    preselected_list_price = Decimal('0.00')

    if preselect_product_id:
        try:
            preselected_product = Product.objects.filter(id=preselect_product_id, is_active=True).select_related('supplier', 'category').first()
            if preselected_product:
                if preselected_product.supplier_id:
                    preselected_supplier_id = preselected_product.supplier_id
                else:
                    # Kayıtlı toptancısı yoksa geçmişteki en son mal kabul hareketine bak
                    last_item = StockEntryItem.objects.filter(
                        product=preselected_product,
                        stock_entry__supplier__isnull=False
                    ).select_related('stock_entry__supplier').order_by('-stock_entry__created_at').first()
                    if last_item and last_item.stock_entry.supplier_id:
                        preselected_supplier_id = last_item.stock_entry.supplier_id

                # Liste fiyatını hesapla (Alış fiyatı KDV dahil maliyet olduğundan: liste = alış / (1 + KDV/100))
                if preselected_product.buy_price and preselected_product.buy_price > Decimal('0.00'):
                    vat_div = Decimal('1.00') + (preselected_product.vat_rate / Decimal('100.00'))
                    preselected_list_price = round(preselected_product.buy_price / vat_div, 2)
                else:
                    preselected_list_price = Decimal('0.00')
        except Exception as e:
            print(f"Preselect product error: {e}")

    context = {
        'suppliers': suppliers,
        'products': products,
        'categories': categories,
        'preselect_product_id': preselect_product_id,
        'preselected_product': preselected_product,
        'preselected_supplier_id': preselected_supplier_id,
        'preselected_list_price': preselected_list_price,
        'unit_choices': Product.UNIT_CHOICES,
    }
    return render(request, 'admin/stock_entry_create.html', context)


def stock_barcode_search_api(request):
    """
    Mal Kabul / Stok Girişi Esnasında El Terminali veya Barkod Okuyucu İle Hızlı Ürün Bulma
    """
    barcode = request.GET.get('barcode', '').strip()
    supplier_id = request.GET.get('supplier_id')

    if not barcode:
        return JsonResponse({'success': False, 'message': 'Barkod girilmedi.'}, status=400)

    product = Product.objects.filter(is_active=True).filter(
        Q(barcode=barcode) | Q(secondary_barcode=barcode)
    ).first()

    if not product:
        return JsonResponse({'success': False, 'message': f"'{barcode}' barkodlu ürün bulunamadı. Hızlı Ürün Tanımla ile ekleyebilirsiniz."}, status=404)

    is_supplier_product = False
    if supplier_id:
        try:
            s_id = int(supplier_id)
            if product.supplier_id == s_id:
                is_supplier_product = True
        except (ValueError, TypeError):
            pass

    return JsonResponse({
        'success': True,
        'product': {
            'id': product.id,
            'name': product.name,
            'barcode': product.barcode,
            'secondary_barcode': product.secondary_barcode or '',
            'category_id': product.category_id,
            'category_name': product.category.name if product.category else '',
            'supplier_id': product.supplier_id,
            'supplier_name': product.supplier.company_name if product.supplier else '',
            'buy_price': float(product.buy_price),
            'sell_price': float(product.sell_price),
            'vat_rate': float(product.vat_rate),
            'unit': product.unit,
            'stock_quantity': float(product.stock_quantity),
            'is_weighted': product.is_weighted,
            'is_supplier_product': is_supplier_product
        }
    })


@csrf_exempt
def quick_create_product_api(request):
    """
    Fatura / Stok Girişi veya POS Esnasında Hızlı Ürün Tanımlama API Uç Noktası
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Yalnızca POST istekleri kabul edilir.'}, status=405)
    
    try:
        data = json.loads(request.body.decode('utf-8'))
        barcode = data.get('barcode', '').strip()
        secondary_barcode = data.get('secondary_barcode', '').strip() or None
        name = data.get('name', '').strip()
        category_id = data.get('category_id')
        supplier_id = data.get('supplier_id')
        list_price = Decimal(str(data.get('list_price', '0.00') or '0.00'))
        discount_rate = Decimal(str(data.get('discount_rate', '0.00') or '0.00'))
        vat_rate = Decimal(str(data.get('vat_rate', '20.00') or '20.00'))
        buy_price = Decimal(str(data.get('buy_price', '0.00') or '0.00'))
        sell_price = Decimal(str(data.get('sell_price', '0.00') or '0.00'))
        unit = data.get('unit', 'Adet')
        is_weighted = bool(data.get('is_weighted', False))

        # Eğer liste fiyatı girildiyse alış fiyatını otomatik formülle hesapla
        if list_price > Decimal('0.00'):
            disc_factor = Decimal('1.00') - (discount_rate / Decimal('100.00'))
            vat_factor = Decimal('1.00') + (vat_rate / Decimal('100.00'))
            buy_price = round(list_price * disc_factor * vat_factor, 2)

        if not barcode or not name:
            return JsonResponse({'success': False, 'message': 'Barkod ve Ürün Adı zorunludur.'}, status=400)

        if Product.objects.filter(barcode=barcode).exists():
            return JsonResponse({'success': False, 'message': f"Bu barkoda ({barcode}) sahip başka bir ürün zaten kayıtlı!"}, status=400)

        category = Category.objects.filter(id=category_id).first() if category_id else None
        supplier = Supplier.objects.filter(id=supplier_id).first() if supplier_id else None

        product = Product.objects.create(
            barcode=barcode,
            secondary_barcode=secondary_barcode,
            name=name,
            category=category,
            supplier=supplier,
            buy_price=buy_price,
            sell_price=sell_price,
            vat_rate=vat_rate,
            unit=unit,
            stock_quantity=Decimal('0.000'),
            is_weighted=is_weighted,
            is_active=True
        )

        current_user = request.user if (hasattr(request, 'user') and request.user.is_authenticated) else None
        log_action('PRODUCT', 'Hızlı Ürün Tanımlandı', f"{product.name} ({product.barcode}) fatura girişinden eklendi. (Tedarikçi: {supplier.company_name if supplier else 'Yok'})", user=current_user)

        return JsonResponse({
            'success': True,
            'product': {
                'id': product.id,
                'name': product.name,
                'barcode': product.barcode,
                'secondary_barcode': product.secondary_barcode or '',
                'list_price': float(list_price),
                'discount_rate': float(discount_rate),
                'buy_price': float(product.buy_price),
                'sell_price': float(product.sell_price),
                'vat_rate': float(product.vat_rate),
                'unit': product.unit,
                'is_weighted': product.is_weighted,
                'stock_quantity': float(product.stock_quantity),
                'supplier_id': product.supplier_id,
                'supplier_name': product.supplier.company_name if product.supplier else ''
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


def product_catalog_view(request):
    """
    Ürün Yönetim Kataloğu ve Envanter Fiyat Listesi
    """
    search_q = request.GET.get('q', '').strip()
    category_id = request.GET.get('category')
    supplier_id = request.GET.get('supplier')
    stock_status = request.GET.get('stock')

    products = Product.objects.select_related('category', 'supplier').all()

    if search_q:
        products = products.filter(
            Q(name__icontains=search_q) |
            Q(barcode__icontains=search_q) |
            Q(secondary_barcode__icontains=search_q)
        )

    if category_id:
        products = products.filter(category_id=category_id)

    if supplier_id:
        products = products.filter(supplier_id=supplier_id)

    if stock_status == 'low':
        products = products.filter(stock_quantity__lte=F('min_stock_level'), stock_quantity__gt=0)
    elif stock_status == 'out':
        products = products.filter(stock_quantity__lte=0)
    elif stock_status == 'quick':
        products = products.filter(is_quick_button=True)
    elif stock_status == 'weighted':
        products = products.filter(is_weighted=True)

    # İstatistikler (Tüm aktif ürünler üzerinden)
    all_products = Product.objects.all()
    total_products_count = all_products.count()
    low_stock_count = all_products.filter(stock_quantity__lte=F('min_stock_level'), stock_quantity__gt=0).count()
    out_of_stock_count = all_products.filter(stock_quantity__lte=0).count()
    quick_button_count = all_products.filter(is_quick_button=True).count()
    
    # Stok Değeri Hesabı
    total_stock_cost = Decimal('0.00')
    total_stock_value = Decimal('0.00')
    for p in all_products:
        if p.stock_quantity > 0:
            total_stock_cost += p.stock_quantity * p.buy_price
            total_stock_value += p.stock_quantity * p.sell_price

    categories = Category.objects.filter(is_active=True).order_by('name')
    suppliers = Supplier.objects.filter(is_active=True).order_by('company_name')

    context = {
        'products': products,
        'categories': categories,
        'suppliers': suppliers,
        'search_q': search_q,
        'category_id': category_id,
        'supplier_id': supplier_id,
        'stock_status': stock_status,
        'total_products_count': total_products_count,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'quick_button_count': quick_button_count,
        'total_stock_cost': total_stock_cost,
        'total_stock_value': total_stock_value,
    }
    return render(request, 'admin/product_catalog.html', context)


def product_create_edit_view(request, product_id=None):
    """
    Ürün Tanımlama / Düzenleme Sayfası (Master Data)
    """
    product = get_object_or_404(Product, id=product_id) if product_id else None

    if request.method == 'POST':
        barcode = request.POST.get('barcode', '').strip()
        secondary_barcode = request.POST.get('secondary_barcode', '').strip()
        name = request.POST.get('name', '').strip()
        category_id = request.POST.get('category_id')
        supplier_id = request.POST.get('supplier_id')
        buy_price = Decimal(request.POST.get('buy_price', '0.00') or '0.00')
        sell_price = Decimal(request.POST.get('sell_price', '0.00') or '0.00')
        vat_rate = Decimal(request.POST.get('vat_rate', '20.00') or '20.00')
        unit = request.POST.get('unit', 'Adet')
        stock_quantity = Decimal(request.POST.get('stock_quantity', '0.000') or '0.000')
        min_stock_level = Decimal(request.POST.get('min_stock_level', '5.000') or '5.000')
        is_weighted = request.POST.get('is_weighted') == 'on'
        is_quick_button = request.POST.get('is_quick_button') == 'on'
        quick_button_order = int(request.POST.get('quick_button_order', 0) or 0)
        is_active = request.POST.get('is_active') == 'on'

        category = Category.objects.filter(id=category_id).first() if category_id else None
        supplier = Supplier.objects.filter(id=supplier_id).first() if supplier_id else None

        if product:
            product.barcode = barcode
            product.secondary_barcode = secondary_barcode
            product.name = name
            product.category = category
            product.supplier = supplier
            product.buy_price = buy_price
            product.sell_price = sell_price
            product.vat_rate = vat_rate
            product.unit = unit
            product.stock_quantity = stock_quantity
            product.min_stock_level = min_stock_level
            product.is_weighted = is_weighted
            product.is_quick_button = is_quick_button
            product.quick_button_order = quick_button_order
            product.is_active = is_active

            if 'image' in request.FILES:
                product.image = request.FILES['image']

            product.save()
            log_action('PRODUCT', 'Ürün Güncellendi', f"{product.name} ({product.barcode}) güncellendi.", user=request.user)
            messages.success(request, f"Ürün '{name}' başarıyla güncellendi.")
        else:
            product = Product.objects.create(
                barcode=barcode,
                secondary_barcode=secondary_barcode,
                name=name,
                category=category,
                supplier=supplier,
                buy_price=buy_price,
                sell_price=sell_price,
                vat_rate=vat_rate,
                unit=unit,
                stock_quantity=stock_quantity,
                min_stock_level=min_stock_level,
                is_weighted=is_weighted,
                is_quick_button=is_quick_button,
                quick_button_order=quick_button_order,
                is_active=is_active,
                image=request.FILES.get('image')
            )
            log_action('PRODUCT', 'Yeni Ürün Eklendi', f"{product.name} ({product.barcode}) eklendi.", user=request.user)
            messages.success(request, f"Yeni ürün '{name}' başarıyla eklendi.")

        return redirect('product_catalog_view')

    categories = Category.objects.filter(is_active=True).order_by('name')
    suppliers = Supplier.objects.filter(is_active=True).order_by('company_name')

    context = {
        'product': product,
        'categories': categories,
        'suppliers': suppliers,
        'unit_choices': Product.UNIT_CHOICES,
    }
    return render(request, 'admin/product_form.html', context)


def system_logs_view(request):
    """
    Sistem İşlem ve Denetim Logları Ekranı
    """
    module = request.GET.get('module')
    level = request.GET.get('level')
    query = request.GET.get('q', '').strip()

    logs = SystemLog.objects.select_related('user').all()

    if module:
        logs = logs.filter(module=module)
    if level:
        logs = logs.filter(level=level)
    if query:
        logs = logs.filter(Q(action__icontains=query) | Q(message__icontains=query))

    logs = logs[:100]

    context = {
        'logs': logs,
        'selected_module': module,
        'selected_level': level,
        'query': query,
        'modules': SystemLog.MODULES,
        'levels': SystemLog.LOG_LEVELS,
    }
    return render(request, 'admin/system_logs.html', context)

