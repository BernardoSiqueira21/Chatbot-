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

    palavras_desespero = [
        "desesperado", "desesperada", "nao sei o que fazer", "não sei o que fazer",
        "estou perdido", "estou perdida", "sem saida", "sem saída", "nao tenho mais opcao",
        "não tenho mais opção", "precisando muito", "ja tentei tudo", "já tentei tudo",
    ]

    if any(p in msg_lower for p in palavras_desespero):
        return "desesperado"
    if any(p in msg_lower for p in palavras_frustracao):
        return "frustrado"
    if any(p in msg_lower for p in palavras_urgencia):
        return "urgente"
    return "neutro"


def extrair_entidades(mensagem):
    """Extrai entidades relevantes do texto para enriquecer o contexto."""
    texto = mensagem.lower()
    entidades = {}

    # Canal de compra
    if any(w in texto for w in ["internet", "online", "site", "aplicativo", "app", "e-commerce", "marketplace"]):
        entidades["canal_compra"] = "online"
    elif any(w in texto for w in ["loja fisica", "loja física", "presencial", "pessoalmente", "na loja"]):
        entidades["canal_compra"] = "fisica"

    # Objeto
    if "produto" in texto:
        entidades["objeto"] = "produto"
    elif any(w in texto for w in ["servico", "serviço", "servicos", "serviços"]):
        entidades["objeto"] = "servico"

