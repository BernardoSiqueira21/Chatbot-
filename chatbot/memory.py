import re


def obter_ultima_intencao(historico):
    if not historico:
        return None
    return historico[-1].get("intencao")


def obter_ultima_mensagem_usuario(historico):
    if not historico:
        return None
    return historico[-1].get("usuario")


def obter_ultimas_intencoes(historico, limite=5):
    return [item.get("intencao") for item in historico[-limite:]]


def contar_intencao_no_historico(historico, intencao):
    return sum(1 for item in historico if item.get("intencao") == intencao)


def obter_temas_visitados(historico):
    vistos = []
    for item in historico:
        tag = item.get("intencao")
        if tag and tag not in ("desconhecida", "saudacao", "despedida", "agradecimento") and tag not in vistos:
