"""
websearch.py — Busca web em tempo real
Escopo: APENAS dados úteis para o consumidor brasileiro (CDC e correlatos).
- Câmbio (relevante p/ compras internacionais e cobranças)
- Selic, IPCA, CDI (juros, financiamento, superendividamento)
- Salário mínimo, INSS, BPC (benefícios e cobranças)
- Tabela FIPE (veículos usados, CDC Art. 18/26)
- Recalls ANVISA/INMETRO (Art. 10 CDC)
- Tarifas reguladas (ANEEL energia, ANS planos)

FORA DE ESCOPO (não dispara busca):
clima, esportes, geopolítica, loteria, horóscopo, notícias gerais, entretenimento, IA, IT.
"""
import re, time, logging, unicodedata, datetime, os
import requests

logger    = logging.getLogger(__name__)
TIMEOUT   = 8
HOJE      = datetime.date.today()

def _norm(t):
    return "".join(c for c in unicodedata.normalize("NFD", t.lower())
                   if unicodedata.category(c) != "Mn")

# ── Moedas (compras internacionais, comparações de preço) ────────────────────
_MOEDAS_MAP = {
    # Pares com nome completo (verificados antes dos códigos curtos)
    "dolar americano":    ("USD-BRL","Dólar americano"),
    "dolar canadense":    ("CAD-BRL","Dólar canadense"),
    "dolar australiano":  ("AUD-BRL","Dólar australiano"),
    "franco suico":       ("CHF-BRL","Franco suíço"),
    "libra esterlina":    ("GBP-BRL","Libra esterlina"),
    "peso argentino":     ("ARS-BRL","Peso argentino"),
    "peso mexicano":      ("MXN-BRL","Peso mexicano"),
    "peso chileno":       ("CLP-BRL","Peso chileno"),
    # Termos simples
    "dolar":    ("USD-BRL","Dólar americano"),
    "dollar":   ("USD-BRL","Dólar americano"),
    "euro":     ("EUR-BRL","Euro"),
    "libra":    ("GBP-BRL","Libra esterlina"),
    "iene":     ("JPY-BRL","Iene japonês"),
    "yen":      ("JPY-BRL","Iene japonês"),
    "yuan":     ("CNY-BRL","Yuan chinês"),
    "renminbi": ("CNY-BRL","Yuan chinês"),
    "rublo":    ("RUB-BRL","Rublo russo"),
    # Códigos ISO (3 letras — exigem \b)
    "usd": ("USD-BRL","Dólar americano"),
    "eur": ("EUR-BRL","Euro"),
    "gbp": ("GBP-BRL","Libra esterlina"),
    "jpy": ("JPY-BRL","Iene japonês"),
    "cny": ("CNY-BRL","Yuan chinês"),
}

# ── Termos por categoria (TODOS relacionados ao consumidor) ──────────────────
_CAMBIO_GENERICO = [
    "cambio","cotacao","quanto vale","valor da moeda","conversao","conversor",
]
_FINANCEIRO = [
    # Juros e índices oficiais
    "selic","taxa selic","ipca","igpm","inpc","inflacao","inflação",
    "cdi","taxa cdi","rendimento poupanca","rendimento cdi",
    # Salários, benefícios e impostos
    "salario minimo","salário mínimo","piso salarial","inss","bpc","auxilio brasil",
    "bolsa familia","imposto renda","irpf","fgts saque","fgts aniversario",
    # Combustível e custo de vida (cobrança abusiva)
    "gasolina","combustivel","diesel","etanol","preço gasolina",
    # Tabela FIPE (veículos usados — CDC)
    "fipe","tabela fipe","preco fipe","valor fipe",
    # Tarifas reguladas
    "tarifa energia","aneel","bandeira tarifaria","conta de luz",
    "tarifa agua","conta agua",
]
_PALAVRAS_TEMPO = [
    "hoje","agora","atual","atualmente","este ano","esse ano","recente","ultimo",
    "2025","2026","2027","agora mesmo","no momento","esta semana","este mes",
    "ultimamente","acumulado","corrente","vigente",
]
_RECALL_ANVISA = [
    "recall","produto recolhido","retirada do mercado","anvisa recall",
    "alerta anvisa","recall carro","recall medicamento","recall alimento",
]

