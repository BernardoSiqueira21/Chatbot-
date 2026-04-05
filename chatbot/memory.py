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
            vistos.append(tag)
    return vistos


def obter_num_interacoes(historico):
    return len(historico)


def detectar_tom_usuario(mensagem):
    msg_lower = mensagem.lower()

    palavras_frustracao = [
        "absurdo", "ridiculo", "ridículo", "indignado", "indignada", "nao aguento", "não aguento",
        "cansado", "cansada", "pessimo", "péssimo", "horrivel", "horrível", "nunca mais",
        "prejudicado", "prejudicada", "lesado", "lesada", "inacreditavel", "inacreditável",
        "um absurdo", "que vergonha", "nunca vi", "abuso", "revoltante", "revoltado",
        "revoltada", "que raiva", "to com raiva", "tô com raiva", "fui lesado", "fui lesada",
        "puta merda", "me lascaram", "me roubaram", "roubando", "ladrao", "ladrão",
        "me enganaram", "enganação", "enganacao", "me passaram para trás",
    ]

    palavras_urgencia = [
        "urgente", "urgencia", "urgência", "preciso ja", "preciso já", "hoje", "agora mesmo",
        "nao pode esperar", "não pode esperar", "correndo", "rapido", "rápido", "imediato",
        "preciso resolver hoje", "nao tenho tempo", "não tenho tempo", "emergência", "emergencia",
        "muito urgente", "prazo vencendo", "prazo acabando", "ta vencendo", "tá vencendo",
    ]

