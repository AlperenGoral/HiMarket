from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Kategori Adı")
    description = models.TextField(blank=True, null=True, verbose_name="Açıklama")
    display_order = models.PositiveIntegerField(default=0, verbose_name="Sıralama")
    is_active = models.BooleanField(default=True, verbose_name="Aktif mi?")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Kategori"
        verbose_name_plural = "Kategoriler"
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name


class Product(models.Model):
    UNIT_CHOICES = [
        ('Adet', 'Adet'),
        ('KG', 'Kilogram (KG)'),
        ('Gram', 'Gram'),
        ('Litre', 'Litre'),
        ('Paket', 'Paket'),
    ]

    barcode = models.CharField(max_length=50, unique=True, db_index=True, verbose_name="Barkod (EAN-13 vb.)")
    secondary_barcode = models.CharField(max_length=50, blank=True, null=True, verbose_name="İkincil / Koli Barkodu")
    name = models.CharField(max_length=200, verbose_name="Ürün Adı")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name="products", verbose_name="Kategori")
    
    buy_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Alış Fiyatı (TL)")
    sell_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Satış Fiyatı (TL)")
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('20.00'), verbose_name="KDV Oranı (%)")
    
    is_weighted = models.BooleanField(default=False, verbose_name="Tartılı / Terazi Ürünü mü?")
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='Adet', verbose_name="Satış Birimi")
    
    stock_quantity = models.DecimalField(max_digits=10, decimal_places=3, default=Decimal('0.000'), verbose_name="Mevcut Stok Miktarı")
    min_stock_level = models.DecimalField(max_digits=10, decimal_places=3, default=Decimal('5.000'), verbose_name="Kritik Stok Uyarısı Seviyesi")
    
    is_quick_button = models.BooleanField(default=False, verbose_name="Hızlı Buton mu? (Barkodsuz Satış)")
    quick_button_order = models.PositiveIntegerField(default=0, verbose_name="Hızlı Buton Sırası")
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name="Ürün Görseli")
    
    supplier = models.ForeignKey('Supplier', on_delete=models.SET_NULL, null=True, blank=True, related_name="products", verbose_name="Varsayılan Toptancı")
    is_active = models.BooleanField(default=True, verbose_name="Satışta mı?")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Ürün"
        verbose_name_plural = "Ürünler"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.barcode})"

    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.min_stock_level

    @property
    def profit_amount(self):
        """Birim Net Kâr Tutarı (TL) = Satış Fiyatı - Alış Fiyatı"""
        return self.sell_price - self.buy_price

    @property
    def profit_percent(self):
        """Kâr Marjı Yüzdesi (%) = ((Satış - Alış) / Alış) * 100"""
        if self.buy_price and self.buy_price > Decimal('0.00'):
            return ((self.sell_price - self.buy_price) / self.buy_price) * Decimal('100.00')
        return Decimal('0.00')

    @property
    def vat_exclusive_price(self):
        """KDV Dahil Satış Fiyatından İç KDV Hariç Matrah"""
        if self.vat_rate and self.vat_rate > Decimal('0.00'):
            return self.sell_price / (Decimal('1.00') + (self.vat_rate / Decimal('100.00')))
        return self.sell_price

    @property
    def vat_amount_in_sell(self):
        """Satış Fiyatı İçerisindeki KDV Tutarı"""
        return self.sell_price - self.vat_exclusive_price


class CashRegister(models.Model):
    name = models.CharField(max_length=100, default="Kasa 1", verbose_name="Kasa Adı")
    register_code = models.CharField(max_length=20, unique=True, default="KASA-01", verbose_name="Kasa Kodu")
    is_active = models.BooleanField(default=True, verbose_name="Aktif mi?")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Kasa Terminali"
        verbose_name_plural = "Kasa Terminalleri"

    def __str__(self):
        return f"{self.name} [{self.register_code}]"


class Shift(models.Model):
    cash_register = models.ForeignKey(CashRegister, on_delete=models.CASCADE, related_name="shifts", verbose_name="Kasa")
    cashier = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="shifts", verbose_name="Kasiyer")
    
    opened_at = models.DateTimeField(auto_now_add=True, verbose_name="Açılış Zamanı")
    closed_at = models.DateTimeField(blank=True, null=True, verbose_name="Kapanış Zamanı")
    
    opening_float = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Açılış Devir Parası (TL)")
    total_cash_sales = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Toplam Nakit Satış")
    total_card_sales = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Toplam Kart Satışı")
    total_sales_count = models.PositiveIntegerField(default=0, verbose_name="Toplam Fiş Sayısı")
    
    expected_cash = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Beklenen Nakit")
    actual_cash = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Sayılan Nakit")
    difference = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Kasa Farkı (Açık/Fazla)")
    
    is_closed = models.BooleanField(default=False, verbose_name="Kasa Kapandı mı? (Z Raporu)")
    notes = models.TextField(blank=True, null=True, verbose_name="Vardiya Notları")

    class Meta:
        verbose_name = "Kasa Vardiyası / Z Raporu"
        verbose_name_plural = "Kasa Vardiyaları / Z Raporları"
        ordering = ['-opened_at']

    def __str__(self):
        status = "KAPALI" if self.is_closed else "AÇIK"
        return f"{self.cash_register.name} - {self.opened_at.strftime('%d.%m.%Y %H:%M')} [{status}]"


