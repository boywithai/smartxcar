# SmartXCar Web Kontrol Uygulaması

Production domain bilgisi güvenlik nedeniyle repository içinde paylaşılmaz.

SmartXCar, araç kontrolü için geliştirilmiş web tabanlı gerçek zamanlı yönetim panelidir. Uygulamanın ana kapsamı; yönetici giriş ekranı, araç kontrol dashboard'u, Socket.IO tabanlı canlı iletişim, komut doğrulama, telemetri gösterimi ve Docker/Dokploy production deploy sürecidir.

Web uygulaması Flask ile geliştirilmiştir. Dashboard üzerinden verilen hareket ve aksesuar komutları backend tarafından doğrulanır, aktif araç bağlantısına Socket.IO event'leriyle iletilir ve araçtan gelen durum/sensör verileri anlık olarak web arayüzünde gösterilir.

## Özellikler

- Yönetici parolası ile korunan web kontrol paneli
- Araç istemcisi için token tabanlı doğrulama
- Socket.IO ile gerçek zamanlı çift yönlü iletişim
- İleri, geri, sol, sağ ve acil dur komutları
- Korna, far, selektör ve silecek kontrolleri
- Mesafe ve yağış sensörü verilerinin canlı gösterimi
- Araç online/offline durum takibi
- Bağlantı kopması, logout veya yeni cihaz bağlantısında güvenli durum komutları
- Docker ve Gunicorn ile production deploy

## Web Application Kapsamı

Bu repository'nin ana sorumluluğu web application katmanıdır:

- Admin login ekranı
- Session tabanlı dashboard erişimi
- Araç kontrol dashboard'u
- Socket.IO bağlantı yönetimi
- Dashboard ile backend arasında canlı event akışı
- Backend ile aktif araç istemcisi arasında komut relay işlemi
- Mesafe ve yağış telemetrisinin web arayüzüne aktarılması
- Online/offline araç durumunun gösterilmesi
- Frontend tarafında basılı tutma, bırakınca durdurma ve güvenli kontrol davranışları
- Production ortamı için Dockerfile ve Gunicorn yapılandırması
- Dokploy üzerinde canlı yayınlama akışı

## Teknoloji Stack

- Python 3.12
- Flask
- Flask-SocketIO
- python-socketio
- python-dotenv
- Gunicorn
- simple-websocket
- HTML, CSS ve vanilla JavaScript
- Docker
- Dokploy
- Araç istemcisi entegrasyonu

## Dosya Yapısı

```text
smartxcar/
  app.py
  mock_pi_client.py
  Dockerfile
  requirements.txt
  .env.example
  .dockerignore
  .gitignore
  README.md
  templates/
    login.html
    index.html
  static/
    style.css
    control.js
```

`mock_pi_client.py` yalnızca geliştirme ve bağlantı testi için tutulur. Canlı sistemde araç kontrolü gerçek araç istemcisi üzerinden yapılır.

## Web Arayüzü

Web arayüzü Flask template yapısıyla oluşturulmuştur. `templates/login.html` yönetici giriş ekranını, `templates/index.html` ise ana kontrol panelini içerir.

Dashboard ekranında bulunan temel bileşenler:

- Araç bağlantı durumu
- Panel socket bağlantı durumu
- Mesafe sensörü kartı
- Yağış durumu kartı
- Hareket kontrol alanı
- Acil dur butonu
- Korna, far, selektör ve silecek kontrolleri
- Son işlem / komut sonucu alanı

Frontend tarafında `static/control.js` dosyası Socket.IO bağlantısını ve kullanıcı etkileşimlerini yönetir. Yön butonlarında basılı tutma modeli kullanılır. Kullanıcı butona bastığında ilgili hareket komutu gönderilir; buton bırakıldığında, pencere odağı kaybolduğunda veya sayfa gizlendiğinde `stop` komutu gönderilir.

CSS tarafı `static/style.css` içinde tutulur. Arayüz responsive olacak şekilde düzenlenmiştir ve mobil ekranlarda kontrol alanları tek kolonlu yapıya geçer.

## Backend Web Mantığı

`app.py`, web uygulamasının ana giriş noktasıdır. Hem HTTP route'larını hem de Socket.IO event handler'larını içerir.

HTTP route'ları:

- `/login`: Yönetici giriş ekranı
- `/`: Oturum açmış kullanıcı için dashboard
- `/logout`: Oturumu kapatma ve güvenli duruma alma

Socket.IO event'leri:

- `connect`: Dashboard veya araç istemcisi bağlantı doğrulaması
- `disconnect`: Bağlantı kopma durumunda state güncelleme
- `drive_command`: Dashboard'dan gelen hareket komutlarını doğrulama ve iletme
- `accessory_command`: Dashboard'dan gelen aksesuar komutlarını doğrulama ve iletme
- `telemetry_update`: Araçtan gelen sensör verisini dashboard'a yayınlama
- `command_result`: Araçtan gelen komut sonucunu dashboard'a yayınlama

Backend tarafında komutlar whitelist mantığıyla doğrulanır. Geçersiz payload'lar aktif araca iletilmez.

Geçerli hareket komutları:

```text
forward
backward
left
right
stop
```

Geçerli aksesuar komutları:

```text
horn: on/off
headlights: on/off
flash: trigger
wiper: 0/1/2/3
```

## Web Güvenliği

Uygulamada web katmanı için temel güvenlik önlemleri uygulanmıştır:

