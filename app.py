from flask import Flask, render_template, request, jsonify, session
from chatbot.service import processar_mensagem

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = "cdc_chatbot_secret_2026_consumidor"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    try:
        dados = request.get_json(force=True, silent=True)
    except Exception:
        dados = None

    if not dados:
        return jsonify({"resposta": "Requisicao invalida.", "intencao": "erro", "dicas": [], "relacionados": [], "oferta": ""}), 400

    mensagem = ""
    try:
        mensagem = str(dados.get("mensagem", "")).strip()
    except Exception:
        mensagem = ""

    if not mensagem:
        return jsonify({"resposta": "Por favor, escreva sua duvida.", "intencao": "vazia", "dicas": [], "relacionados": [], "oferta": ""})

    historico = session.get("historico", [])
    contexto = session.get("contexto", {})

    if not isinstance(historico, list):
        historico = []
    if not isinstance(contexto, dict):
        contexto = {}

    try:
        resultado = processar_mensagem(mensagem, historico, contexto)
    except Exception as e:
        return jsonify({
            "resposta": "Ocorreu um erro interno. Pode tentar novamente?",
            "intencao": "erro",
            "dicas": [],
            "relacionados": [],
            "oferta": "",
        })

    historico.append({
        "usuario": mensagem,
        "bot": resultado.get("resposta", ""),
        "intencao": resultado.get("intencao", "desconhecida"),
    })

    historico = historico[-60:]
    session["historico"] = historico
    session["contexto"] = resultado.get("contexto", {})

    return jsonify(resultado)

@app.route("/reset", methods=["POST"])
def reset():
    session.pop("historico", None)
    session.pop("contexto", None)
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(debug=True)
