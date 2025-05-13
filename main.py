import smtplib
import pytz
import schedule
import time
import requests
from datetime import datetime
from email.mime.text import MIMEText
import os
from flask import Flask, render_template
import threading
import json
from flask import redirect, request


def write_log_entry(url, status, duration):
    log_file = "upzy_logs.json"
    try:
        with open(log_file, "r") as f:
            logs = json.load(f)
    except:
        logs = {"latest": [], "all": []}

    now = datetime.now(istanbul).strftime("%Y-%m-%d %H:%M:%S")
    new_entry = {
        "url": url,
        "status": status,
        "time": f"{duration:.2f}",
        "timestamp": now
    }

    # İlk URL kontrolünde latest listesini temizle
    if url == urls[0]:
        logs["latest"] = []
    
    # Latest ve all listelerine ekle
    logs["latest"].append(new_entry)
    logs["all"].insert(0, new_entry)

    with open(log_file, "w") as f:
        json.dump(logs, f, indent=2)


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
    import schedule
    import time

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
    app_password = os.environ["SMTP_PSW"]

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
    for url in urls:
        try:
            start_time = datetime.now(istanbul)
            response = requests.get(url, timeout=5)
            duration = (datetime.now(istanbul) - start_time).total_seconds()

            print(
                f"[{datetime.now(istanbul)}] {url} ✅ {response.status_code} - {duration:.2f}s"
            )
            write_log_entry(url, f"{response.status_code} UP", duration)

        except Exception as e:
            now = datetime.now(istanbul)
            msg = f"[{now}] {url} ❌ DOWN: {e}"
            print(msg)
            write_log_entry(url, "DOWN", 0)

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
            send_email("🚨 Upzy Uyarısı: Site Çöktü!", error_html)


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


app = Flask(__name__, static_folder="static", template_folder="templates")


@app.route("/")
def index():
    return render_template("index.html")


from flask import request  # üstte import edilmediyse bunu da ekle


@app.route("/check-now")
def check_now():
    lang = request.args.get("lang", "tr")  # dil parametresini al
    check_urls()
    return redirect(f"/upzy?lang={lang}")


@app.route("/upzy")
def upzy():
    view = request.args.get("view", "latest")
    lang = request.args.get("lang", "tr")

    try:
        with open("upzy_logs.json", "r") as f:
            all_logs = json.load(f)
    except:
        all_logs = {"latest": [], "all": []}

    if view == "latest":
        logs = all_logs.get("latest", [])
    elif view == "all":
        logs = all_logs.get("all", [])
    else:  # errors
        logs = [log for log in all_logs.get("all", []) if log["status"] == "DOWN"]

    return render_template("upzy.html", logs=logs, view=view, lang=lang)


if __name__ == "__main__":

    threading.Thread(target=run_schedule).start()
    app.run(host="0.0.0.0", port=81)