class Sale(models.Model):
    PAYMENT_CHOICES = [
        ('NAKIT', 'Nakit'),
        ('KART', 'Banka / Kredi Kartı'),
        ('PARCALI', 'Parçalı Ödeme'),
        ('VERESIYE', 'Veresiye / Cari'),
    ]

    receipt_number = models.CharField(max_length=50, unique=True, db_index=True, verbose_name="Fiş Numarası")
    shift = models.ForeignKey(Shift, on_delete=models.SET_NULL, null=True, blank=True, related_name="sales", verbose_name="Vardiya")
    cashier = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="sales", verbose_name="Kasiyer")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Satış Tarihi")
    
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Ara Toplam (TL)")
    total_vat = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Toplam KDV (TL)")
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="İskonto (TL)")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Genel Toplam (TL)")
    
    payment_type = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='NAKIT', verbose_name="Ödeme Tipi")
    cash_paid = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Alınan Nakit (TL)")
    change_given = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Para Üstü (TL)")
    
    is_cancelled = models.BooleanField(default=False, verbose_name="Fiş İptal Edildi mi?")
    cancellation_reason = models.TextField(blank=True, null=True, verbose_name="İptal Gerekçesi")
    is_return = models.BooleanField(default=False, verbose_name="İade Fişi mi?")
    return_reason = models.TextField(blank=True, null=True, verbose_name="İade Gerekçesi")

    class Meta:
        verbose_name = "Satış Fişi"
        verbose_name_plural = "Satış Fişleri"
        ordering = ['-created_at']

    def __str__(self):
        return f"Fiş #{self.receipt_number} - {self.total_amount} TL"


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="items", verbose_name="Fiş")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, related_name="sale_items", verbose_name="Ürün")
    product_name = models.CharField(max_length=200, verbose_name="Ürün Adı")
    barcode = models.CharField(max_length=50, verbose_name="Barkod")
    
    quantity = models.DecimalField(max_digits=10, decimal_places=3, default=Decimal('1.000'), verbose_name="Miktar / Gramaj")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Birim Fiyat")
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('10.00'), verbose_name="KDV Oranı (%)")
    vat_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="KDV Tutarı")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Satır Toplamı")

    class Meta:
        verbose_name = "Fiş Kalemi"
        verbose_name_plural = "Fiş Kalemleri"

    def __str__(self):
        return f"{self.product_name} x {self.quantity} = {self.total_price} TL"


class Supplier(models.Model):
    company_name = models.CharField(max_length=200, verbose_name="Toptancı / Firma Adı")
    contact_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Yetkili Kişi")
    phone = models.CharField(max_length=30, blank=True, null=True, verbose_name="Telefon")
    email = models.EmailField(blank=True, null=True, verbose_name="E-Posta")
    tax_office = models.CharField(max_length=100, blank=True, null=True, verbose_name="Vergi Dairesi")
    tax_number = models.CharField(max_length=50, blank=True, null=True, verbose_name="Vergi Numarası")
    address = models.TextField(blank=True, null=True, verbose_name="Adres")
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="Cari Bakiye (TL) [+ Borç / - Alacak]")
    notes = models.TextField(blank=True, null=True, verbose_name="Notlar")
    is_active = models.BooleanField(default=True, verbose_name="Aktif mi?")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Toptancı Carisi"
        verbose_name_plural = "Toptancı Carileri"
        ordering = ['company_name']

    def __str__(self):
        return self.company_name


class SupplierTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('ALIS', 'Mal Alımı (Borç Eklendi)'),
        ('ODEME', 'Toptancıya Ödeme Yapıldı'),
        ('IADE', 'Mal İadesi (Alacak Eklendi)'),
        ('DUZELTME', 'Cari Bakiye Düzeltme'),
    ]
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="transactions", verbose_name="Toptancı")
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES, verbose_name="İşlem Tipi")
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Tutar (TL)")
    balance_after = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="İşlem Sonrası Bakiye")
    document_no = models.CharField(max_length=50, blank=True, null=True, verbose_name="Fatura / İrsaliye No")
    description = models.TextField(blank=True, null=True, verbose_name="Açıklama")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="İşlem Tarihi")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="İşlemi Yapan")

    class Meta:
        verbose_name = "Cari Hesap Hareketi"
        verbose_name_plural = "Cari Hesap Hareketleri"
        ordering = ['-created_at']