- Admin paneli parola ile korunur.
- Oturum yönetimi Flask session ile yapılır.
- `SECRET_KEY` environment variable üzerinden alınır.
- Hassas bilgiler `.env` dosyasında tutulur ve repository'ye gönderilmez.
- Production ortamında secure cookie ayarı aktif edilir.
- Dashboard Socket.IO bağlantısı session kontrolünden geçer.
- Yetkisiz socket bağlantıları reddedilir.
- Dashboard'dan gelen komut payload'ları doğrulanır.

## Ortam Değişkenleri

Sunucu aşağıdaki environment variable değerleriyle çalışır:

```env
APP_ENV=production
SECRET_KEY=<güçlü secret>
ADMIN_PASSWORD=<güçlü panel parolası>
DEVICE_TOKEN=<güçlü cihaz tokenı>
CAR_ID=car-01
```

`SECRET_KEY`, `ADMIN_PASSWORD` ve `DEVICE_TOKEN` zorunludur. Bu değerler boş bırakılırsa uygulama başlamaz.

Araç istemcisi canlı sunucuya bağlanırken aşağıdaki değerleri kullanır:

```env
SERVER_URL=<production server url>
DEVICE_TOKEN=<production device token>
CAR_ID=<production car id>
```

`DEVICE_TOKEN` ve `CAR_ID`, sunucu tarafındaki değerlerle aynı olmalıdır. Aksi durumda araç bağlantısı reddedilir.

## Local Geliştirme

1. `python -m venv venv`
2. `venv\Scripts\activate`
3. `pip install -r requirements.txt`
4. `.env.example` dosyasını `.env` olarak kopyalayıp doldurun.
5. Terminal 1: `python app.py`
6. Geliştirme testi için araç istemcisini veya geçici test istemcisini çalıştırın.
7. Tarayıcı: `http://localhost:5000`

Local geliştirme için örnek `.env`:

```env
APP_ENV=development
SECRET_KEY=
ADMIN_PASSWORD=
DEVICE_TOKEN=
CAR_ID=car-01
SERVER_URL=http://localhost:5000
```

Local geliştirmede bile gerçek production secret, panel parolası veya cihaz tokenı kullanılmamalıdır.

## Production Çalışma Şekli

Dockerfile uygulamayı production ortamında Gunicorn ile çalıştırır:

```powershell
gunicorn -w 1 --threads 100 --bind 0.0.0.0:5000 app:app
```

Tek worker kullanımı bilinçli bir tercihtir. Bu sürümde aktif araç bağlantısı ve dashboard socket listesi process memory içinde tutulur. Birden fazla worker açılırsa bağlantı durumu worker'lar arasında paylaşılmaz.

## Dokploy Deploy

Canlı uygulama Dokploy üzerinde Dockerfile tabanlı olarak deploy edilir.

Deploy akışı:

1. Repository Dokploy'a bağlanır.
2. Dokploy, proje kökündeki `Dockerfile` ile image build eder.
3. Container `0.0.0.0:5000` üzerinden Gunicorn ile başlatılır.
4. Dokploy reverse proxy/domain ayarı ile uygulama production domaini üzerinden yayınlanır.
5. Production environment variable değerleri Dokploy panelinden girilir.
6. `.env` dosyası repository'ye gönderilmez.

Dokploy tarafında dikkat edilmesi gerekenler:

- Container iç portu `5000` olmalıdır.
- WebSocket/Socket.IO bağlantıları reverse proxy tarafından desteklenmelidir.
- `APP_ENV=production` kullanılmalıdır.
- `SECRET_KEY`, `ADMIN_PASSWORD` ve `DEVICE_TOKEN` güçlü değerler olmalıdır.
- Uygulama tek worker ile çalıştırılmalıdır.

## Araç Entegrasyonu

Araç tarafı bu web uygulamasına Socket.IO client olarak bağlanır. Canlı sistemde istemci Raspberry Pi üzerinde çalışır; ancak bu repository'nin ana odağı araç donanım kodu değil, web uygulaması ve realtime kontrol sunucusudur.

Bağlantı sırasında aşağıdaki auth bilgileri gönderilir:

```json
{
  "role": "raspi",
  "car_id": "car-01",
  "device_token": "<production device token>"
}
```

Sunucu bu bilgileri doğruladıktan sonra istemciyi aktif araç bağlantısı olarak kabul eder. Dashboard'dan gelen komutlar yalnızca doğrulanmış aktif araç bağlantısına iletilir.

Sunucudan araç istemcisine giden event'ler:

- `drive_command`
- `accessory_command`

Araç istemcisinden sunucuya gelen event'ler:

- `telemetry_update`
- `command_result`

## Güvenli Durum Davranışı

Sunucu aşağıdaki durumlarda araca güvenli komutlar gönderir:

- Dashboard logout olduğunda
- Dashboard socket bağlantısı koptuğunda
- Yeni araç istemcisi bağlantısı eski bağlantının yerini aldığında

Gönderilen güvenli komutlar:

```text
drive_command: stop
accessory_command: horn off
accessory_command: wiper 0
```

## Notlar

- Canlı sistem araç istemcisiyle entegre çalışmaktadır.
- `mock_pi_client.py` production akışının parçası değildir; sadece geliştirme/test amaçlı yardımcı istemcidir.
- Server motor hızını veya fiziksel GPIO/PWM detaylarını belirlemez; doğrulanmış dashboard komutlarını araç istemcisine iletir.
- Fiziksel hareket davranışı araç tarafındaki kontrol kodunda uygulanır.
