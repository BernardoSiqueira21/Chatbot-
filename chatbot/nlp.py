import json, os, re, string, unicodedata

BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
INTENTS_PATH  = os.path.join(BASE_DIR, "intents.json")
KB_PATH       = os.path.join(BASE_DIR, "knowledge_base.json")

STOPWORDS = {
    "de","a","o","que","e","do","da","em","um","para","com","uma","os","no",
    "se","na","por","mais","as","dos","como","mas","ao","ele","das","seu","sua",
    "ou","quando","muito","nos","ja","eu","tambem","so","pelo","pela","ate","isso",
    "ela","entre","depois","sem","mesmo","aos","seus","quem","nas","me","esse",
    "eles","voce","essa","nem","suas","meu","minha","pelos","elas","qual","nos",
    "lhe","deles","essas","esses","pelas","este","dele","tu","te","voces","vos",
    "lhes","meus","minhas","teu","tua","teus","tuas","nosso","nossa","nossos",
    "nossas","dela","delas","esta","estes","estas","aquele","aquela","aqueles",
    "aquelas","isto","aquilo","ha","foi","sao","era","tem","ter","ser","estar",
    "nao","sim","tao","tudo","nada","todo","toda","todos","todas","outro","outra",
    "outros","outras","ai","la","ca","ja","ate","sobre","sob","ante","apos",
    "atraves","mediante","conforme","segundo","durante","enquanto","portanto",
    "porem","contudo","todavia","entretanto","logo","assim","pois","porque",
    "embora","desde","ainda","agora","aqui","ali","bem","mal","pouco","menos",
    "demais","talvez","certamente","apenas","inclusive","alias","enfim",
    "quais","qual","meu","minha","meus","minhas","esse","essa",
}

SUFIXOS = [
    "amentos","imentos","amento","imento","acoes","acao","ções","ção",
    "adores","adoras","adora","adores","istas","ista","mente","issimo",
    "issima","izacao","izado","izados","izar","izando","dores","doras",
    "dor","dora","ores","oras","veis","vel","avel","ivel","oso","osa",
    "osos","osas","eiro","eira","eiros","eiras","inha","inho","inhas",
    "inhos","zinho","zinha","agem","agens","ada","ado","adas","ados",
    "idade","idades","ura","uras","ante","antes","ente","entes","encia",
    "ancias","al","ais","ar","er","ir",
    "aram","eram","iram","arem","erem","irem",
    "aria","eria","iria","asse","esse","isse",
    "ando","endo","indo","ndo",
    "arei","erei","irei","arao","erao","irao",
    "ava","ava","avam","avas",
    "ou","eu","iu",
    "os","as","es","a","o","e",
]

def _stem(palavra):
    if len(palavra) <= 4:
        return palavra
    for suf in sorted(SUFIXOS, key=len, reverse=True):
        if palavra.endswith(suf) and len(palavra) - len(suf) >= 3:
            return palavra[:-len(suf)]
    return palavra

def remover_acentos(t):
    return "".join(
        c for c in unicodedata.normalize("NFD", t)
        if unicodedata.category(c) != "Mn"
    )

def normalizar(t):
    return re.sub(r"\s+", " ", remover_acentos(t.lower().strip()))

def tokenizar(t):
    tokens = re.findall(r"\w+", normalizar(t))
    return [tk for tk in tokens
            if tk not in STOPWORDS and tk.isalnum() and len(tk) > 1]

def stemizar(tokens):
    return [_stem(tk) for tk in tokens]

def detectar_entidades(t):
    ent = {}
    tn = normalizar(t)
    if any(w in tn for w in ["internet","online","site","aplicativo","app","e-commerce","celular"]):
        ent["canal"] = "online"
    elif any(w in tn for w in ["loja fisica","presencial","pessoalmente"]):
        ent["canal"] = "fisica"
    if "produto" in tn:
        ent["objeto"] = "produto"
    elif any(w in tn for w in ["servico","servicos"]):
        ent["objeto"] = "servico"
    m = re.search(r"r\$\s*(\d[\d.,]*)", tn)
    if m:
        ent["valor"] = m.group(0)
    return ent

def _levenshtein(a, b):
    if abs(len(a) - len(b)) > 3:
        return 99
    la, lb = len(a), len(b)
    if la == 0: return lb
    if lb == 0: return la
    linha_ant = list(range(lb + 1))
    for i in range(1, la + 1):
        linha_atual = [i] + [0] * lb
        for j in range(1, lb + 1):
            custo = 0 if a[i-1] == b[j-1] else 1
            linha_atual[j] = min(
                linha_ant[j] + 1,
                linha_atual[j-1] + 1,
                linha_ant[j-1] + custo,
            )
        linha_ant = linha_atual
    return linha_ant[lb]

