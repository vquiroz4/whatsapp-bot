import os
from flask import Flask, request
import requests

app = Flask(__name__)

TOKEN = os.environ.get("ACCESS_TOKEN")
PHONE_ID = os.environ.get("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "mi_token_secreto_123")

# Memoria simple para saber en qué pregunta va cada usuario
usuarios = {}

def enviar_mensaje(to, texto):
    url = f"https://graph.facebook.com/v20.0/{PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
    payload = {"messaging_product": "whatsapp", "to": to, "text": {"body": texto}}
    requests.post(url, headers=headers, json=payload)

def enviar_botones(to):
    url = f"https://graph.facebook.com/v20.0/{PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": "¡Hola! 👋 Soy tu asistente. ¿En qué te ayudo hoy?"},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "btn_productos", "title": "🛍️ Ver Productos"}},
                    {"type": "reply", "reply": {"id": "btn_precios", "title": "💰 Precios"}},
                    {"type": "reply", "reply": {"id": "btn_humano", "title": "👤 Hablar con humano"}}
                ]
            }
        }
    }
    requests.post(url, headers=headers, json=payload)

def enviar_lista_productos(to):
    url = f"https://graph.facebook.com/v20.0/{PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "body": {"text": "Elige la categoría que te interesa:"},
            "action": {
                "button": "Ver opciones",
                "sections": [{
                    "title": "Nuestros productos",
                    "rows": [
                        {"id": "prod_1", "title": "Opción A", "description": "La más vendida"},
                        {"id": "prod_2", "title": "Opción B", "description": "La más económica"},
                        {"id": "prod_3", "title": "Opción C", "description": "Premium"}
                    ]
                }]
            }
        }
    }
    requests.post(url, headers=headers, json=payload)

@app.route('/')
def home(): return "Bot 24/7 Activo"

@app.route('/webhook', methods=['GET'])
def verify():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return "Error", 403

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    try:
        entry = data['entry'][0]['changes'][0]['value']
        if 'messages' in entry:
            msg = entry['messages'][0]
            numero = msg['from']
            numero_enviar = numero
            if numero.startswith("521"): numero_enviar = "52" + numero[3:]

            # Si es un botón
            if msg['type'] == 'interactive':
                opcion = msg['interactive']['button_reply']['id'] if 'button_reply' in msg['interactive'] else msg['interactive']['list_reply']['id']
                print(f"Boton: {opcion}")

                if opcion == "btn_productos": enviar_lista_productos(numero_enviar)
                elif opcion == "btn_precios": enviar_mensaje(numero_enviar, "Nuestros precios van desde $199. ¿Cuál te interesa? (Escribe A, B o C)")
                elif opcion == "btn_humano": enviar_mensaje(numero_enviar, "Un asesor te contactará en breve. Déjanos tu nombre por favor.")
                elif "prod_" in opcion: enviar_mensaje(numero_enviar, f"¡Excelente! Elegiste {opcion}. ¿Quieres que te lo apartemos? Responde SI o NO")

            else: # Si es texto normal
                texto = msg['text']['body'].lower()
                if "hola" in texto or "menu" in texto:
                    enviar_botones(numero_enviar)
                else:
                    enviar_botones(numero_enviar)

    except Exception as e:
        print(f"Error: {e}")
    return "OK", 200

app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