# ── BLOCKLIST — tudo o que NÃO é tema de consumidor ──────────────────────────
_OFF_SCOPE_BLOCKLIST = [
    # Entretenimento e jogos
    "horoscopo","signo","tarot","numerologia","mapa astral","oraculo",
    "loteria","mega sena","quina","lotofacil","loteria federal","jogo do bicho",
    "bolao","aposta esportiva",
    # Esportes
    "futebol","copa","mundial","olimpiada","campeonato","torneio","placar",
    "quem ganhou","time","jogador","artilheiro","libertadores","brasileirao",
    "nba","nfl","formula 1","f1","tenis","volei",
    # Clima e tempo meteorológico
    "clima","tempo em","temperatura","previsao tempo","vai chover","vai nevar",
    "umidade","tempestade","sensacao termica","graus celsius","fahrenheit",
    "previsao do tempo",
    # Datas e horas (puramente informativo)
    "que horas","fuso horario","hora em","hora atual","horas em","horas agora",
    "feriado","carnaval","natal data","pascoa","corpus christi","calendario",
    # Geopolítica e notícias gerais
    "guerra","conflito armado","tensao","tensão","geopolitica","sancao","embargo",
    "ucrania","russia","israel","gaza","hormuz","iran","china taiwan","coreia",
    "ultima hora","breaking news","noticias hoje","noticia geral","atualidade",
    # Educação e concursos
    "concurso publico","enem","vestibular","fuvest","unicamp","sisu","prouni",
    "fies","encceja","oab","tcc","monografia",
    # Comida e estilo de vida
    "receita de","como cozinhar","como fazer bolo","drink","cocktail","dieta",
    # Tecnologia geral (não consumidor)
    "chatgpt","gpt","ia generativa","google bard","gemini","claude ai","llm",
    "programar","codigo python","javascript","linguagem programacao",
    # Outras áreas legais
    "direito penal","direito de familia","divorcio","pensao alimenticia",
    "heranca","inventario","crime","prisao",
    # Commodities puras (não-consumo direto)
    "ouro preco","preço ouro","preco ouro","ouro hoje",
    "prata preco","preço prata","preco prata",
    "petroleo brent","petróleo brent","barril petroleo",
    "bitcoin","ethereum","cripto","cryptocurrency","blockchain","nft",
    # Música, cinema, cultura
    "musica","filme","novela","serie","cantor","ator","ingresso show",
    # Religião e política partidária
    "eleicao","presidente","deputado","partido","ideologia",
    "religiao","biblia","corao","oracao",
]

def esta_fora_do_escopo(mensagem):
    """Detecta se a mensagem é off-topic (fora do tema CDC/consumidor)."""
    mn = _norm(mensagem)
    return any(t in mn for t in _OFF_SCOPE_BLOCKLIST)

def _detectar_moedas(mn):
    """Detecta moedas — termos compostos primeiro, códigos curtos com \\b."""
    pares_vistos  = set()
    resultado     = []
    termos_usados = set()
    for termo in sorted(_MOEDAS_MAP.keys(), key=len, reverse=True):
        par, nome = _MOEDAS_MAP[termo]
        if par in pares_vistos: continue
        if len(termo) <= 4 and termo.isalpha():
            bate = bool(re.search(r'\b' + re.escape(termo) + r'\b', mn))
        else:
            bate = termo in mn
        if bate:
            partes = set(termo.split())
            if not partes.issubset(termos_usados):
                resultado.append((par, nome))
                pares_vistos.add(par)
                termos_usados.update(partes)
    return resultado

def precisa_busca_web(mensagem):
    """Dispara busca web SÓ para temas dentro do escopo do consumidor."""
    if esta_fora_do_escopo(mensagem):
        return False
    mn = _norm(mensagem)
    if _detectar_moedas(mn):                              return True
    if any(p in mn for p in _CAMBIO_GENERICO):            return True
    if any(p in mn for p in _RECALL_ANVISA):              return True
    # Termos que sempre disparam (mudam frequentemente e são consumidor-puro)
    sempre_disparam = [
        # Índices financeiros
        "selic","taxa selic","ipca","igpm","cdi","taxa cdi","inpc",
        # Veículos
        "fipe","tabela fipe","preco fipe","valor fipe","tabela fipe carro",
        # Energia
        "aneel","tarifa energia","bandeira tarifaria","conta de luz","conta luz",
        # Água
        "tarifa agua","conta agua","tarifa de agua","conta de agua",
        # Combustível
        "gasolina","diesel","etanol","combustivel","preço gasolina","preço diesel",
        # Salários e benefícios
        "salario minimo","salário mínimo","piso salarial",
        "inss valor","bpc valor","auxilio brasil valor","bolsa familia valor",
        # FGTS
        "fgts saque","fgts aniversario","saque aniversario fgts",
        # ANS
        "rol ans","reajuste plano saude","ans reajuste",
        # ANATEL
        "internet caiu","velocidade internet","brasilbandalarga",
        # Bancário
        "cheque especial juros","teto cheque especial","superendividamento",
    ]
    if any(t in mn for t in sempre_disparam):             return True
    # Demais financeiros precisam de palavra temporal
    tem_assunto = any(a in mn for a in _FINANCEIRO)
    tem_tempo   = any(p in mn for p in _PALAVRAS_TEMPO)
    if tem_assunto and tem_tempo:                         return True
    if tem_assunto and re.search(r'\b202[5-9]\b', mn):    return True
    return False

