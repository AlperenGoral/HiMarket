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

Projeyi çalıştırmak için ana dizindeki `BASLAT.bat` dosyasını çalıştırmanız yeterlidir:

1. `BASLAT.bat` dosyasına çift tıklayın.
2. C# Backend API (Port 5000) ve Django Sunucusu (Port 8000) otomatik olarak başlatılacaktır.
3. Tarayıcınızda `http://127.0.0.1:8000/login/` adresi açılacaktır.

---

## 🔒 Lisans
Tüm hakları saklıdır.