def _corrigir_token(token, vocabulario, max_dist=2):
    if token in vocabulario:
        return token
    if len(token) <= 3:
        return token
    # Distância máxima baseada no tamanho do token
    # Tokens curtos com erros graves precisam de distância maior
    if len(token) <= 4:
        dist_max = 1
    elif len(token) <= 6:
        dist_max = 2
    else:
        dist_max = 3
    dist_max = min(dist_max, max_dist)
    melhor, melhor_dist, melhor_len = token, dist_max + 1, 0
    for palavra in vocabulario:
        if abs(len(token) - len(palavra)) > dist_max:
            continue
        d = _levenshtein(token, palavra)
        # Prefere palavra mais longa em empate (evita "jeito" vs "defeito")
        if d < melhor_dist or (d == melhor_dist and len(palavra) > melhor_len):
            melhor_dist = d
            melhor = palavra
            melhor_len = len(palavra)
    return melhor if melhor_dist <= dist_max else token

def _carregar():
    with open(INTENTS_PATH, encoding="utf-8") as f:
        intents = json.load(f)
    with open(KB_PATH, encoding="utf-8") as f:
        kb = json.load(f)
    return intents, kb

INTENTS_DB, KNOWLEDGE_BASE = _carregar()

def _construir_vocabulario():
    vocab = set()
    for item in INTENTS_DB.get("intents", []):
        for p in item.get("patterns", []):
            for tk in tokenizar(p):
                vocab.add(tk)
    for art in KNOWLEDGE_BASE.get("artigos", {}).values():
        for kw in art.get("palavras_chave", []):
            for tk in tokenizar(kw):
                vocab.add(tk)
    for fl in KNOWLEDGE_BASE.get("fluxos_acao", {}).values():
        for kw in fl.get("palavras_chave", []):
            for tk in tokenizar(kw):
                vocab.add(tk)
    for org in KNOWLEDGE_BASE.get("orgaos_defesa", {}).values():
        for kw in org.get("palavras_chave", []):
            for tk in tokenizar(kw):
                vocab.add(tk)
    for dado in KNOWLEDGE_BASE.get("dados_atualizados", {}).values():
        for kw in dado.get("palavras_chave", []):
            for tk in tokenizar(kw):
                vocab.add(tk)
    return vocab

VOCABULARIO = _construir_vocabulario()

def corrigir_ortografia(tokens):
    return [_corrigir_token(tk, VOCABULARIO) for tk in tokens]

def _score_intencao(tnorm, tokens, stems, pats, spats):
    score = 0.0
    score_bigrama = 0.0  # Score de matches multi-token exatos — NÃO normalizado
    stems_set  = set(stems)
    tokens_set = set(tokens)
    for pt in pats:
        if " " in pt and pt in tnorm:
            score_bigrama += 4.0  # match multi-token exato — sinal muito forte
        elif pt in tokens_set:
            score += 1.5
        else:
            pt_tokens = pt.split()
            pt_stems  = stemizar(pt_tokens)
            if " " in pt:
                matches_exatos = sum(1 for t in pt_tokens if t in tokens_set and len(t) > 3)
                if matches_exatos >= 2:
                    score += 1.0
                    continue
            for stk in pt_stems:
                if stk in stems_set and len(stk) > 3:
                    score += 0.5
                    break
    # Normaliza só o score de stems (que sofre com intents grandes)
    # O score_bigrama de matches exatos multi-token é mantido — é sinal forte
    if pats and len(tokens) >= 2:
        import math
        score = score / math.sqrt(len(pats))
    return score + score_bigrama

