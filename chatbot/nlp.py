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


def detectar_entidades(texto_normalizado):
    entidades = {}

    if any(w in texto_normalizado for w in ["internet", "online", "site", "aplicativo", "app", "e-commerce"]):
        entidades["canal_compra"] = "online"
    elif any(w in texto_normalizado for w in ["loja fisica", "loja física", "presencial", "pessoalmente"]):
        entidades["canal_compra"] = "fisica"

    if "produto" in texto_normalizado:
        entidades["objeto"] = "produto"
    elif any(w in texto_normalizado for w in ["servico", "serviço", "servicos", "serviços"]):
        entidades["objeto"] = "servico"

    if any(w in texto_normalizado for w in ["dias", "semanas", "meses", "horas"]):
        entidades["menciona_tempo"] = True

    return entidades


def identificar_intencao(texto):
    texto_normalizado = normalizar_texto(texto)
    tokens_usuario = preprocessar_texto(texto)
    stems_usuario = gerar_stems(tokens_usuario)

    if not tokens_usuario:
        return "desconhecida", 0, [], {}

    pontuacoes = {}
    correspondencias_map = {}

    for item in INTENTS_DB["intents"]:
        tag = item["tag"]
        palavras = [normalizar_texto(p) for p in item["patterns"]]
        stems_palavras = gerar_stems(palavras)

        pontuacao = 0.0
        correspondencias = []

        for token, stem in zip(tokens_usuario, stems_usuario):
            for palavra, stem_p in zip(palavras, stems_palavras):
                if " " in palavra and palavra in texto_normalizado:
                    pontuacao += 3.0
                    if palavra not in correspondencias:
                        correspondencias.append(palavra)
                elif token == palavra:
                    pontuacao += 1.5
                    if token not in correspondencias:
                        correspondencias.append(token)
                elif stem == stem_p and len(stem) > 3:
                    pontuacao += 0.8
                    if token not in correspondencias:
                        correspondencias.append(token)

        pontuacoes[tag] = pontuacao
        correspondencias_map[tag] = correspondencias

    melhor_intencao = max(pontuacoes, key=pontuacoes.get)
    melhor_pontuacao = pontuacoes[melhor_intencao]

    if melhor_pontuacao < 0.5:
        return "desconhecida", 0, [], detectar_entidades(texto_normalizado)

    return (
        melhor_intencao,
        round(melhor_pontuacao, 2),
        correspondencias_map[melhor_intencao],
        detectar_entidades(texto_normalizado)
    )