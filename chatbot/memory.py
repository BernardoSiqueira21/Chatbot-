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

    # Menção de tempo
    match_tempo = re.search(r"(\d+)\s*(dia|dias|semana|semanas|mes|mês|meses|hora|horas)", texto)
    if match_tempo:
        entidades["tempo_mencionado"] = match_tempo.group(0)

    # Valor monetário
    match_valor = re.search(r"r\$\s?[\d.,]+|\d+\s*reais", texto, re.IGNORECASE)
    if match_valor:
        entidades["valor_mencionado"] = match_valor.group(0)

    # Tipo de produto específico
    produtos_duráveis = ["celular", "smartphone", "notebook", "computador", "televisão", "televisao",
                         "tv", "geladeira", "fogão", "fogao", "lavadora", "maquina de lavar",
                         "ar condicionado", "microondas", "tablet", "videogame"]
    if any(p in texto for p in produtos_duráveis):
        entidades["tipo_produto"] = "duravel"

    # Plataformas específicas
    if any(p in texto for p in ["mercado livre", "mercadolivre", "shopee", "amazon", "americanas",
                                  "magazine luiza", "magalu", "casas bahia", "submarino"]):
        entidades["marketplace"] = True

    return entidades


def atualizar_contexto(contexto_atual, intencao, mensagem, entidades=None, oferta_pendente=None):
    novo_contexto = dict(contexto_atual) if contexto_atual else {}

    novo_contexto["ultima_intencao"] = intencao
    novo_contexto["ultima_mensagem"] = mensagem

    if entidades:
        # Mescla entidades existentes com novas
        entidades_existentes = novo_contexto.get("entidades", {})
        entidades_existentes.update(entidades)
        novo_contexto["entidades"] = entidades_existentes

    if intencao != "desconhecida":
        novo_contexto["topico_principal"] = intencao

    temas_visitados = novo_contexto.get("temas_visitados", [])
    if intencao != "desconhecida" and intencao not in temas_visitados:
        temas_visitados.append(intencao)
    novo_contexto["temas_visitados"] = temas_visitados[-15:]

    num_trocas = novo_contexto.get("num_trocas", 0) + 1
    novo_contexto["num_trocas"] = num_trocas

    # Tom do usuário — mantém frustração/desespero por mais tempo
    tom = detectar_tom_usuario(mensagem)
    tom_anterior = novo_contexto.get("tom", "neutro")
    if tom != "neutro":
        novo_contexto["tom"] = tom
    elif tom_anterior in ("frustrado", "desesperado") and num_trocas < 4:
        # Mantém o tom negativo por algumas trocas
        pass
    else:
        novo_contexto["tom"] = "neutro"

    # Extrai valor monetário se não tiver ainda
    match_valor = re.search(r"R\$\s?[\d.,]+|\d+\s*reais", mensagem, re.IGNORECASE)
    if match_valor and "valor_mencionado" not in novo_contexto:
        novo_contexto["valor_mencionado"] = match_valor.group(0)

    # Extrai entidades adicionais da mensagem
    entidades_msg = extrair_entidades(mensagem)
    if entidades_msg:
        entidades_ctx = novo_contexto.get("entidades", {})
        entidades_ctx.update(entidades_msg)
        novo_contexto["entidades"] = entidades_ctx

    if oferta_pendente:
        novo_contexto["oferta_pendente"] = oferta_pendente
    else:
        novo_contexto["oferta_pendente"] = None

