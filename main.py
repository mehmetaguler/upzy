import smtplib
import pytz
import schedule
import time
import requests
from datetime import datetime
from email.mime.text import MIMEText
import os
from flask import Flask, render_template, jsonify, request
import threading
import json
from flask import redirect

# Flask uygulamasını oluştur
app = Flask(__name__, static_folder="static", template_folder="templates")


# Jinja2 Environment'ına fromjson filtresini ekle (artık kullanılmayacak ama kalsın)
@app.template_filter('fromjson')
def fromjson_filter(value):
    return json.loads(value)


# Saat dilimi
istanbul = pytz.timezone("Europe/Istanbul")

# URL listesi
urls = [
    "https://www.lcwaikiki.rs/sr-RS/RS/", "https://www.lcwaikiki.rs/en-US/RS",
    "https://www.lcwaikiki.ge/en-US/GE", "https://www.lcwaikiki.ge/ka-GE/GE",
    "https://www.lcwaikiki.de/de-DE/DE", "https://www.lcwaikiki.de/tr-TR/DE",
    "https://www.lcwaikiki.fr/fr-FR/FR", "https://www.lcwaikiki.fr/tr-TR/FR",
    "https://www.lcwaikiki.it/en-US/IT", "https://www.lcwaikiki.bg/en-US/BG",
    "https://www.lcwaikiki.bg/bg-BG/BG", "https://www.lcwaikiki.ro/ro-RO/RO",
    "https://www.lcwaikiki.ro/en-US/RO", "https://www.lcwaikiki.ru/ru-RU/RU",
    "https://www.lcwaikiki.ua/uk-UA/UA", "https://www.lcwaikiki.ua/ru-RU/UA",
    "https://www.lcwaikiki.kz/kk-KZ/KZ", "https://www.lcwaikiki.kz/ru-RU/KZ",
    "https://www.lcwaikiki.ma/fr-FR/MA", "https://www.lcwaikiki.ma/ar-MA/MA",
    "https://www.lcwaikiki.ma/en-US/MA", "https://www.lcwaikiki.eg/ar-EG/EG",
    "https://www.lcwaikiki.eg/en-US/EG", "https://www.lcwaikiki.iq/en",
    "https://www.lcwaikiki.iq/ku", "https://www.yokboylesite29291.com/lcw"
]


def run_schedule():
    schedule.every().day.at("08:00").do(check_urls)
    schedule.every().day.at("12:00").do(check_urls)
    schedule.every().day.at("18:00").do(check_urls)
    schedule.every().day.at("00:00").do(check_urls)
    schedule.every().day.at("10:00").do(daily_report)

    print("🟢 Upzy çalışıyor... Takvim ayarlandı.")

    while True:
        schedule.run_pending()
        time.sleep(1)


# Mail gönderici
def send_email(subject, html_body):
    sender_email = "upzybot@gmail.com"
    receiver_email = "mehmeta.guler@gmail.com"
    app_password = os.environ.get("SMTP_PSW", "yfzy lpds azab tswm")

    msg = MIMEText(html_body, "html")
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = receiver_email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, app_password)
            server.send_message(msg)
        print(f"📧 Mail gönderildi: {subject}")
    except Exception as e:
        print(f"❌ Mail gönderilemedi: {e}")


# 🔁 Hata kontrolü
def check_urls():
    log_file = "upzy_logs.json"

    try:
        with open(log_file, "r", encoding='utf-8') as f:
            logs_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        logs_data = {"latest": [], "all": []}

    logs_data["latest"] = [
    ]  # Her yeni kontrol başlamadan önce 'latest' listesini temizle

    for url in urls:
        try:
            start_time = datetime.now(istanbul)
            response = requests.get(url, timeout=5)
            duration = (datetime.now(istanbul) - start_time).total_seconds()

            print(
                f"[{datetime.now(istanbul).strftime('%Y-%m-%d %H:%M:%S')}] {url} ✅ {response.status_code} - {duration:.2f}s"
            )

            new_entry = {
                "url": url,
                "status": f"{response.status_code} UP",
                "time": f"{duration:.2f}",
                "timestamp":
                datetime.now(istanbul).strftime("%Y-%m-%d %H:%M:%S")
            }

            logs_data["latest"].append(new_entry)
            logs_data["all"].insert(0, new_entry)

        except Exception as e:
            now = datetime.now(istanbul)
            msg = f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] {url} ❌ DOWN: {e}"
            print(msg)

            new_entry = {
                "url": url,
                "status": "DOWN",
                "time": "N/A",  # Hata durumunda süre "N/A"
                "timestamp":
                datetime.now(istanbul).strftime("%Y-%m-%d %H:%M:%S")
            }

            logs_data["latest"].append(new_entry)
            logs_data["all"].insert(0, new_entry)

            error_html = f"""
            <html>
              <body style="font-family: Arial, sans-serif; background-color: #f6f6f6; padding: 30px;">
                <div style="max-width: 600px; margin: auto; background-color: #ffffff; padding: 25px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.05); border: 1px solid #eee;">

                  <h2 style="color: #D9534F; margin-bottom: 10px;">🚨 Upzy Uyarısı</h2>
                  <p style="font-size: 15px; color: #333;">Aşağıdaki site kontrol edilirken bir hata oluştu:</p>

                  <div style="background-color: #f2dede; padding: 15px; border-left: 6px solid #d9534f; color: #a94442; border-radius: 6px; margin-top: 15px;">
                    <pre style="white-space: pre-wrap; font-size: 14px;">{msg}</pre>
                  </div>

                  <p style="font-size: 12px; color: #999; margin-top: 25px; text-align: center;">
                    Bu e-posta <strong>Upzy</strong> tarafından otomatik olarak gönderilmiştir.
                  </p>
                  <p style="text-align: center; font-weight: bold; font-size: 14px; color: #d9534f;">upzy🚨</p>

                </div>
              </body>
            </html>
            """
            try:
                send_email("🚨 Upzy Uyarısı: Site Çöktü!", error_html)
            except Exception as e:
                print(f"[WARN] Mail gönderilemedi: {e}")

    with open(log_file, "w", encoding='utf-8') as f:
        json.dump(logs_data, f, indent=2)