def _montar_query(mensagem):
    """Monta query otimizada com data atual — sempre mais recente primeiro."""
    mn   = _norm(mensagem)
    hoje = HOJE.strftime("%d/%m/%Y")
    ano  = HOJE.year

    pares = _detectar_moedas(mn)
    if pares:
        nomes = " e ".join(n for _, n in pares[:2])
        return f"cotação {nomes} real brasileiro hoje {hoje}"

    mapeamentos = [
        (_RECALL_ANVISA,            lambda: f"{mensagem} ANVISA recall {ano}"),
        (["selic","taxa selic"],    lambda: f"taxa Selic atual {ano} Banco Central"),
        (["ipca","inflacao"],       lambda: f"IPCA inflação Brasil {ano} acumulado IBGE"),
        (["cdi","rendimento"],      lambda: f"taxa CDI hoje {ano}"),
        (["salario minimo","piso"], lambda: f"salário mínimo Brasil {ano}"),
        (["inss","bpc"],            lambda: f"INSS valor benefício {ano}"),
        (["gasolina","combustivel"],lambda: f"preço gasolina Brasil hoje {ano}"),
        (["fipe","tabela fipe"],    lambda: f"tabela FIPE {mensagem} {ano}"),
        (["aneel","tarifa energia","bandeira tarifaria","conta de luz"],
                                    lambda: f"tarifa energia ANEEL bandeira {ano}"),
        (["tarifa agua","conta agua"], lambda: f"tarifa água {mensagem} {ano}"),
        (["fgts saque","saque aniversario fgts","fgts aniversario"],
                                    lambda: f"FGTS saque aniversário regras {ano}"),
        (["rol ans","reajuste plano","ans reajuste"],
                                    lambda: f"ANS rol procedimentos plano saúde {ano}"),
        (["cheque especial","teto cheque especial"],
                                    lambda: f"cheque especial teto juros Banco Central {ano}"),
        (["bpc","auxilio brasil","bolsa familia"],
                                    lambda: f"{mensagem} valor {ano} CadÚnico"),
        (["internet caiu","velocidade internet"],
                                    lambda: f"velocidade internet ANATEL Marco Civil {ano}"),
    ]
    for gatilhos, fn in mapeamentos:
        if any(g in mn for g in gatilhos):
            return fn()

    palavras = [w for w in mensagem.split() if len(w) > 3][:6]
    return " ".join(palavras) + f" Brasil consumidor {hoje}"

def buscar_dado_atual(mensagem):
    """Busca dado atual — câmbio via AwesomeAPI, resto via motores de busca."""
    mn     = _norm(mensagem)
    inicio = time.time()
    pares  = _detectar_moedas(mn)
    if pares:
        r = _buscar_cambio(pares, inicio)
        if r: return r
    query = _montar_query(mensagem)
    for fn in [_tentar_brave, _tentar_ddg_instant, _tentar_ddg_html]:
        r = fn(query, inicio)
        if r and r.get("sucesso"):
            r["data_busca"] = HOJE.isoformat()
            return r
    return {"sucesso": False, "erro": "sem resultado", "query": query}

