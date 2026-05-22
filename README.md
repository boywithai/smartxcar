# SmartXCar Local Kontrol Sunucusu

Production hedef domain: https://smartxcar.com

Bu proje şimdilik yalnızca local server + mock Pi testi içindir. Gerçek Raspberry Pi Socket.IO client dönüşümü sonraki aşamadır. Server motor hızını veya fiziksel hareket biçimini belirlemez; sadece dashboard komutlarını doğrulanmış araca relay eder.

## Windows Local Test

1. `python -m venv venv`
2. `venv\Scripts\activate`
3. `pip install -r requirements.txt`
4. `.env.example` dosyasını `.env` olarak kopyalayıp doldurun.
5. Terminal 1: `python app.py`
6. Terminal 2: `python mock_pi_client.py`
7. Tarayıcı: `http://localhost:5000`
8. Login sonrası mock aracın online görünmesini, buton basılı tutulduğunda tekrarlanan komutları, bırakıldığında `stop` komutunu ve sensör güncellemelerini doğrulayın.
9. Dashboard bağlantısı kopunca, logout yapılınca veya yeni mock Pi bağlanınca terminalde `stop`, `horn:off` ve `wiper:0` güvenli durum komutlarının gittiğini doğrulayın.

## Gerekli .env Değerleri

```env
APP_ENV=development
SECRET_KEY=local-secret
ADMIN_PASSWORD=local-admin-password
DEVICE_TOKEN=local-device-token
CAR_ID=car-01
SERVER_URL=http://localhost:5000
```

`SECRET_KEY`, `ADMIN_PASSWORD` ve `DEVICE_TOKEN` boş bırakılamaz.

## Production Deploy Hazırlığı

Dockerfile uygulamayı production'da Gunicorn ile çalıştırır:

```powershell
gunicorn -w 1 --threads 100 --bind 0.0.0.0:5000 app:app
```

Tek worker kullanımı zorunludur; bu MVP'de aktif Raspberry Pi bağlantısı ve dashboard socket listesi process memory içinde tutulur. Birden fazla worker açılırsa bağlantı durumu worker'lar arasında paylaşılmaz.

Dokploy deploy aşamasında env değerleri panelden girilecek; `.env` GitHub'a gönderilmeyecek.

Production env değerleri:

```env
APP_ENV=production
SECRET_KEY=<güçlü secret>
ADMIN_PASSWORD=<güçlü panel parolası>
DEVICE_TOKEN=<güçlü cihaz tokenı>
CAR_ID=car-01
```

`SERVER_URL` server container için zorunlu değildir; mock client veya gerçek Raspberry Pi client tarafından kullanılır. Local mock testte `SERVER_URL=http://localhost:5000`, canlı mock/Pi testte `SERVER_URL=https://smartxcar.com` olmalıdır.

Hedef domain: https://smartxcar.com

Gerçek Raspberry Pi dönüşümü ancak canlı mock client testi tamamlandıktan sonra yapılacak.

## Dosya Yapısı

```text
iot-car-server/
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

## Notlar

- Gerçek Raspberry Pi donanım kodu bu aşamada yoktur.
- GPIO, motor, PWM veya fiziksel dönüş davranışı server tarafında bulunmaz.
- Araç kontrol modeli: yön tuşu basılıyken komut tekrarlanır, bırakıldığında `stop` gönderilir.
