from dotenv import load_dotenv
load_dotenv()

import os, random, time
from collections import defaultdict
from flask import Flask, render_template, request, jsonify, session
from chatbot.agent import processar_mensagem
from chatbot.llm   import llm_disponivel

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "cdc_chatbot_llm_2026_v2")

NOMES_AGENTE = ["Marina","Camila","Juliana","Fernanda","Patricia",
                "Amanda","Beatriz","Larissa","Gabriela","Aline"]

_rate_data = defaultdict(list)
RATE_LIMIT  = 30
RATE_WINDOW = 60
_last_cleanup = time.time()

def _rate_ok(ip):
    global _last_cleanup
    agora = time.time()
    if agora - _last_cleanup > 300:
        ips_antigos = [k for k, v in _rate_data.items()
                       if not any(agora - t < RATE_WINDOW for t in v)]
        for k in ips_antigos:
            del _rate_data[k]
        _last_cleanup = agora
    _rate_data[ip] = [t for t in _rate_data[ip] if agora - t < RATE_WINDOW]
    if len(_rate_data[ip]) >= RATE_LIMIT:
        return False
    _rate_data[ip].append(agora)
    return True

def _compactar_hist(hist):
    compacto = []
    for item in hist:
        compacto.append({
            "usuario":  str(item.get("usuario",""))[:120],
            "bot":      str(item.get("bot",""))[:180],
            "intencao": item.get("intencao",""),
            "fonte":    item.get("fonte",""),
            "usou_llm": bool(item.get("usou_llm")),
            "usou_web": bool(item.get("usou_web")),
        })
    return compacto[-6:]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    ip = request.headers.get("X-Forwarded-For", request.remote_addr or "local").split(",")[0].strip()
    if not _rate_ok(ip):
        return jsonify({
            "resposta": "Muitas mensagens em pouco tempo. Aguarde um momento.",
            "intencao": "rate_limit", "fonte": "sistema",
            "usou_llm": False, "usou_web": False,
            "dicas": [], "relacionados": [], "oferta": "", "kb_score": 0.0,
        }), 429

    try:
        dados = request.get_json(force=True, silent=True) or {}
    except Exception:
        dados = {}

    mensagem = str(dados.get("mensagem", "")).strip()
    if not mensagem:
        return jsonify({
            "resposta": "Por favor, escreva sua dúvida.",
            "intencao": "vazia", "fonte": "sistema",
            "usou_llm": False, "usou_web": False,
            "dicas": [], "relacionados": [], "oferta": "", "kb_score": 0.0,
        })

    historico = session.get("historico", [])
    contexto  = session.get("contexto",  {})
    if not isinstance(historico, list): historico = []
    if not isinstance(contexto,  dict): contexto  = {}

    if "nome_agente" not in contexto:
        contexto["nome_agente"] = session.get("nome_agente") or random.choice(NOMES_AGENTE)
    session["nome_agente"] = contexto["nome_agente"]

    try:
        resultado = processar_mensagem(mensagem, historico, contexto)
    except Exception as e:
        app.logger.exception("Erro ao processar mensagem")
        return jsonify({
            "resposta": "Tive um problema interno. Pode tentar novamente?",
            "intencao": "erro", "fonte": "erro",
            "usou_llm": False, "usou_web": False,
            "dicas": [], "relacionados": [], "oferta": "", "kb_score": 0.0,
        })

    historico.append({
        "usuario":      mensagem,
        "bot":          resultado.get("resposta", ""),
        "intencao":     resultado.get("intencao", ""),
        "fonte":        resultado.get("fonte", ""),
        "usou_llm":     bool(resultado.get("usou_llm")),
        "usou_web":     bool(resultado.get("usou_web")),
        "kb_score":     float(resultado.get("kb_score", 0.0)),
        "llm_tempo_ms": resultado.get("llm_tempo_ms"),
    })

    stats = session.get("stats", {"total":0,"via_kb":0,"via_llm":0,"via_web":0,"fallback":0})
    stats["total"] += 1
    fonte = resultado.get("fonte", "")
    if fonte in ("llm","llm_web"):         stats["via_llm"] += 1
    elif "base_conhecimento" in fonte:     stats["via_kb"]  += 1
    elif "web" in fonte:                   stats["via_web"] += 1
    else:                                  stats["fallback"] += 1

    session["historico"] = _compactar_hist(historico)
    session["contexto"]  = {
        "nome_agente":    resultado.get("contexto", {}).get("nome_agente", contexto.get("nome_agente")),
        "ultima_intencao":resultado.get("contexto", {}).get("ultima_intencao",""),
        "num_trocas":     resultado.get("contexto", {}).get("num_trocas", 0),
        "temas_visitados":resultado.get("contexto", {}).get("temas_visitados",[])[-5:],
        "revelado":       resultado.get("contexto", {}).get("revelado", False),
        "idioma":         resultado.get("contexto", {}).get("idioma","pt"),
    }
    session["stats"]     = stats
    session.modified     = True

    return jsonify(resultado)
