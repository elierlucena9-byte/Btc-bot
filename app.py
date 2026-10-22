import threading
import time
import json
import os
import urllib.request
import urllib.parse
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

# Configuración desde variables de entorno (Secrets)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()
SYMBOL = os.getenv("SYMBOL", "BTCUSDT").strip().upper()

# Historial global para mostrar las señales en la página web
signals_history = []
bot_status = "Iniciando..."

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BTC Scalping & Telegram Bot Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0b0e11; color: #f0f6fc; margin: 0; padding: 20px; }
        h1 { color: #58a6ff; font-size: 1.5rem; text-align: center; }
        .card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 15px; margin-bottom: 15px; }
        .signal-item { padding: 10px; margin: 5px 0; border-radius: 6px; font-size: 0.9rem; }
        .long { background: rgba(46, 160, 67, 0.2); border-left: 4px solid #2ea043; }
        .short { background: rgba(248, 81, 73, 0.2); border-left: 4px solid #f85149; }
        .status { text-align: center; font-weight: bold; color: #3fb950; margin-bottom: 20px; }
    </style>
</head>
<body>
    <h1>🚀 BTC Scalping Bot & Terminal</h1>
    <div class="status" id="bot-status">Estado: Conectando con el Bot...</div>
    
    <div class="card">
        <h3>📊 Precio Actual de BTC</h3>
        <h2 id="btc-price" style="text-align: center; color: #f0b90b;">Cargando...</h2>
    </div>

    <div class="card">
        <h3>📡 Últimas Señales Enviadas a Telegram</h3>
        <div id="signals-container">Cargando señales recientes...</div>
    </div>

    <script>
        async function updateData() {
            try {
                let response = await fetch('/api/data');
                let data = await response.json();
                document.getElementById('btc-price').innerText = "$" + data.price.toLocaleString() + " USDT";
                document.getElementById('bot-status').innerText = "Estado del Bot: " + data.status;
                
                let container = document.getElementById('signals-container');
                if (data.signals.length === 0) {
                    container.innerHTML = "<p>Esperando el primer impulso del mercado...</p>";
                } else {
                    container.innerHTML = data.signals.map(s => `
                        <div class="signal-item ${s.type}">
                            <strong>${s.title}</strong><br>
                            Precio: <code>${s.price}</code> | Var: <code>${s.change}</code><br>
                            <small>${s.time}</small>
                        </div>
                    `).join('');
                }
            } catch (e) {
                console.error(e);
            }
        }
        setInterval(updateData, 3000);
        updateData();
    </script>
</body>
</html>
"""

def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = json.dumps({"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"Error enviando Telegram: {e}")

latest_price = 0.0

def trading_bot_loop():
    global latest_price, bot_status
    bot_status = "Activo y Monitoreando (1m, 5m, 15m)"
    
    last_alert = {
        "1m": {"up": 0, "down": 0},
        "5m": {"up": 0, "down": 0},
        "15m": {"up": 0, "down": 0}
    }

    while True:
        try:
            # Consultar precio actual
            price_url = f"https://api.binance.com/api/v3/ticker/price?symbol={SYMBOL}"
            res = urllib.request.urlopen(price_url, timeout=10)
            latest_price = float(json.loads(res.read().decode("utf-8"))["price"])

            # Consultar velas (1m, 5m, 15m)
            def get_open(interval):
                kline_url = f"https://api.binance.com/api/v3/klines?symbol={SYMBOL}&interval={interval}&limit=1"
                k_res = urllib.request.urlopen(kline_url, timeout=10)
                return float(json.loads(k_res.read().decode("utf-8"))[0][1])

            open_1m = get_open("1m")
            open_5m = get_open("5m")
            open_15m = get_open("15m")

            c_1m = ((latest_price - open_1m) / open_1m) * 100
            c_5m = ((latest_price - open_5m) / open_5m) * 100
            c_15m = ((latest_price - open_15m) / open_15m) * 100

            current_time = time.time()
            readable_time = time.strftime('%H:%M:%S', time.localtime(current_time))

            def register_signal(title, t_type, change_str):
                msg = f"*{title}*\nPrecio: `{latest_price}` USDT\nVariación: `{change_str}`"
                send_telegram(msg)
                signals_history.insert(0, {
                    "title": title,
                    "type": t_type,
                    "price": latest_price,
                    "change": change_str,
                    "time": readable_time
                })
                if len(signals_history) > 10: # Mantener solo las últimas 10
                    signals_history.pop()

            # 1M Scalping
            if c_1m >= 0.05 and (current_time - last_alert["1m"]["up"] > 45):
                register_signal("⚡ PROBABLE LONG - SCALPING RÁPIDO (1M)", "long", f"+{c_1m:.3f}%")
                last_alert["1m"]["up"] = current_time
            elif c_1m <= -0.05 and (current_time - last_alert["1m"]["down"] > 45):
                register_signal("⚡ PROBABLE SHORT - SCALPING RÁPIDO (1M)", "short", f"{c_1m:.3f}%")
                last_alert["1m"]["down"] = current_time

            # 5M Scalping
            if c_5m >= 0.12 and (current_time - last_alert["5m"]["up"] > 120):
                register_signal("🚀 PROBABLE LONG - SCALPING 5M", "long", f"+{c_5m:.3f}%")
                last_alert["5m"]["up"] = current_time
            elif c_5m <= -0.12 and (current_time - last_alert["5m"]["down"] > 120):
                register_signal("🔻 PROBABLE SHORT - SCALPING 5M", "short", f"{c_5m:.3f}%")
                last_alert["5m"]["down"] = current_time

            # 15M Tardío
            if c_15m >= 0.25 and (current_time - last_alert["15m"]["up"] > 300):
                register_signal("⏳ POSITIVO TARDÍO (LONG - 15M)", "long", f"+{c_15m:.3f}%")
                last_alert["15m"]["up"] = current_time
            elif c_15m <= -0.25 and (current_time - last_alert["15m"]["down"] > 300):
                register_signal("⏳ POSITIVO TARDÍO (SHORT - 15M)", "short", f"{c_15m:.3f}%")
                last_alert["15m"]["down"] = current_time

        except Exception as e:
            print(f"Error en el bucle del bot: {e}")

        time.sleep(10)

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/data')
def api_data():
    return jsonify({
        "price": latest_price,
        "status": bot_status,
        "signals": signals_history
    })

if __name__ == '__main__':
    # Iniciar el bot de trading en un hilo secundario (background thread)
    t = threading.Thread(target=trading_bot_loop, daemon=True)
    t.start()
    
    # Iniciar el servidor web Flask
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
