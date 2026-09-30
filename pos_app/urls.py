from django.urls import path
from . import views

urlpatterns = [
    # Kullanıcı Oturum Açma & Kapatma
    path('login/', views.login_view, name='login_view'),
    path('logout/', views.logout_view, name='logout_view'),

    # Kasa Satış Ana Ekranı
    path('', views.pos_screen, name='pos_screen'),

    # Barkod & Terazi API Uç Noktası
    path('api/barcode/', views.search_barcode, name='search_barcode'),

    # Satış İşleme API Uç Noktası
    path('api/sale/process/', views.process_sale, name='process_sale'),

    # Termal Fiş Görüntüleme & Yazdırma
    path('receipt/<str:receipt_number>/', views.receipt_view, name='receipt_view'),

    # Z Raporu Ekranı
    path('z-report/', views.z_report_view, name='z_report_view'),
    path('api/shift/close/', views.close_shift_action, name='close_shift_action'),
    path('api/shift/open/', views.open_shift_action, name='open_shift_action'),

    # Yönetim Kontrol Paneli & Dashboard
    path('management/dashboard/', views.admin_dashboard_view, name='admin_dashboard_view'),

    # Toptancı Carileri
    path('management/suppliers/', views.supplier_list_view, name='supplier_list_view'),
    path('management/suppliers/create/', views.supplier_create_view, name='supplier_create_view'),
    path('management/suppliers/<int:supplier_id>/payment/', views.supplier_payment_view, name='supplier_payment_view'),

    # Stok Giriş & İrsaliye
    path('management/stock-entry/', views.stock_entry_list_view, name='stock_entry_list'),
    path('management/stock-entry/create/', views.stock_entry_create_view, name='stock_entry_create'),

    # Ürün Kataloğu & Ürün Yönetimi
    path('management/products/', views.product_catalog_view, name='product_catalog_view'),
    path('management/products/create/', views.product_create_edit_view, name='product_create_view'),
    path('management/products/<int:product_id>/edit/', views.product_create_edit_view, name='product_edit_view'),

    # Sistem İşlem Logları
    path('management/logs/', views.system_logs_view, name='system_logs_view'),

    # Hızlı Ürün Tanımlama & Mal Kabul Barkod API
    path('api/product/quick-create/', views.quick_create_product_api, name='quick_create_product_api'),
    path('api/stock/barcode-search/', views.stock_barcode_search_api, name='stock_barcode_search_api'),
]
