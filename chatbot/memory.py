"""
memory.py — Memória de contexto do caso
Extrai e persiste: empresa, produto, valor, data, canal, protocolo, tentativas, tom
"""
import re, unicodedata, datetime

def _norm(t):
    return "".join(c for c in unicodedata.normalize("NFD", t.lower())
                   if unicodedata.category(c) != "Mn")

_EMPRESAS_CONHECIDAS = [
    # Fabricantes / marcas (maior especificidade — listados primeiro)
    "samsung","lg","apple","iphone","ipad","macbook","sony","motorola","xiaomi","positivo",
    "renault","volkswagen","vw","fiat","chevrolet","gm","ford","honda","toyota","hyundai",
    "natura","avon","o boticario","nivea","unilever",
    "sul america","bradesco saude","unimed","amil","hapvida","notre dame","golden cross",
    # Bancos e fintechs
    "nubank","itau","bradesco","banco do brasil","bb","caixa","santander","inter",
    "c6","picpay","mercado pago","pagseguro","stone","cielo",
    # Operadoras
    "tim","claro","vivo","oi","nextel","net","sky","embratel","algar","sercomtel",
    "claro net","vivo fibra","tim fibra","claro tv",
    # Apps e plataformas
    "ifood","rappi","uber","uber eats","99","cabify","lalamove","loggi",
    # Varejistas (depois para não sobrepor fabricantes)
    "mercado livre","shopee","aliexpress","shein","amazon","ebay","wish","temu",
    "americanas","submarino","shoptime","magazine luiza","magalu","casas bahia",
    "carrefour","extra","pao de acucar","assai","atacadao",
    # Utilities e serviços
    "sabesp","copel","cemig","light","enel","energisa","coelba","celpe",
    "anatel","procon","anvisa","inss","receita federal","detran",
    # Seguradoras
    "porto seguro","tokio marine","allianz","liberty","mapfre","sura",
]

_CANAIS = {
    "online":    ["online","internet","site","app","aplicativo","celular","shopee",
                  "aliexpress","mercado livre","amazon","shein","temu","pelo app"],
    "loja_fisica":["loja","fisicamente","presencial","shopping","estabelecimento","loja fisica"],
    "telefone":  ["telefone","ligacao","telemarketing","0800","call center","por telefone"],
    "delivery":  ["delivery","entrega","ifood","rappi","por entrega"],
}

_MESES = {
    "janeiro":1,"fevereiro":2,"marco":3,"abril":4,"maio":5,"junho":6,
    "julho":7,"agosto":8,"setembro":9,"outubro":10,"novembro":11,"dezembro":12,
}

def _extrair_data_relativa(texto, hoje=None):
    """Extrai datas relativas: 'há 3 dias', 'semana passada', 'ontem', etc."""
    hoje = hoje or datetime.date.today()
    tn   = _norm(texto)

    # "há X dias/semanas/meses"
    m = re.search(r'ha\s+(\d+)\s+(dia|semana|mes|ano)', tn)
    if m:
        n, unidade = int(m.group(1)), m.group(2)
        delta = {"dia": n, "semana": n*7, "mes": n*30, "ano": n*365}.get(unidade, 0)
        data = hoje - datetime.timedelta(days=delta)
        return data.strftime("%d/%m/%Y")

    # "ontem"
    if "ontem" in tn:
        return (hoje - datetime.timedelta(days=1)).strftime("%d/%m/%Y")

    # "semana passada"
    if "semana passada" in tn:
        return (hoje - datetime.timedelta(days=7)).strftime("%d/%m/%Y")

    # "mes passado"
    if "mes passado" in tn or "mês passado" in tn:
        return (hoje - datetime.timedelta(days=30)).strftime("%d/%m/%Y")

    # "em fevereiro", "em janeiro de 2026" etc.
    for mes_nome, mes_num in _MESES.items():
        m = re.search(rf'\bem\s+{mes_nome}(?:\s+de\s+(\d{{4}}))?', tn)
        if m:
            ano = int(m.group(1)) if m.group(1) else hoje.year
            try:
                return datetime.date(ano, mes_num, 1).strftime("01/%m/%Y")
            except ValueError:
                pass

    return None