def buscar_com_validacao(mensagem):
    """Busca com validação dupla + cache. Resultado sempre carimbado com data."""
    from chatbot.cache_dados import get_cache, set_cache, validar_duplo
    cached = get_cache(mensagem)
    if cached:
        cached["sucesso"] = True
        cached["origem"]  = "cache"
        return cached
    mn = _norm(mensagem); inicio = time.time()
    pares = _detectar_moedas(mn)
    r1 = r2 = None
    if pares:
        r1 = _buscar_cambio(pares, inicio)
        if r1:
            q2 = _montar_query(mensagem)
            r2 = _tentar_ddg_instant(q2, inicio) or _tentar_ddg_html(q2, inicio)
    else:
        query = _montar_query(mensagem)
        r1 = (_tentar_brave(query, inicio) or _tentar_ddg_instant(query, inicio)
               or _tentar_ddg_html(query, inicio))
        if r1:
            q2 = query + " atualizado"
            r2 = _tentar_ddg_instant(q2, inicio) or _tentar_ddg_html(q2, inicio)
    if not r1 or not r1.get("sucesso"):
        return {"sucesso": False, "erro": "sem resultado", "origem": "busca"}
    texto1, fonte1 = r1["texto"], r1.get("fonte","web")
    if r2 and r2.get("sucesso"):
        texto_final, fonte_final, confianca = validar_duplo(
            texto1, fonte1, r2["texto"], r2.get("fonte","web2"))
    else:
        texto_final, fonte_final, confianca = texto1, fonte1, "media"
    set_cache(mensagem, texto_final, fonte_final, confianca)
    return {
        "texto": texto_final, "fonte": fonte_final, "confianca": confianca,
        "sucesso": True, "origem": "busca_dupla",
        "tempo_ms": int((time.time()-inicio)*1000),
        "data_busca": HOJE.isoformat(),
    }

# ── Fontes ────────────────────────────────────────────────────────────────────
def _buscar_cambio(pares, inicio):
    simbolos = ",".join(p for p, _ in pares)
    try:
        r = requests.get(
            f"https://economia.awesomeapi.com.br/json/last/{simbolos}",
            timeout=TIMEOUT,
            headers={"User-Agent": "ConsumidorBot/1.0"},
        )
        if r.status_code == 200:
            data, linhas = r.json(), []
            for par, nome in pares:
                chave = par.replace("-","")
                if chave in data:
                    d   = data[chave]
                    bid = float(d.get("bid",0)); ask = float(d.get("ask",0))
                    var = float(d.get("pctChange",0)); hora = d.get("create_date","")[:16]
                    linhas.append(
                        f"{nome}: R$ {bid:.2f} (compra) / R$ {ask:.2f} (venda) "
                        f"variação {var:+.2f}% — {hora}"
                    )
                else:
                    linhas.append(f"{nome}: não disponível via API")
            if linhas:
                return {"texto": "\n".join(linhas),
                        "fonte": "AwesomeAPI / Banco Central",
                        "sucesso": True,
                        "tempo_ms": int((time.time()-inicio)*1000),
                        "data_busca": HOJE.isoformat()}
    except Exception as e:
        logger.warning(f"AwesomeAPI: {e}")
    return None

def _tentar_brave(query, inicio):
    token = os.environ.get("BRAVE_API_KEY","").strip()
    if not token: return None
    try:
        r = requests.get(
            "https://api.search.brave.com/res/v1/web/search",
            params={"q": query, "count": 3, "country": "br", "lang": "pt"},
            headers={"Accept":"application/json","Accept-Encoding":"gzip",
                     "X-Subscription-Token": token},
            timeout=TIMEOUT)
        if r.status_code == 200:
            results = r.json().get("web",{}).get("results",[])
            if results:
                desc = results[0].get("description","")
                if len(desc) > 30:
                    return {"texto": desc[:500], "fonte": "Brave Search",
                            "sucesso": True,
                            "tempo_ms": int((time.time()-inicio)*1000)}
    except Exception as e:
        logger.warning(f"Brave: {e}")
    return None

def _tentar_ddg_instant(query, inicio):
    try:
        r = requests.get("https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"},
            headers={"User-Agent": "ConsumidorBot/1.0"}, timeout=TIMEOUT)
        if r.status_code == 200:
            data  = r.json()
            texto = (data.get("AbstractText") or data.get("Answer") or
                     data.get("Definition") or "")
            if len(texto) > 30:
                return {"texto": texto[:500],
                        "fonte": data.get("AbstractSource","DuckDuckGo"),
                        "sucesso": True,
                        "tempo_ms": int((time.time()-inicio)*1000)}
    except Exception as e:
        logger.warning(f"DDG instant: {e}")
    return None

def _tentar_ddg_html(query, inicio):
    try:
        r = requests.get("https://html.duckduckgo.com/html/", params={"q": query},
            headers={"User-Agent": "Mozilla/5.0 (compatible; ConsumidorBot/1.0)",
                     "Accept-Language": "pt-BR,pt;q=0.9"}, timeout=TIMEOUT)
        if r.status_code != 200: return None
        snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', r.text, re.DOTALL)
        if not snippets: return None
        texto = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', snippets[0])).strip()
        if len(texto) > 30:
            return {"texto": texto[:400], "fonte": "DuckDuckGo",
                    "sucesso": True,
                    "tempo_ms": int((time.time()-inicio)*1000)}
    except Exception as e:
        logger.warning(f"DDG html: {e}")
    return None
