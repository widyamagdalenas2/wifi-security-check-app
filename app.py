from flask import Flask, jsonify
from flask_cors import CORS
import subprocess
import socket
import ssl
import requests
import re

app = Flask(__name__)
CORS(app)

# ==============================
# AMBIL NAMA WIFI TERHUBUNG
# ==============================
def get_wifi_name():
    try:
        output = subprocess.check_output(
            ["netsh", "wlan", "show", "interfaces"],
            shell=True
        ).decode(errors="ignore")

        for line in output.splitlines():
            if "SSID" in line and "BSSID" not in line:
                return line.split(":")[1].strip()
    except:
        pass
    return "Unknown"

# ==============================
# SSL INTERCEPTION
# ==============================
def check_ssl(host="www.google.com", port=443):
    result = {
        "TLS Aktif": False,
        "Sertifikat Valid": False,
        "Issuer Dikenal": False
    }

    try:
        context = ssl.create_default_context()
        with socket.create_connection((host, port), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()


                result["TLS Aktif"] = True
                result["Sertifikat Valid"] = True

                issuer = cert.get("issuer")
                result["Issuer Dikenal"] = True if issuer else False

    except Exception as e:
        result["Error"] = str(e)

    return result


# ==============================
# DNS HIJACKING
# ==============================
def check_dns(domain="facebook.com"):
    result = {
        "Domain": domain,
        "Local DNS IP": "Unknown",
        "Public DNS IP": "Unknown",
        "Match": False
    }

    try:
        # DNS lokal (default OS)
        local_ip = socket.gethostbyname(domain)
        result["Local DNS IP"] = local_ip
    except:
        pass

    try:
        # DNS publik (Google DNS)
        import dns.resolver
        resolver = dns.resolver.Resolver()
        resolver.nameservers = ["8.8.8.8"]
        answers = resolver.resolve(domain, "A")
        public_ip = answers[0].to_text()
        result["Public DNS IP"] = public_ip
    except:
        pass

    if result["Local DNS IP"] == result["Public DNS IP"]:
        result["Match"] = True

    return result


# ==============================
# CAPTIVE PORTAL
# ==============================
def check_captive():
    test_url = "http://neverssl.com/"
    result = {
        "Test URL": test_url,
        "HTTP Status": "Unknown",
        "Redirected": "Tidak",
        "Final URL": "Unknown",
        "Captive Portal": "Tidak"
    }

    try:
        response = requests.get(
            test_url,
            timeout=5,
            allow_redirects=True
        )

        result["HTTP Status"] = response.status_code
        result["Final URL"] = response.url

        if response.history:
            result["Redirected"] = "YA"

        # Jika tidak sampai ke neverssl.com → indikasi captive portal
        if "neverssl.com" not in response.url.lower():
            result["Captive Portal"] = "YA"

        # Jika status bukan 200 juga mencurigakan
        if response.status_code != 200:
            result["Captive Portal"] = "YA"

    except:
        result["Captive Portal"] = "YA"

    return result


# ==============================
# GATEWAY
# ==============================
def check_gateway():
    result = {
        "Client IP": "Unknown",
        "Subnet Mask": "Unknown",
        "Gateway IP": "Unknown",
        "MAC Gateway": "Unknown",
        "Gateway Response": "Normal",
        "IP Conflict": "Tidak"
    }

    try:
        # Ambil ipconfig
        output = subprocess.check_output("ipconfig", shell=True).decode(errors="ignore")

        for line in output.splitlines():
            if "IPv4 Address" in line:
                result["Client IP"] = line.split(":")[1].strip()
            elif "Subnet Mask" in line:
                result["Subnet Mask"] = line.split(":")[1].strip()
            elif "Default Gateway" in line and ":" in line:
                result["Gateway IP"] = line.split(":")[1].strip()
    except:
        pass

    try:
        # Ambil MAC gateway dari ARP
        arp = subprocess.check_output("arp -a", shell=True).decode(errors="ignore")
        if result["Gateway IP"] in arp:
            for line in arp.splitlines():
                if result["Gateway IP"] in line:
                    result["MAC Gateway"] = line.split()[1]
    except:
        pass

    return result


# ==============================
# EVIL TWIN
# ==============================
def check_evil_twin(ssid):
    try:
        output = subprocess.check_output(
            ["netsh", "wlan", "show", "networks", "mode=bssid"],
            shell=True
        ).decode(errors="ignore")

        count = output.count(ssid)
        if count > 1:
            return {"Jumlah AP": count, "Status": "WASPADA"}, 20
        return {"Jumlah AP": 1, "Status": "AMAN"}, 0
    except:
        return {"Status": "UNKNOWN"}, 10

# ==============================
# API SCAN
# ==============================
@app.route("/scan")
def scan():
    ssid = get_wifi_name()
    results = {}

    # ======================
    # SSL CHECK
    # ======================
    ssl_result = check_ssl("www.google.com")

    ssl_risk = 0
    if not ssl_result.get("TLS Aktif"):
        ssl_risk += 30
    if not ssl_result.get("Sertifikat Valid"):
        ssl_risk += 30
    if not ssl_result.get("Issuer Dikenal"):
        ssl_risk += 20

    results["ssl_interception"] = {
        "risk": ssl_risk,
        "output": {
            "Target Host": "www.google.com",
            "TLS Aktif": "YA" if ssl_result["TLS Aktif"] else "TIDAK",
            "Sertifikat Valid": "YA" if ssl_result["Sertifikat Valid"] else "TIDAK",
            "Issuer Dikenal": "YA" if ssl_result["Issuer Dikenal"] else "TIDAK",
            "Status": "AMAN" if ssl_risk == 0 else "WASPADA",
            "Keterangan": [
                "Pemeriksaan TLS dilakukan secara langsung",
                "Koneksi HTTPS diverifikasi end-to-end",
                "Tidak menggunakan packet sniffing"
            ]
        }
    }

    # ======================
    # DNS HIJACKING
    # ======================
    dns_result = check_dns()

    dns_risk = 0
    if not dns_result["Match"]:
        dns_risk = 30

    results["dns_hijacking"] = {
        "risk": dns_risk,
        "output": {
            "SSID": ssid,
            "Domain Uji": dns_result["Domain"],
            "IP DNS Lokal": dns_result["Local DNS IP"],
            "IP DNS Publik": dns_result["Public DNS IP"],
            "DNS Cocok": "YA" if dns_result["Match"] else "TIDAK",
            "Status": "AMAN" if dns_risk == 0 else "WASPADA"
        }
    }

    # ======================
    # CAPTIVE PORTAL
    # ======================
    captive_output = check_captive()
    captive_risk = 25 if captive_output["Captive Portal"] == "YA" else 0

    results["captive_portal"] = {
        "risk": captive_risk,
        "output": {
            "SSID": ssid,
            "URL Test": captive_output["Test URL"],
            "HTTP Status": captive_output["HTTP Status"],
            "Redirect": captive_output["Redirected"],
            "Final URL": captive_output["Final URL"],
            "Captive Portal": captive_output["Captive Portal"],
            "Status": "AMAN" if captive_risk == 0 else "TERDETEKSI"
        }
    }

    # ======================
    # EVIL TWIN
    # ======================
    evil_output, evil_risk = check_evil_twin(ssid)
    results["evil_twin"] = {
        "risk": evil_risk,
        "output": evil_output
    }

    # ======================
    # GATEWAY
    # ======================
    gateway_output = check_gateway()
    results["gateway"] = {
        "risk": 0,
        "output": gateway_output
    }

    # ======================
    # FINAL SCORE
    # ======================
    total_risk = sum(item["risk"] for item in results.values())
    score = max(0, 100 - total_risk)

    status = "AMAN" if score >= 70 else "WASPADA" if score >= 50 else "BERBAHAYA"

    return jsonify({
        "wifi_name": ssid,
        "score": score,
        "final_status": status,
        "results": results
    })


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