def identificar_intencao(texto):
    tnorm  = normalizar(texto)
    tokens = tokenizar(texto)

    if not tokens:
        return "desconhecida", 0, [], {}

    tokens_corr = corrigir_ortografia(tokens)
    stems_orig  = stemizar(tokens)
    stems_corr  = stemizar(tokens_corr)

    entidades = detectar_entidades(tnorm)
    scores, corr_map = {}, {}

    for item in INTENTS_DB.get("intents", []):
        tag   = item["tag"]
        pats  = [normalizar(p) for p in item.get("patterns", [])]
        spats = stemizar(pats)

        sc_orig = _score_intencao(tnorm, tokens,      stems_corr, pats, spats)
        sc_corr = _score_intencao(tnorm, tokens_corr, stems_corr, pats, spats)
        score   = max(sc_orig, sc_corr)

        corr = []
        for tk, stk in zip(tokens_corr, stems_corr):
            for pt, spt in zip(pats, spats):
                if " " in pt and pt in tnorm:
                    if pt not in corr: corr.append(pt)
                elif tk == pt or stk == spt and len(stk) > 2:
                    if tk not in corr: corr.append(tk)

        scores[tag]   = score
        corr_map[tag] = corr

    best    = max(scores, key=scores.get)
    best_sc = scores[best]

    n_tokens = len(tokens)
    limiar = 0.4 if n_tokens <= 2 else 0.5

    if best_sc < limiar:
        return "desconhecida", 0, [], entidades

    return best, round(best_sc, 2), corr_map[best], entidades

def _score_kb(tnorm, tokens, stems, tokens_corr, stems_corr, palavras_chave):
    kws  = [normalizar(p) for p in palavras_chave]
    skws = stemizar(kws)
    sc   = 0.0
    for kw, skw in zip(kws, skws):
        if " " in kw and kw in tnorm:
            sc += 3.0
        elif kw in tokens or kw in tokens_corr:
            sc += 1.5
        elif (skw in stems or skw in stems_corr) and len(skw) > 2:
            sc += 0.8
    return sc / (len(kws) ** 0.5) if kws else 0.0

def buscar_kb(texto, limiar=0.35):
    tnorm       = normalizar(texto)
    tokens      = tokenizar(texto)
    stems       = stemizar(tokens)
    tokens_corr = corrigir_ortografia(tokens)
    stems_corr  = stemizar(tokens_corr)

    melhor_score, melhor = 0.0, None

    def avaliar(secao, items):
        nonlocal melhor_score, melhor
        for sid, item in items.items():
            sc = _score_kb(tnorm, tokens, stems, tokens_corr, stems_corr,
                           item.get("palavras_chave", []))
            if sc > melhor_score:
                melhor_score = sc
                melhor = (secao, sid, item, sc)

    avaliar("artigo",         KNOWLEDGE_BASE.get("artigos", {}))
    avaliar("fluxo",          KNOWLEDGE_BASE.get("fluxos_acao", {}))
    avaliar("orgao",          KNOWLEDGE_BASE.get("orgaos_defesa", {}))

    for sid, dado in KNOWLEDGE_BASE.get("dados_atualizados", {}).items():
        sc = _score_kb(tnorm, tokens, stems, tokens_corr, stems_corr,
                       dado.get("palavras_chave", [])) * 1.4
        if sc > melhor_score:
            melhor_score = sc
            melhor = ("dado_atualizado", sid, dado, sc)

    if melhor_score < limiar or melhor is None:
        return None

    secao, sid, item, sc = melhor

    if secao == "artigo":
        return {"tipo":"artigo","id":sid,"titulo":item["titulo"],
                "resumo":item.get("resumo",""),"texto":item.get("texto",""),
                "prazos":item.get("prazos",{}),"opcoes":item.get("opcoes",item.get("direitos",[])),
                "art_num":item["numero"],"score":sc}
    if secao == "fluxo":
        return {"tipo":"fluxo","id":sid,"titulo":item["titulo"],
                "passos":item.get("passos",[]),"score":sc}
    if secao == "orgao":
        return {"tipo":"orgao","id":sid,"titulo":item["nome"],
                "descricao":item.get("descricao",""),"como":item.get("como_acionar",""),
                "score":sc}
    return {"tipo":"dado_atualizado","id":sid,"titulo":item["titulo"],
            "resumo":item.get("conteudo",""),"texto":item.get("conteudo",""),
            "fonte":item.get("fonte",""),"vigencia":item.get("vigencia",""),
            "score":sc,"art_num":None,"prazos":{},"opcoes":[]}

def buscar_artigo_exato(numero_artigo):
    chave = f"art{numero_artigo}"
    art   = KNOWLEDGE_BASE.get("artigos", {}).get(chave)
    if not art:
        return None
    return {"tipo":"artigo","id":chave,"titulo":art["titulo"],
            "resumo":art.get("resumo",""),"texto":art.get("texto",""),
            "prazos":art.get("prazos",{}),"opcoes":art.get("opcoes",art.get("direitos",[])),
            "art_num":art["numero"],"score":1.0}
