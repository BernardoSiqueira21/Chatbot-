from flask import Flask, render_template, request, jsonify, session
from chatbot.service import processar_mensagem

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = "chatbot_consumidor_secret_key_2026"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    dados = request.get_json(silent=True) or {}
    mensagem = (dados.get("mensagem") or "").strip()

    if not mensagem:
        return jsonify({
            "resposta": "Digite uma mensagem para eu conseguir te ajudar melhor.",
            "intencao": "vazia",
            "confianca": 0,
            "contexto": session.get("contexto", {})
        })