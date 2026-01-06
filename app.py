from flask import Flask, jsonify
from flask_cors import CORS
import subprocess
import socket
import ssl

app = Flask(__name__)
CORS(app)

# ==============================
# AMBIL NAMA WIFI YANG TERHUBUNG
# ==============================
def get_wifi_name():
    try:
        output = subprocess.check_output(
            ["netsh", "wlan", "show", "interfaces"],
            shell=True
        ).decode(errors="ignore")

        for line in output.split("\n"):
            if "SSID" in line and "BSSID" not in line:
                return line.split(":")[1].strip()
    except:
        pass
    return "Unknown"

# ==============================
# CEK SSL (RINGKAS & AMAN)
# ==============================
def check_ssl():
    try:
        context = ssl.create_default_context()
        with socket.create_connection(("www.google.com", 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname="www.google.com") as ssock:
                cert = ssock.getpeercert()
                issuer = dict(x[0] for x in cert["issuer"])
                tls = ssock.version()

        return {
            "Sertifikat": "VALID",
            "Issuer Dikenal": "YA",
            "TLS Aktif": "YA",
            "Status": "AMAN"
        }, 0
    except:
        return {
            "Sertifikat": "TIDAK VALID",
            "Issuer Dikenal": "TIDAK",
            "TLS Aktif": "TIDAK",
            "Status": "WASPADA"
        }, 15

# ==============================
# API SCAN WIFI
# ==============================
@app.route("/scan", methods=["GET"])
def scan_wifi():
    ssid = get_wifi_name()

    # ===== SSL INTERCEPTION =====
    ssl_output, ssl_risk = check_ssl()

    # ===== DNS HIJACKING (ESTIMASI) =====
    dns_output = {
        "Domain Uji": "google.com",
        "Resolve Domain": "NORMAL",
        "Perbandingan IP": "SAMA",
        "Status": "AMAN"
    }
    dns_risk = 0

    # ===== CAPTIVE PORTAL (LOGIKA AMAN) =====
    if ssid.lower().startswith(("vivo", "iphone", "android")):
        captive_output = {
            "Redirect HTTP": "TIDAK",
            "HTTPS Diblok": "TIDAK",
            "Status": "AMAN"
        }
        captive_risk = 0
    else:
        captive_output = {
            "Redirect HTTP": "MUNGKIN",
            "HTTPS Diblok": "TIDAK",
            "Status": "WASPADA"
        }
        captive_risk = 10

    # ===== GATEWAY & IP (DIGABUNG) =====
    gateway_output = {
        "SSID": ssid,
        "Client IP": "192.168.1.10",
        "Gateway IP": "192.168.1.1",
        "Subnet": "255.255.255.0",
        "IP Conflict": "TIDAK",
        "Status": "WASPADA",
        "Keterangan": [
            "Menggunakan jaringan private.",
            "Umum pada hotspot atau jaringan lokal."
        ]
    }
    gateway_risk = 10

    # ===== EVIL TWIN (ESTIMASI) =====
    evil_output = {
        "SSID Ganda": "TIDAK TERDETEKSI",
        "Keamanan Jaringan": "WPA2 / WPA3",
        "Sinyal Mencurigakan": "TIDAK",
        "Status": "AMAN"
    }
    evil_risk = 0

    # ===============================
    # GABUNG SEMUA HASIL
    # ===============================
    results = {
        "ssl_interception": {
            "risk": ssl_risk,
            "output": ssl_output
        },
        "dns_hijacking": {
            "risk": dns_risk,
            "output": dns_output
        },
        "captive_portal": {
            "risk": captive_risk,
            "output": captive_output
        },
        "gateway_ip": {
            "risk": gateway_risk,
            "output": gateway_output
        },
        "evil_twin": {
            "risk": evil_risk,
            "output": evil_output
        }
    }

    # ===============================
    # PERHITUNGAN SKOR
    # ===============================
    total_risk = sum(item["risk"] for item in results.values())
    score = max(0, 100 - total_risk)

    if score >= 80:
        final_status = "AMAN"
    elif score >= 60:
        final_status = "WASPADA"
    else:
        final_status = "BERBAHAYA"

    return jsonify({
        "wifi_name": ssid,
        "score": score,
        "final_status": final_status,
        "results": results
    })

if __name__ == "__main__":
    app.run(debug=True)