class StockEntry(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('NAKIT', 'Nakit Ödendi'),
        ('HAVALE', 'Banka / Havale Ödendi'),
        ('KART', 'Kredi Kartı Ödendi'),
        ('VERESIYE', 'Cari Hesaba İşlendi (Veresiye)'),
    ]

    ENTRY_TYPE_CHOICES = [
        ('GIRIS', 'Mal Alımı (Stok Girişi)'),
        ('IADE', 'Toptancıya İade (Stok Çıkışı)'),
    ]

    entry_number = models.CharField(max_length=50, unique=True, verbose_name="Stok Fiş No")
    entry_type = models.CharField(max_length=20, choices=ENTRY_TYPE_CHOICES, default='GIRIS', verbose_name="İşlem Türü")
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, related_name="stock_entries", verbose_name="Toptancı")
    invoice_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="Fatura / İrsaliye No")
    entry_date = models.DateTimeField(default=timezone.now, verbose_name="Fatura / Giriş Tarihi")
    payment_type = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='VERESIYE', verbose_name="Ödeme Yöntemi")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="Toplam Fatura Tutarı (TL)")
    notes = models.TextField(blank=True, null=True, verbose_name="Notlar / Açıklama")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Kaydeden")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Stok Giriş Fişi"
        verbose_name_plural = "Stok Giriş Fişleri"
        ordering = ['-created_at']

    def __str__(self):
        supplier_name = self.supplier.company_name if self.supplier else "Genel Stok Girişi"
        return f"Giriş #{self.entry_number} - {supplier_name} ({self.total_amount} TL)"


class StockEntryItem(models.Model):
    stock_entry = models.ForeignKey(StockEntry, on_delete=models.CASCADE, related_name="items", verbose_name="Stok Giriş Fişi")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="stock_entry_items", verbose_name="Ürün")
    quantity = models.DecimalField(max_digits=10, decimal_places=3, verbose_name="Miktar")
    unit = models.CharField(max_length=20, choices=Product.UNIT_CHOICES, default='Adet', verbose_name="Birim")
    list_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Birim Fiyat / Liste Fiyatı (TL)")
    discount_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), verbose_name="İskonto Oranı (%)")
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('20.00'), verbose_name="KDV Oranı (%)")
    buy_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Hesaplanan Alış Maliyeti (TL)")
    total_price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Satır Toplamı (TL)")

    class Meta:
        verbose_name = "Stok Giriş Kalemi"
        verbose_name_plural = "Stok Giriş Kalemleri"


class SystemLog(models.Model):
    LOG_LEVELS = [
        ('INFO', 'Bilgi'),
        ('WARNING', 'Uyarı'),
        ('ERROR', 'Hata'),
        ('SECURITY', 'Güvenlik / Denetim'),
    ]

    MODULES = [
        ('POS', 'Kasa Satış'),
        ('STOCK', 'Stok Yönetimi'),
        ('SUPPLIER', 'Toptancı Carileri'),
        ('PRODUCT', 'Ürün Yönetimi'),
        ('AUTH', 'Kullanıcı / Oturum'),
        ('SYSTEM', 'Sistem'),
    ]

    level = models.CharField(max_length=10, choices=LOG_LEVELS, default='INFO', verbose_name="Seviye")
    module = models.CharField(max_length=20, choices=MODULES, default='SYSTEM', verbose_name="Modül")
    action = models.CharField(max_length=100, verbose_name="Eylem / İşlem Adı")
    message = models.TextField(verbose_name="Log Detayı / Mesaj")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Kullanıcı")
    ip_address = models.GenericIPAddressField(blank=True, null=True, verbose_name="IP Adresi")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Tarih / Zaman")

    class Meta:
        verbose_name = "Sistem İşlem Logu"
        verbose_name_plural = "Sistem İşlem Logları"
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.created_at.strftime('%Y-%m-%d %H:%M')}] [{self.module}] {self.action}: {self.message[:50]}"


def log_action(module, action, message, level='INFO', user=None, ip_address=None):
    """
    Sistem çapında işlem loglama yardımcısı
    """
    try:
        SystemLog.objects.create(
            module=module,
            action=action,
            message=message,
            level=level,
            user=user if (user and user.is_authenticated) else None,
            ip_address=ip_address
        )
    except Exception as e:
        print(f"Log kaydetme hatası: {e}")