def detectar_entidades(texto):
    """Extrai entidades: empresa, produto, valor, data, canal, protocolo, tentativas."""
    tn   = _norm(texto)
    ents = {}

    # Empresa — termos compostos primeiro
    for emp in sorted(_EMPRESAS_CONHECIDAS, key=len, reverse=True):
        if emp in tn:
            ents["empresa"] = emp.title()
            break

    # Empresa genérica
    if "empresa" not in ents:
        m = re.search(r'\b(?:empresa|loja|marca|site|app|banco|operadora)\s+([A-Za-z][A-Za-zÀ-ú]{2,20})', texto)
        if m:
            ents["empresa"] = m.group(1).title()

    # Produto
    for p in ["celular","smartphone","notebook","laptop","geladeira","televisao","tv",
              "maquina de lavar","maquina","fogao","ar condicionado","tablet","smartwatch",
              "roupa","sapato","tenis","bolsa","medicamento","remedio","alimento",
              "produto","eletronico","veiculo","carro","moto","bicicleta"]:
        if p in tn:
            ents["objeto"] = p
            break

    # Valor monetário
    m = re.search(r'r\$\s*([\d.]+(?:,\d{1,2})?)', tn)
    if not m:
        m = re.search(r'([\d.]+(?:,\d{1,2})?)\s*(?:reais|real)', tn)
    if m:
        try:
            v = m.group(1).replace(".", "").replace(",", ".")
            val = float(v)
            ents["valor"] = f"R$ {val:,.2f}".replace(",","X").replace(".",",").replace("X",".")
        except Exception:
            pass

    # Data absoluta (DD/MM/AAAA ou DD/MM/AA)
    m = re.search(r'\b(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{2,4})\b', texto)
    if m:
        d, mo, a = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if a < 100: a += 2000
        try:
            ents["data_evento"] = datetime.date(a, mo, d).strftime("%d/%m/%Y")
        except ValueError:
            pass

    # Data relativa (se não achou absoluta)
    if "data_evento" not in ents:
        data_rel = _extrair_data_relativa(texto)
        if data_rel:
            ents["data_evento"] = data_rel

    # Canal
    for canal, termos in _CANAIS.items():
        if any(t in tn for t in termos):
            ents["canal"] = canal
            break

    # Protocolo / número de pedido / ordem de serviço
    for label, pattern in [
        ("protocolo",  r'\b(?:protocolo|prot\.?)\s*[:\-#]?\s*(\d{4,})\b'),
        ("pedido",     r'\b(?:pedido|order|ordem)\s*[:\-#]?\s*(\d{4,})\b'),
        ("os",         r'\b(?:os|o\.s\.?|ordem de servico)\s*[:\-#]?\s*(\d{4,})\b'),
    ]:
        m = re.search(pattern, tn)
        if m:
            ents[label] = m.group(1)
            break
    # Número isolado com contexto (ex: "número 98765")
    if "protocolo" not in ents and "pedido" not in ents:
        m = re.search(r'\b(?:numero|n[°º]|#)\s*(\d{4,})\b', tn)
        if m:
            ents["referencia"] = m.group(1)

    # Tentativas de contato
    m = re.search(r'\b(\d+)\s*(?:vezes?|tentativa|contato)', tn)
    if m:
        n = int(m.group(1))
        if n > 0:
            ents["tentativas"] = n

    return ents


    if oferta_pendente:
        novo_contexto["oferta_pendente"] = oferta_pendente
    else:
        novo_contexto["oferta_pendente"] = None

    # Rastreia se empresa já foi contactada
    sinais_contato = ["ja entrei", "já entrei", "liguei", "mandei email", "falei com",
                      "fui até", "reclamei", "protocolo", "ja reclamei", "já reclamei"]
    if any(s in mensagem.lower() for s in sinais_contato):
        novo_contexto["empresa_contactada"] = True

    # Rastreia se tem prova documental
    sinais_prova = ["tenho foto", "tenho print", "tenho nota", "guardei", "tenho comprovante",
                    "tenho protocolo", "tenho e-mail", "tenho email"]
    if any(s in mensagem.lower() for s in sinais_prova):
        novo_contexto["tem_provas"] = True

    return novo_contexto
