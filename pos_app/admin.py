from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Category, Product, CashRegister, Shift, Sale, SaleItem, Supplier, SupplierTransaction, StockEntry, StockEntryItem, SystemLog

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_order', 'status_badge', 'created_at')
    list_editable = ('display_order',)
    search_fields = ('name',)

    def status_badge(self, obj):
        if obj.is_active:
            return mark_safe('<span class="badge bg-success text-white px-2 py-1"><i class="bi bi-check-circle me-1"></i>Aktif</span>')
        return mark_safe('<span class="badge bg-secondary text-white px-2 py-1">Pasif</span>')
    status_badge.short_description = "Durum"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'barcode', 'category', 'supplier', 'sell_price', 'stock_status', 'unit', 'is_quick_button', 'is_active')
    list_filter = ('category', 'supplier', 'is_weighted', 'is_quick_button', 'is_active')
    search_fields = ('name', 'barcode', 'secondary_barcode')
    list_editable = ('sell_price', 'is_quick_button', 'is_active')

    def stock_status(self, obj):
        if obj.is_low_stock:
            return format_html('<span style="color:red; font-weight:bold;">⚠️ {} {} (Kritik)</span>', obj.stock_quantity, obj.unit)
        return format_html('<span style="color:green; font-weight:bold;">{} {}</span>', obj.stock_quantity, obj.unit)
    stock_status.short_description = "Stok Durumu"


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'contact_name', 'phone', 'balance_status', 'is_active')
    search_fields = ('company_name', 'contact_name', 'phone', 'tax_number')
    
    def balance_status(self, obj):
        if obj.balance > 0:
            return format_html('<span style="color:red; font-weight:bold;">Borcumuz: {} TL</span>', obj.balance)
        elif obj.balance < 0:
            return format_html('<span style="color:green; font-weight:bold;">Alacak: {} TL</span>', abs(obj.balance))
        return mark_safe('<span style="color:#64748b; font-weight:600;">0.00 TL</span>')
    balance_status.short_description = "Cari Bakiye"


@admin.register(SupplierTransaction)
class SupplierTransactionAdmin(admin.ModelAdmin):
    list_display = ('supplier', 'transaction_type', 'amount', 'balance_after', 'document_no', 'created_at')
    list_filter = ('transaction_type', 'supplier')
    search_fields = ('supplier__company_name', 'document_no')


class StockEntryItemInline(admin.TabularInline):
    model = StockEntryItem
    extra = 0


@admin.register(StockEntry)
class StockEntryAdmin(admin.ModelAdmin):
    list_display = ('entry_number', 'entry_type', 'supplier', 'invoice_number', 'payment_type', 'total_amount', 'entry_date')
    list_filter = ('entry_type', 'payment_type', 'supplier')
    search_fields = ('entry_number', 'invoice_number')
    inlines = [StockEntryItemInline]


@admin.register(SystemLog)
class SystemLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'level', 'module', 'action', 'message', 'user', 'ip_address')
    list_filter = ('level', 'module', 'created_at')
    search_fields = ('action', 'message', 'user__username')
    readonly_fields = ('created_at',)


