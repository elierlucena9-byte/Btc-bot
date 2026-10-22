import os
import time
import threading
import requests
from flask import Flask

app = Flask(__name__)

# Configuración de Telegram
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

# Variable global para almacenar el precio actual de BTC
latest_btc_price = "Cargando..."

def send_telegram_message(message):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("⚠️ Advertencia: No se han configurado TELEGRAM_TOKEN o CHAT_ID.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=payload, timeout=5)
    except Exception as e:
        print(f"Error enviando mensaje a Telegram: {e}")

def btc_scalping_bot():
    global latest_btc_price
    print("Bot de scalping de BTC iniciado...")
    
    # Enviar mensaje de bienvenida / prueba al iniciar
    send_telegram_message("🟢 *¡Bot de Scalping BTC Iniciado!*\nMonitoreando Binance en tiempo real...")
    
    last_price = None
    
    while True:
        try:
            # Obtener precio actual de Binance (API Pública)
            res = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=8)
            if res.status_code == 200:
                data = res.json()
                current_price = float(data["price"])
                latest_btc_price = f"${current_price:,.2f} USDT"
                
                if last_price is not None:
                    change = ((current_price - last_price) / last_price) * 100
                    # Alerta si hay cambio >= 0.05%
                    if abs(change) >= 0.05:
                        direction = "🚀 Subida detectada" if change > 0 else "⚠️ Bajada detectada"
                        msg = f"*{direction} en BTCUSDT*\nPrecio: `${current_price:,.2f}`\nVariación: `{change:.2f}%`"
                        send_telegram_message(msg)
                        last_price = current_price
                else:
                    last_price = current_price
            else:
                print(f"Error HTTP Binance: {res.status_code}")
                
        except Exception as e:
            print(f"Error consultando Binance: {e}")
            
        time.sleep(15)  # Consulta cada 15 segundos

@app.route("/")
def home():
    global latest_btc_price
    return f"""
    <!DOCTYPE html>
    <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>BTC Scalping Bot</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0b0e14; color: #f8fafc; text-align: center; padding: 30px 15px; margin: 0; }}
                .card {{ background: #151d2a; max-width: 420px; margin: 0 auto; padding: 25px; border-radius: 16px; border: 1px solid #1e293b; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }}
                h1 {{ color: #38bdf8; font-size: 22px; margin-bottom: 20px; }}
                .price-box {{ background: #0f172a; padding: 20px; border-radius: 12px; margin: 15px 0; border: 1px solid #334155; }}
                .price {{ font-size: 28px; font-weight: bold; color: #f59e0b; }}
                .status {{ color: #22c55e; font-weight: bold; display: inline-block; margin-bottom: 10px; }}
                p {{ color: #94a3b8; font-size: 14px; line-height: 1.5; }}
            </style>
        </head>
        <body>
            <div class="card">
                <h1>🚀 BTC Scalping Bot & Terminal</h1>
                <div class="status">● Bot Activo y Monitoreando</div>
                <div class="price-box">
                    <p style="margin:0 0 5px 0; color:#64748b;">Precio Actual de BTC</p>
                    <div class="price">{latest_btc_price}</div>
                </div>
                <p>Las alertas de volatilidad se enviarán automáticamente a tu Telegram.</p>
            </div>
        </body>
    </html>
    """

if __name__ == "__main__":
    # Iniciar bot en segundo plano
    bot_thread = threading.Thread(target=btc_scalping_bot, daemon=True)
    bot_thread.start()
    
    # Iniciar servidor Flask
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

