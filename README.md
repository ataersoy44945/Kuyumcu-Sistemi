# Kuyumcu Pro — Premium Mücevher & Altın Yönetim Sistemi

Katmanlı mimari, OOP prensipleri ve PyQt6 kullanılarak geliştirilmiş masaüstü kuyumcu yönetim uygulaması. Premium koyu lacivert/siyah + altın temalı, canlı altın & döviz takipli, müşteri ve admin için ayrı paneller içerir.

## Klasör Yapısı

```
kuyumcu_sistemi/
├── main.py                      # Genel giriş — Login → Admin/Müşteri yönlendirme
├── config.py                    # Yollar, sabitler, karat katsayıları, API ayarları
├── data/app.db                  # SQLite veritabanı (otomatik oluşur)
│
├── backend/                     # İş mantığı ve veri katmanı
│   ├── app_context.py               # Bağımlılık konteyneri (DI)
│   ├── api/exchange_rate_api.py     # ExchangeRate API + Binance BTC
│   ├── database/database_manager.py # Şema, migration, singleton bağlantı
│   ├── models/                      # Veri sınıfları (User, Product, Order, SavedCard, …)
│   ├── repositories/                # CRUD katmanı (her tablo için ayrı)
│   ├── services/                    # AuthService, CartService, OrderService,
│   │                                #   PriceCalculator, ExchangeRateService,
│   │                                #   SavedCardService, FavoriteService, …
│   └── utils/                       # logger, validators
│
├── frontend/                    # Sunum katmanı (PyQt6 ekranları + tema)
│   ├── windows/                     # LoginWindow / AdminWindow / UserWindow
│   ├── pages/
│   │   ├── admin/                   # dashboard, products, categories,
│   │   │                            #   orders, users, rates
│   │   └── user/                    # home, catalog, categories, favorites,
│   │                                #   cart, checkout, orders, campaigns, profile
│   ├── components/                  # ProductCard, Toast, CartBar
│   ├── dialogs/                     # confirm, product, user_form/detail,
│   │                                #   password_reset, saved_cards,
│   │                                #   order_success
│   ├── styles/app_theme.py          # Renk paleti, font, QSS bileşenleri
│   └── utils.py                     # Kategori ikonları vb.
│
├── scripts/                     # demo seed scriptleri
│   ├── seed_products.py
│   └── seed_campaigns.py
└── assets/images/products/      # Ürün görselleri
```

## Çalıştırma

Gerekli kütüphaneleri kurun:

```bash
pip install -r requirements.txt
```

Uygulamayı başlatın:

```bash
python main.py
```

İlk açılışta `DatabaseManager` şemayı oluşturur, migration'ları uygular ve varsayılan admin hesabını otomatik üretir. Ürün/kategori/kampanya seed'i için:

```bash
python scripts/seed_products.py
python scripts/seed_campaigns.py
```

## Giriş (main.py)

Açılan login ekranında kullanıcı adı + şifre girilir; rol otomatik tespit edilir:

- **Admin girişi** → AdminWindow (operasyon merkezi)
- **Müşteri girişi** → UserWindow (alışveriş paneli)

```
admin                                              şifre: 1234
ataersoy1234 / beyto / dencadiktas / cemkaya       şifre: 1234
musteri                                            şifre: 1234
```

> **Uyarı:** Tüm şifreler deneme amacıyla `1234`'e ayarlandı. Üretime geçişten önce admin panelden **Şifre** butonu ile mutlaka değiştirilmeli.

## Mimari Notu

Proje üç katmanlı yapıyı sıkı uygular:

- **Repositories** → SQLite ile tek temas noktası (raw SQL)
- **Services** → İş kuralları, validasyon, fiyat hesabı, sipariş üretimi
- **UI** → Pages/Dialogs hiçbir zaman doğrudan DB'ye dokunmaz; her şey `AppContext` üzerinden servislere gider

`AppContext` bağımlılık konteyneridir; tüm servis ve repo'lar burada bir kez kurulur ve UI'ye geçirilir. Mock'lamak veya bağımlılık değiştirmek için tek nokta.

## Özellikler