# 📬 Günlük rapor (hata olmasa bile)
def daily_report():
    logs = ""
    for url in urls:
        try:
            start_time = datetime.now(istanbul)
            response = requests.get(url, timeout=5)
            duration = (datetime.now(istanbul) - start_time).total_seconds()
            logs += f"<tr><td>{url}</td><td>{response.status_code}</td><td>{duration:.2f} s</td></tr>"
        except Exception as e:
            logs += f"<tr style='color:red;'><td>{url}</td><td>DOWN</td><td>{e}</td></tr>"

    now = datetime.now(istanbul).strftime("%Y-%m-%d %H:%M")
    html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; background-color: #f8f8f8; padding: 30px;">
        <div style="background-color: #fff; padding: 20px; border-radius: 8px; border: 1px solid #ddd; max-width: 700px; margin: auto;">
          <h2 style="color:#d9534f;">📊 Upzy Günlük Rapor – {now}</h2>
          <p>Tüm sitelerin son kontrol sonuçları aşağıdadır:</p>
          <table style="width:100%; border-collapse: collapse;">
            <tr style="background:#f2f2f2;">
              <th style="text-align:left; padding: 8px;">URL</th>
              <th style="text-align:left; padding: 8px;">Durum</th>
              <th style="text-align:left; padding: 8px;">Yanıt Süresi</th>
            </tr>
            {logs}
          </table>
          <p style="font-size:12px; color: #999; margin-top: 20px;">Bu rapor <strong>Upzy</strong> tarafından otomatik olarak gönderilmiştir.</p>
          <p style="text-align:center; font-weight: bold; font-size: 14px; color: #d9534f;">upzy🚨</p>
        </div>
      </body>
    </html>
    """
    send_email("📊 Upzy Günlük Durum Raporu", html)


@app.route("/")
def index():
    return render_template("index.html")


# HTML sayfasını render eden route
@app.route("/upzy")
def upzy():
    view = request.args.get("view", "latest")
    lang = request.args.get("lang", "tr")
    # Bu sayfaya logs verisi göndermeyeceğiz, JavaScript API'den alacak
    return render_template("upzy.html", view=view, lang=lang)


# Verileri döndüren yeni API uç noktası
@app.route("/api/upzy_logs", methods=['GET'])
def get_upzy_logs():
    view = request.args.get("view", "latest")  # view parametresini buradan al
    try:
        with open("upzy_logs.json", "r", encoding='utf-8') as f:
            all_logs = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        all_logs = {"latest": [], "all": []}

    if view == "latest":
        logs_to_return = all_logs.get("latest", [])
    elif view == "all":
        logs_to_return = all_logs.get("all", [])
    else:  # errors
        logs_to_return = [
            log for log in all_logs.get("all", []) if log["status"] == "DOWN"
        ]
    return jsonify(logs_to_return)


# Bu route, AJAX isteği ile tetiklenecek
@app.route('/trigger_check', methods=['POST'])
def trigger_check():
    try:
        # İstemciden gelen view parametresini al (şimdilik sadece tetikleme için kullanılıyor)
        # check_urls() fonksiyonu tüm logları güncellediği için burada view'a özel bir işlem yapmıyoruz
        requested_view = request.json.get('view', 'latest')

        check_urls(
        )  # URL kontrol fonksiyonunu çağır (bu fonksiyon upzy_logs.json dosyasını günceller)

        # check_urls() bittikten sonra logları doğrudan get_upzy_logs API'sinden çekmesi daha doğru
        # Bu kısım aslında artık gerekli değil, çünkü trigger_check sadece check_urls'ı çalıştırmalı
        # ve front-end DataTables'ı yeniden yüklemeli. Ancak şimdilik response formatını koruyalım.
        try:
            with open("upzy_logs.json", "r", encoding='utf-8') as f:
                updated_logs = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            updated_logs = {"latest": [], "all": []}

        if requested_view == "latest":
            logs_to_return = updated_logs.get('latest', [])
        elif requested_view == "all":
            logs_to_return = updated_logs.get('all', [])
        else:  # errors
            logs_to_return = [
                log for log in updated_logs.get("all", [])
                if log["status"] == "DOWN"
            ]

        return jsonify(
            status='success',
            message='URL kontrolü tamamlandı ve loglar güncellendi.',
            data=logs_to_return  # Trigger sonrası güncel veriyi döndürüyoruz
        )
    except Exception as e:
        print(f"Hata: {e}")  # Konsola hatayı yaz
        return jsonify(status='error', message=str(e)), 500


if __name__ == "__main__":
    threading.Thread(target=run_schedule).start()
    app.run(host="0.0.0.0", port=81)
