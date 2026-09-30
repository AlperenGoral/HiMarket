from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from pos_app.models import Category, Product, CashRegister
from decimal import Decimal

class Command(BaseCommand):
    help = 'Varsayılan market verilerini (kategoriler, barkodlu ürünler, kasa ve admin) yükler.'

    def handle(self, *args, **options):
        self.stdout.write("Market verileri yükleniyor...")

        # 1. Admin Kullanıcısı
        admin_user, created = User.objects.get_or_create(username='admin', defaults={'email': 'admin@himarket.com', 'is_staff': True, 'is_superuser': True})
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Yönetici (admin / admin123) oluşturuldu."))

        # 2. Kasiyer Kullanıcısı
        cashier_user, created = User.objects.get_or_create(username='kasiyer', defaults={'first_name': 'Ahmet', 'last_name': 'Yılmaz'})
        if created:
            cashier_user.set_password('1234')
            cashier_user.save()
            self.stdout.write(self.style.SUCCESS("Kasiyer (kasiyer / 1234) oluşturuldu."))

        # 3. Kasa Tanımı
        register, _ = CashRegister.objects.get_or_create(register_code="KASA-01", defaults={'name': 'Kasa 1 (Ana Kasa)', 'is_active': True})

        # 4. Kategoriler
        cat_bakery, _ = Category.objects.get_or_create(name="Fırın & Unlu Mamüller", defaults={'display_order': 1})
        cat_food, _ = Category.objects.get_or_create(name="Temel Gıda", defaults={'display_order': 2})
        cat_drink, _ = Category.objects.get_or_create(name="İçecekler", defaults={'display_order': 3})
        cat_dairy, _ = Category.objects.get_or_create(name="Şarküteri & Süt", defaults={'display_order': 4})
        cat_produce, _ = Category.objects.get_or_create(name="Manav & Sebze/Meyve", defaults={'display_order': 5})

        # 5. Örnek Barkodlu Ürünler
        products_data = [
            {
                'barcode': '8690000000010',
                'name': 'Ekmek 200g',
                'category': cat_bakery,
                'buy_price': Decimal('8.00'),
                'sell_price': Decimal('10.00'),
                'vat_rate': Decimal('1.00'),
                'is_weighted': False,
                'unit': 'Adet',
                'stock_quantity': Decimal('350.000'),
                'is_quick_button': True,
                'quick_button_order': 1
            },
            {
                'barcode': '8690000000027',
                'name': 'Büyük Boy Poşet',
                'category': cat_food,
                'buy_price': Decimal('0.10'),
                'sell_price': Decimal('0.50'),
                'vat_rate': Decimal('20.00'),
                'is_weighted': False,
                'unit': 'Adet',
                'stock_quantity': Decimal('10000.000'),
                'is_quick_button': True,
                'quick_button_order': 2
            },
            {
                'barcode': '8690504018003',
                'name': 'Su 0.5L Pet',
                'category': cat_drink,
                'buy_price': Decimal('3.50'),
                'sell_price': Decimal('6.00'),
                'vat_rate': Decimal('10.00'),
                'is_weighted': False,
                'unit': 'Adet',
                'stock_quantity': Decimal('240.000'),
                'is_quick_button': True,
                'quick_button_order': 3
            },
            {
                'barcode': '8690504000123',
                'name': 'Tam Yağlı Süt 1L',
                'category': cat_dairy,
                'buy_price': Decimal('26.00'),
                'sell_price': Decimal('34.50'),
                'vat_rate': Decimal('1.00'),
                'is_weighted': False,
                'unit': 'Adet',
                'stock_quantity': Decimal('65.000'),
                'is_quick_button': False
            },
            {
                'barcode': '2700001014502', # Terazi Barkodu Örneği: 27 + 00001 ÜrünKodu + 01450 Gramaj (1.450 KG)
                'name': 'Amasya Elması',
                'category': cat_produce,
                'buy_price': Decimal('22.00'),
                'sell_price': Decimal('35.00'),
                'vat_rate': Decimal('1.00'),
                'is_weighted': True,
                'unit': 'KG',
                'stock_quantity': Decimal('120.500'),
                'is_quick_button': True,
                'quick_button_order': 4
            },
            {
                'barcode': '2700002005008', # Terazi Barkodu: 27 + 00002 ÜrünKodu + 00500 Gramaj (0.500 KG = 500g)
                'name': 'Taze Kaşar Peyniri',
                'category': cat_dairy,
                'buy_price': Decimal('170.00'),
                'sell_price': Decimal('240.00'),
                'vat_rate': Decimal('1.00'),
                'is_weighted': True,
                'unit': 'KG',
                'stock_quantity': Decimal('45.000'),
                'is_quick_button': True,
                'quick_button_order': 5
            }
        ]

        for p_data in products_data:
            Product.objects.get_or_create(barcode=p_data['barcode'], defaults=p_data)

        self.stdout.write(self.style.SUCCESS("Tüm örnek market ürünleri başarıyla yüklendi!"))
