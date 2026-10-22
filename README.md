# Hİ MARKET - Kasa (POS) & Stok Yönetim Sistemi

Hİ MARKET, perakende satış noktaları (süpermarket, manav, şarküteri vb.) için geliştirilmiş; hızlı, modern ve yüksek performanslı hibrit mimariye sahip bir Kasa Satış (POS) ve Stok Yönetim Otomasyonudur.

---

## 🚀 Mimari ve Teknoloji Yığını

* **Python 3 / Django 5**: Kasa POS ekranı, yönetim paneli, dinamik şablonlar, kullanıcı/vardiya yönetimi ve web arayüzleri.
* **C# .NET 8 Web API & EF Core**: Çoklu kiracılı (Multi-tenant) veri işleme, Swagger dokümantasyonu ve arka plan servisleri.
* **SQLite Veritabanı**: Harici sunucu kurulumu gerektirmeyen, hafif, taşınabilir ve hızlı veritabanı.
* **Bootstrap 5.3 & Vanilla JavaScript**: Dokunmatik POS ekranlarına, tabletlere ve mobil cihazlara tam uyumlu arayüz.

---

## ✨ Temel Özellikler

1. **Canlı Kasa Satış Terminali (POS):**
   - Sıfır gecikmeli yerel barkod arama (< 2 ms).
   - Barkodsuz ve hızlı ürünler için dokunmatik seçim ızgarası.
   - Tartılı / Terazili ürün barkodu desteği (27 ile başlayan EAN-13 ağırlık ayrıştırma).
   - Nakit, Kredi Kartı, Parçalı ve Veresiye tahsilat seçenekleri.
   - Termal fiş ve bilgi fişi yazdırma.

2. **Dört Katmanlı Piramit Stok Mimarisi:**
   - **Tedarikçi Carileri:** Toptancı bakiyeleri, borç/alacak takibi, cari ekstreler.
   - **Mal Kabul & İrsaliye:** Liste fiyatı, iskonto ve KDV formülüyle net alış maliyeti hesaplama.
   - **Ürün Kataloğu:** Otomatik tedarikçi bağı, ikincil koli barkodu, KDV dahil raf fiyatı ve kâr marjı analizi.
   - **Kasa:** Satış ve iadelerin anlık stok ve cariye yansıması.

3. **Vardiya ve Z Raporu Denetimi:**
   - Kasa devri, nakit/kart dağılımı ve gün sonu kasa farkı hesaplama.
   - Detaylı sistem işlem logları.

---

## 💻 Çalıştırma Talimatı

### Yöntem 1: Tek Tıkla Başlatma (Tavsiye Edilen)
Projeyi GitHub'tan indirdikten sonra çalıştırmak için:

1. Bilgisayarınızda **Python 3.10 veya üzeri** yüklü olduğundan emin olun (Kurulum yaparken **"Add Python to PATH"** kutucuğunu mutlaka işaretleyiniz).
2. Ana dizindeki **`BASLAT.bat`** dosyasına çift tıklayın.
   - Script ilk çalıştırmada gerekli Python paketlerini (`requirements.txt`) otomatik olarak yükler ve veritabanı tablolarını hazırlar.
   - C# Backend API'sini (Port 5000) ve Django Sunucusunu (Port 8000) otomatik başlatır.
3. Tarayıcınızda otomatik olarak açılacak adres:
   - **Bilgisayar:** `http://127.0.0.1:8000/login/`
   - **Aynı Wi-Fi'daki Telefon/Tablet:** Ekranda yazan yerel IP adresi (Örn: `http://192.168.1.xxx:8000/login/`)

### Yöntem 2: Visual Studio 2022 ile Geliştirme (C# Backend)
1. Visual Studio 2022 ile ana dizindeki **`HiMarket.sln`** dosyasını açın.
2. `HiMarket.API` projesinin başlangıç projesi (Startup Project) olduğunu doğrulayın ve **F5** (veya `Ctrl+F5`) tuşuna basarak başlatın.
3. C# Swagger API paneli `http://localhost:5000/swagger` adresinde açılacaktır.

---

## 🔑 Varsayılan Giriş Bilgileri

* **Kasa Girişi (Kasiyer):**
  * Kasa: `KASA-01`
  * Hızlı PIN Kodu: `1234`
* **Yönetici Paneli (Admin):**
  * Adres: `http://127.0.0.1:8000/login/` veya `http://127.0.0.1:8000/admin/`
  * Kullanıcı Adı: `admin`
  * Şifre: `admin123`

---

## 🔒 Lisans
Tüm hakları saklıdır.
