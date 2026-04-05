import json
import os
import re
import unicodedata
import nltk

from nltk.corpus import stopwords

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INTENTS_PATH = os.path.join(BASE_DIR, "intents.json")

try:
    nltk.data.find("corpora/stopwords")
except Exception:
    nltk.download("stopwords", quiet=True)


STOPWORDS = set(stopwords.words("portuguese"))


def carregar_intents():
    with open(INTENTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


INTENTS_DB = carregar_intents()


def remover_acentos(texto):
    return "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )


def normalizar_texto(texto):
    texto = texto.lower().strip()
    texto = remover_acentos(texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto