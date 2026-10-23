import os
import time
import threading
import requests
from flask import Flask

app = Flask(__name__)

# Variable global para el precio
latest_btc_price = "Cargando..."

def update_btc_price():
    global latest_btc_price
    while True:
        try:
            res = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=10)
            if res.status_code == 200:
                data = res.json()
                current_price = float(data["bitcoin"]["usd"])
                latest_btc_price = f"${current_price:,.2f} USD"
        except Exception as e:
            print(f"Error obteniendo precio: {e}")
        time.sleep(20)

@app.route("/")
def home():
    global latest_btc_price
    return f"""
    <!DOCTYPE html>
    <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>BTC Live Price</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, sans-serif; background: #0b0e14; color: #f8fafc; text-align: center; padding: 40px 20px; margin: 0; }}
                .card {{ background: #151d2a; max-width: 400px; margin: 0 auto; padding: 30px; border-radius: 16px; border: 1px solid #1e293b; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }}
                h1 {{ color: #38bdf8; font-size: 22px; margin-bottom: 15px; }}
                .price-box {{ background: #0f172a; padding: 20px; border-radius: 12px; margin: 20px 0; border: 1px solid #334155; }}
                .price {{ font-size: 32px; font-weight: bold; color: #f59e0b; }}
                .status {{ color: #22c55e; font-weight: bold; margin-bottom: 10px; }}
                p {{ color: #94a3b8; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="card">
                <h1>🚀 Monitoreo BTC en Vivo</h1>
                <div class="status">● Servidor Activo 24/7</div>
                <div class="price-box">
                    <p style="margin:0 0 5px 0; color:#64748b;">Precio Actual</p>
                    <div class="price">{latest_btc_price}</div>
                </div>
                <p>Panel web limpio y funcionando sin complicaciones.</p>
            </div>
        </body>
    </html>
    """

if __name__ == "__main__":
    threading.Thread(target=update_btc_price, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
