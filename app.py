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

