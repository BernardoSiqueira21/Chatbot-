import json
import os
import re
import string
import unicodedata
import nltk

from nltk.corpus import stopwords
from nltk.stem import RSLPStemmer
from nltk.tokenize import RegexpTokenizer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INTENTS_PATH = os.path.join(BASE_DIR, "intents.json")

try:
    nltk.data.find("corpora/stopwords")
except Exception:
    nltk.download("stopwords", quiet=True)

try:
    nltk.data.find("stemmers/rslp")
except Exception:
    nltk.download("rslp", quiet=True)

STOPWORDS = set(stopwords.words("portuguese"))
STEMMER = RSLPStemmer()
TOKENIZER = RegexpTokenizer(r"\w+")


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


def preprocessar_texto(texto):
    texto = normalizar_texto(texto)

    try:
        tokens = TOKENIZER.tokenize(texto)
    except Exception:
        tokens = texto.split()

    tokens_limpos = []
    for token in tokens:
        if token in string.punctuation:
            continue
        if token in STOPWORDS:
            continue
        if not token.isalnum():
            continue
        tokens_limpos.append(token)

    return tokens_limpos


def gerar_stems(tokens):
    stems = []
    for token in tokens:
        try:
            stems.append(STEMMER.stem(token))
        except Exception:
            stems.append(token)
    return stems