### Müşteri Paneli
- **Ana Sayfa:** Canlı kur kartları (USD, EUR, Gram Altın, BTC) — 60 sn'de bir otomatik yenilenir
- **Ürünler:** Responsive grid (ekran genişliğine göre 1–6 sütun), kategori/ayar/arama filtreleri
- **Kategoriler:** İkonik kategori kartları + alt kategori filtreleri
- **Favoriler:** Kalp ikonuyla ekleme/çıkarma, favori listesi
- **Sepet:** Sticky **CartBar** (tüm sayfaların altında, sepete bir ürün eklenince çıkar), adet artır/azalt, satır silme, anlık toplam
- **Sipariş Özeti:** Ara toplam + kargo/sigorta + genel toplam (50.000 TL altı = 750 TL sigortalı kargo, üzeri ücretsiz)
- **Ödeme (4 yöntem):** Kredi/Banka Kartı (16 hane + AA/YY + CVV validasyonlu), Havale/EFT (IBAN gösterimi), Kapıda Ödeme, Mağazadan Teslim (şube seçimi)
- **Kayıtlı Kartlar:** "Bu kartı kaydet" checkbox; kart sahibi + BIN + son 4 hane + son kullanma + marka (Visa/Mastercard/Amex/Troy otomatik tespit) saklanır. Tam PAN ve CVV asla kaydedilmez. Yönetim dialog'undan silme/varsayılan yapma
- **Sipariş Tamamlama:** `KJ-YYYY-NNNNN` formatında benzersiz numara, başarı modalı, "Siparişlerime Git"
- **Siparişlerim:** Hazırlanıyor / Ödeme Bekleniyor / Onaylandı / Teslim Edildi / İptal durumları, ödeme yöntemine göre dinamik etiket
- **Kampanyalar:** Kategoriye yönlendiren kampanya kartları
- **Profil:** Bilgi görüntüleme, şifre değiştirme, sipariş geçmişi tablosu

### Admin Paneli
- **Dashboard:** Sipariş durumu sayıları, gelir özeti, hızlı erişim kartları
- **Ürün Yönetimi:** CRUD + görsel yükleme, kategori, ayar, gram, işçilik, kar marjı, stok, sabit fiyat / hesaplı fiyat seçimi
- **Kategori Yönetimi:** İkonlu kategori CRUD
- **Sipariş Yönetimi:** Tüm siparişler, durum güncelleme, müşteri/admin notları
- **Kullanıcı Yönetimi:** CRUD, rol değiştirme, hesap engelleme/aktif etme, **Şifre Sıfırla** (admin yeni şifre belirler, panoya kopyalanır)
- **Kur Yönetimi:** Manuel kur girişi + API'den otomatik yenileme

### Tema & Bileşenler
- **Premium koyu palet:** `#080D18` zemin → `#0D1628` yüzey → `#111C30` yükseltilmiş, altın aksanları (`#D4AF37`, `#F0C93A`)
- **Hover glow efektleri:** Ürün kartlarında üst altın çizgi belirir
- **Toast bildirimleri:** Alt-merkez fade-in/out (success/info/error variant'ları)
- **CartBar:** Üst altın çizgi + yumuşak yukarı gölge, sepet boşalınca otomatik gizlenir
- **OrderSuccessDialog:** Yeşil tik + sipariş bilgileri kartı

### Backend
- **Şifre güvenliği:** PBKDF2-HMAC-SHA256 + 32 byte rastgele salt + 100.000 iterasyon, sabit zamanlı doğrulama
- **Fiyat hesabı:** `gram × gram_altın_fiyatı × karat_katsayısı + işçilik + kar_marjı`. Sabit fiyatlı ürünler için `base_price` doğrudan döner
- **Auto-migrate:** Şema değişiklikleri idempotent (`PRAGMA table_info` ile kolon kontrolü), eski DB'ler veri kaybetmeden yükselir
- **Canlı kur:** Worker thread (`QThread`) UI'yi dondurmadan ExchangeRate API ve Binance BTC'yi çeker
- **Karat katsayıları:** 8/14/18/21/22/24 ayar (`config.KARAT_COEFFICIENTS`)
- **Foreign keys:** Tüm ilişkiler ON DELETE CASCADE/RESTRICT/SET NULL ile koruma altında

## Test Hesapları

| Kullanıcı Adı | Rol | Ad Soyad |
|---|---|---|
| `admin` | admin | Sistem Admin |
| `ataersoy1234` | customer | ata ersoy |
| `beyto` | customer | beyto Özen |
| `dencadiktas` | customer | Dença Diktaş |
| `cemkaya` | customer | Cem Kaya |
| `musteri` | customer | Test Müşteri |

Tümünün şifresi: `1234`

## Üretime Geçiş Kontrol Listesi

- [ ] Tüm test şifreleri admin panelden değiştirilmeli (özellikle `admin`)
- [ ] `checkout_page.py` içindeki `_DEMO_IBAN` ve `_DEMO_BANK` gerçek banka bilgileriyle değiştirilmeli
- [ ] `_STORES` listesi gerçek mağaza şubeleriyle güncellenmeli
- [ ] Kart bilgisi: PCI-DSS uyumu için iyzico/Stripe gibi tokenize eden ödeme sağlayıcısı entegre edilmeli — mevcut yapı yalnızca BIN+last4 saklıyor (deneme için yeterli, üretim için SAQ-A formu gerekir)
- [ ] `config.LOG_LEVEL` üretimde `WARNING`'e çekilmeli