@admin.register(CashRegister)
class CashRegisterAdmin(admin.ModelAdmin):
    list_display = ('name', 'register_code', 'is_active', 'created_at')


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    readonly_fields = ('product_name', 'barcode', 'quantity', 'unit_price', 'vat_rate', 'vat_amount', 'total_price')


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('receipt_number', 'operation_type_badge', 'created_at', 'formatted_total', 'payment_badge', 'cashier', 'status_badge')
    list_filter = ('is_return', 'payment_type', 'is_cancelled', 'created_at')
    search_fields = ('receipt_number',)
    inlines = [SaleItemInline]
    readonly_fields = ('created_at',)

    def operation_type_badge(self, obj):
        if obj.is_return:
            return mark_safe('<span class="badge bg-danger text-white px-2 py-1"><i class="bi bi-arrow-return-left me-1"></i>İADE FİŞİ</span>')
        return mark_safe('<span class="badge bg-success text-white px-2 py-1"><i class="bi bi-cart-check me-1"></i>SATIŞ</span>')
    operation_type_badge.short_description = "İşlem Türü"

    def formatted_total(self, obj):
        return format_html('<span class="fw-bold text-slate-900 fs-7">₺{}</span>', f"{obj.total_amount:.2f}")
    formatted_total.short_description = "Toplam Tutar"

    def payment_badge(self, obj):
        if obj.payment_type == 'NAKIT':
            return mark_safe('<span class="badge bg-success-subtle text-success border border-success-subtle px-2 py-1"><i class="bi bi-cash me-1"></i>Nakit</span>')
        elif obj.payment_type == 'KART':
            return mark_safe('<span class="badge bg-primary-subtle text-primary border border-primary-subtle px-2 py-1"><i class="bi bi-credit-card me-1"></i>Kart</span>')
        elif obj.payment_type == 'PARCALI':
            return mark_safe('<span class="badge bg-info-subtle text-info border border-info-subtle px-2 py-1"><i class="bi bi-pie-chart me-1"></i>Parçalı</span>')
        elif obj.payment_type == 'VERESIYE':
            return mark_safe('<span class="badge bg-warning-subtle text-warning-emphasis border border-warning-subtle px-2 py-1"><i class="bi bi-person-lines-fill me-1"></i>Veresiye</span>')
        return obj.payment_type
    payment_badge.short_description = "Ödeme Tipi"

    def status_badge(self, obj):
        if obj.is_cancelled:
            return mark_safe('<span class="badge bg-danger text-white px-2.5 py-1 fw-bold"><i class="bi bi-x-circle-fill me-1"></i>İptal Edildi</span>')
        return mark_safe('<span class="badge bg-success-subtle text-success border border-success px-2.5 py-1 fw-bold"><i class="bi bi-check-circle-fill me-1"></i>Başarılı</span>')
    status_badge.short_description = "Fiş Durumu"


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ('cash_register', 'cashier', 'opened_at', 'closed_at', 'formatted_open_float', 'formatted_sales', 'difference_status', 'shift_status')
    list_filter = ('is_closed', 'cash_register')

    def formatted_open_float(self, obj):
        return format_html('<span class="fw-semibold text-slate-700">₺{}</span>', f"{obj.opening_float:.2f}")
    formatted_open_float.short_description = "Açılış Devri"

    def formatted_sales(self, obj):
        cash_str = f"{obj.total_cash_sales:.2f}"
        card_str = f"{obj.total_card_sales:.2f}"
        return format_html('<span class="fs-8 text-slate-600">Nakit: <b>₺{}</b><br>Kart: <b>₺{}</b></span>', cash_str, card_str)
    formatted_sales.short_description = "Satışlar"

    def difference_status(self, obj):
        if not obj.is_closed:
            return mark_safe('<span class="badge bg-warning text-dark px-2 py-1"><i class="bi bi-hourglass-split me-1"></i>Devam Ediyor</span>')
        if obj.difference < 0:
            return format_html('<span class="badge bg-danger text-white px-2 py-1"><i class="bi bi-arrow-down-circle me-1"></i>Açık: {} TL</span>', f"{abs(obj.difference):.2f}")
        elif obj.difference > 0:
            return format_html('<span class="badge bg-primary text-white px-2 py-1"><i class="bi bi-arrow-up-circle me-1"></i>Fazla: +{} TL</span>', f"{obj.difference:.2f}")
        return mark_safe('<span class="badge bg-success text-white px-2 py-1"><i class="bi bi-check-circle me-1"></i>Fark Yok (0.00 TL)</span>')
    difference_status.short_description = "Kasa Farkı"

    def shift_status(self, obj):
        if not obj.is_closed:
            return mark_safe('<span class="badge bg-primary text-white px-2 py-1"><i class="bi bi-play-circle-fill me-1"></i>Açık Vardiya</span>')
        return mark_safe('<span class="badge bg-secondary text-white px-2 py-1"><i class="bi bi-lock-fill me-1"></i>Kapatıldı</span>')
    shift_status.short_description = "Vardiya Durumu"


