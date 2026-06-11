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

