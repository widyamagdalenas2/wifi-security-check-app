function scanWifi() {
    fetch("http://127.0.0.1:5000/scan")
        .then(res => res.json())
        .then(data => {

            document.getElementById("wifiName").innerText =
                "WiFi: " + data.wifi_name;

            document.getElementById("score").innerText = data.score;
            document.getElementById("finalStatus").innerText =
                "Status: " + data.final_status;

            // Warna skor
            let circle = document.getElementById("scoreCircle");
            if (data.score >= 80) circle.style.borderColor = "green";
            else if (data.score >= 60) circle.style.borderColor = "orange";
            else circle.style.borderColor = "red";

            renderDetail("ssl", data.results.ssl_interception.output, "SSL INTERCEPTION");
            renderDetail("captive", data.results.captive_portal.output, "CAPTIVE PORTAL CHECK");
            renderDetail("dns", data.results.dns_hijacking.output, "DNS HIJACKING CHECK");
            renderDetail("gateway", data.results.gateway_ip.output, "GATEWAY & IP CHECK");
            renderDetail("evil", data.results.evil_twin.output, "EVIL TWIN CHECK");
        });
}

function renderDetail(id, data, title) {
    let text = `[ ${title} ]\n\n`;

    for (let key in data) {
        if (Array.isArray(data[key])) {
            text += key + ":\n";
            data[key].forEach(item => {
                text += "- " + item + "\n";
            });
        } else {
            text += key.padEnd(22) + ": " + data[key] + "\n";
        }
    }

    document.getElementById(id).innerText = text;
}

function toggle(id) {
    let el = document.getElementById(id);
    el.style.display = el.style.display === "block" ? "none" : "block";
}
