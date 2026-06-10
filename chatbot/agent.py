"""
agent.py — Agente Híbrido v13
Roteamento flexível com tratamento de erros robusto.
Prompts reforçados para que o LLM NUNCA contradiga a KB.
"""
import random, logging, re, time, datetime
from chatbot.nlp               import (identificar_intencao, buscar_kb, buscar_artigo_exato,
                                        INTENTS_DB, normalizar)
from chatbot.llm               import consultar_llm, llm_disponivel
from chatbot.memory            import obter_ultima_intencao, atualizar_contexto, resumo_caso
from chatbot.websearch         import precisa_busca_web, buscar_dado_atual, buscar_com_validacao
from chatbot.gerador_reclamacao import montar_prompt_reclamacao
from chatbot.calculadora_prazos import montar_prompt_prazos, formatar_prazos_para_llm

logger = logging.getLogger(__name__)
LIMIAR_KB = 0.65

FOLLOWUP = {
    "garantia":             "O defeito apareceu logo após a compra ou depois de algum tempo?",
    "troca":                "A empresa já deu algum prazo ou protocolo?",
    "arrependimento":       "Você ainda está dentro dos 7 dias do recebimento?",
    "atraso_entrega":       "Qual foi o prazo prometido e quantos dias já passaram?",
    "produto_nao_entregue": "Você já tentou contato com a empresa?",
    "cobranca_indevida":    "A cobrança apareceu no cartão, débito ou boleto?",
    "reembolso":            "Quanto tempo faz que você solicitou o reembolso?",
    "cancelamento":         "A empresa está cobrando multa por cancelamento?",
    "empresa_negou_solucao":"A empresa deu a negativa por escrito?",
    "procon":               "Você já tentou resolver diretamente com a empresa?",
    "compra_online":        "A compra foi em marketplace ou no site da marca?",
    "saude_plano":          "A negativa foi por escrito? Qual procedimento foi negado?",
    "servico_com_problema": "O serviço foi feito por empresa ou profissional autônomo?",
    "voo_transporte":       "O voo foi cancelado pela companhia ou você que cancelou?",
    "garantia_estendida":   "O produto ainda está na garantia legal de 90 dias do CDC?",
    "assistencia_tecnica":  "Já se passaram 30 dias desde a entrega para conserto?",
    "produto_falsificado":  "Você tem nota fiscal e/ou comprovante da compra?",
    "dano_moral":           "Você tem documentação do constrangimento ou prejuízo?",
    "recall":               "Qual produto/empresa fez o recall? Você já foi atendido?",
    "juizado_virtual":      "Qual estado você está? O sistema varia por tribunal.",
    "ecommerce":            "Em qual site/plataforma foi a compra?",
    "lgpd":                 "Você quer acessar, corrigir ou excluir seus dados?",
    "consignado":           "Você autorizou o desconto ou foi sem seu consentimento?",
    "seguro":               "Qual tipo de seguro — auto, vida, residencial?",
    "trabalho":             "Você ainda está empregado ou já foi dispensado?",
    "nota_fiscal":          "O estabelecimento se recusou a emitir ou você quer informações?",
    "importacao":           "O produto está retido na alfândega ou ainda vai chegar?",
    "medicamento":          "É sobre troca por genérico, preço, recall ou outra situação?",
    "financiamento":        "É financiamento de carro, imóvel ou outro tipo?",
    "streaming":            "Qual plataforma — Netflix, Spotify, Globoplay, Disney+?",
    "veiculo_usado":        "Você comprou de loja, particular ou concessionária?",
    "locacao":              "Você é locatário (inquilino) ou proprietário?",
    "idoso":                "A pessoa tem 60+ anos? O CDC e o Estatuto do Idoso se aplicam.",
    "ead_curso":            "É curso EAD, presencial ou semipresencial?",
    "academia":             "Você quer cancelar a mensalidade ou contestar cobrança?",
    "banco_digital":        "Qual banco — Nubank, Inter, C6, PicPay ou outro?",
    "loja_fisica":          "Você ainda está na loja ou já foi embora?",
    "tempo_prazo":          "Qual a data de compra ou recebimento do produto?",
    "assinatura_plano":     "Você quer cancelar, contestar cobrança ou outro?",
    "frete_entrega":        "O produto não chegou ou veio com problema?",
    "consumidor_gov":       "Você já abriu reclamação no consumidor.gov.br?",
    "contrato_cláusula_abusiva":"Qual cláusula te parece abusiva no contrato?",
    "aneel_energia":      "Qual sua companhia — Cemig, Enel, Light? Já reclamou para ela?",
    "saneamento_agua":    "É Sabesp, Cedae, Copasa? O problema é cobrança, falta ou vazamento?",
    "internet_provedor":  "Você tem o teste de velocidade em brasilbandalarga.com.br?",
    "compra_redes_sociais":"Você tem prints da conversa e do anúncio?",
    "pix_golpes":         "Você fez o Pix há quanto tempo? Já acionou o banco?",
    "phishing_golpes":    "Você já trocou as senhas e notificou o banco?",
    "voo_aviacao":        "Qual companhia aérea e quanto tempo de atraso?",
    "apps_mobilidade":    "Qual aplicativo — Uber, 99, iFood, Rappi?",
    "transporte_onibus":  "Qual viação? Você tem o bilhete?",
    "imovel_construtora": "Qual construtora e quanto tempo de atraso?",
    "condominio":         "É cobrança alta, multa por infração ou problema com obras?",
    "medico_clinica":     "É erro médico, procedimento estético ou cobrança?",
    "home_care_idoso":    "É o plano que negou home care ou problema em casa de repouso?",
    "escola_anuidade":    "Qual o problema — reajuste, transferência, material ou matrícula?",
    "pcd_direitos":       "É acessibilidade, isenção fiscal ou atendimento prioritário?",
    "publicidade_infantil":"Qual marca/produto e onde a propaganda apareceu?",
    "funeraria":          "É funerária (serviço pontual) ou plano funerário (mensal)?",
    "cheque_especial":    "Você quer revisar juros ou negociar dívida acumulada?",
    "vale_alimentacao":   "Qual operadora — Alelo, Sodexo, Ticket, VR?",
    "eventos_show":       "Foi cancelado em definitivo ou apenas adiado?",
    "venda_casada":       "O que estão te obrigando a comprar junto?",
    "contrato_adesao":    "É contrato de banco, plano de saúde, financeira ou outro?",
}

ROTULOS = {
    "garantia":"garantia e defeito","troca":"troca do produto","arrependimento":"arrependimento",
    "atraso_entrega":"atraso na entrega","produto_nao_entregue":"produto não entregue",
    "cobranca_indevida":"cobrança indevida","reembolso":"reembolso","cancelamento":"cancelamento",
    "sac":"atendimento e protocolo","procon":"Procon e órgãos","empresa_negou_solucao":"empresa negou",
    "prova_documental":"provas e documentos","compra_online":"compra online",
    "juizado_especial":"Juizado Especial","direito_basico":"direitos do consumidor",
    "propaganda_enganosa":"propaganda enganosa","servico_com_problema":"serviço com problema",
    "saude_plano":"plano de saúde","voo_transporte":"voos/transporte",
    "cartao_credito":"cartão de crédito","nota_fiscal":"nota fiscal",
    "pix_transferencia":"Pix",
    "garantia_estendida":"garantia estendida","assistencia_tecnica":"assistência técnica",
    "produto_falsificado":"produto falsificado","dano_moral":"dano moral",
    "recall":"recall","juizado_virtual":"juizado virtual",
    "ecommerce":"e-commerce","lgpd":"LGPD/dados pessoais",
    "consignado":"empréstimo consignado","seguro":"seguros",
    "trabalho":"direitos trabalhistas","nota_fiscal":"nota fiscal",
    "importacao":"importação","medicamento":"medicamentos",
    "financiamento":"financiamento","streaming":"streaming",
    "veiculo_usado":"veículo usado","locacao":"locação/aluguel",
    "idoso":"direitos do idoso","ead_curso":"curso EAD",
    "academia":"academia","banco_digital":"banco digital",
    "loja_fisica":"loja física","tempo_prazo":"prazo/tempo",
    "assinatura_plano":"assinatura","frete_entrega":"frete/entrega",
    "consumidor_gov":"consumidor.gov.br","contrato_cláusula_abusiva":"cláusula abusiva",
    "aneel_energia":"conta de luz","saneamento_agua":"conta de água",
    "internet_provedor":"internet/banda larga","compra_redes_sociais":"compras em redes sociais",
    "pix_golpes":"golpes Pix","phishing_golpes":"golpes online/phishing",
    "voo_aviacao":"voos/companhias aéreas","apps_mobilidade":"Uber/99/iFood",
    "transporte_onibus":"ônibus interestadual","imovel_construtora":"imóvel na planta",
    "condominio":"condomínio","medico_clinica":"erro médico/clínica estética",
    "home_care_idoso":"home care/casa de repouso","escola_anuidade":"escola particular",
    "pcd_direitos":"direitos PCD","publicidade_infantil":"publicidade a crianças",
    "funeraria":"funerária","cheque_especial":"cheque especial",
    "vale_alimentacao":"VR/VA","eventos_show":"eventos cancelados",
    "venda_casada":"venda casada","contrato_adesao":"contrato de adesão",
}

RELACIONADOS = {
    "garantia":              ["troca","empresa_negou_solucao","procon"],
    "troca":                 ["garantia","reembolso","empresa_negou_solucao"],
    "arrependimento":        ["reembolso","cancelamento","compra_online"],
    "atraso_entrega":        ["produto_nao_entregue","cancelamento","reembolso"],
    "cobranca_indevida":     ["reembolso","cancelamento","empresa_negou_solucao"],
    "empresa_negou_solucao": ["procon","juizado_especial","prova_documental"],
    "compra_online":         ["arrependimento","atraso_entrega","produto_nao_entregue"],
    "cancelamento":          ["reembolso","empresa_negou_solucao","procon"],
    "garantia_estendida":    ["garantia","assistencia_tecnica","empresa_negou_solucao"],
    "assistencia_tecnica":   ["garantia","empresa_negou_solucao","reembolso"],
    "produto_falsificado":   ["empresa_negou_solucao","procon","prova_documental"],
    "dano_moral":            ["empresa_negou_solucao","juizado_virtual","procon"],
    "recall":                ["garantia","empresa_negou_solucao","procon"],
    "juizado_virtual":       ["empresa_negou_solucao","prova_documental","procon"],
    "ecommerce":             ["arrependimento","atraso_entrega","produto_nao_entregue"],
    "lgpd":                  ["empresa_negou_solucao","procon","juizado_virtual"],
    "consignado":            ["cobranca_indevida","empresa_negou_solucao","procon"],
    "seguro":                ["empresa_negou_solucao","procon","juizado_virtual"],
    "nota_fiscal":           ["garantia","cobranca_indevida","procon"],
    "streaming":             ["cancelamento","cobranca_indevida","arrependimento"],
    "banco_digital":         ["cobranca_indevida","cancelamento","procon"],
}

def _classificar_primeira_msg(mensagem):
    """
    Classifica se a primeira mensagem é:
    - 'saudacao': mensagem sem conteúdo ("oi", "olá") → apresenta-se
    - 'direta': pergunta ou assunto → responde direto
    """
    m   = mensagem.lower().strip()
    mn  = "".join(c for c in __import__('unicodedata').normalize("NFD", m)
                  if __import__('unicodedata').category(c) != "Mn")

    saudacoes_puras = {
        "oi","ola","olá","bom dia","boa tarde","boa noite","hello","hi","hey",
        "eai","e ai","tudo bem","tudo bom","oi!","olá!","bom dia!","boa tarde!",
    }
    if m in saudacoes_puras:
        return "saudacao"

    indicadores_diretos = [
        r'\bartigo\b', r'\bart\b', r'\d{2,}',
        r'\bdefeito\b', r'\bgarantia\b', r'\bcdc\b',
        r'\bprocon\b', r'\bjuros\b', r'\bdolar\b',
        r'\bplano\b', r'\bsaude\b', r'\bseguros?\b',
        r'\bprazo\b', r'\bdireito\b', r'\bcancelamento\b',
        r'\bcobrança\b', r'\bcobranca\b', r'\breembolso\b',
        r'\bmercado\b', r'\bclima\b', r'\btemperatura\b',
        r'\bhoras?\b', r'\bouro\b', r'\bpetroleo\b',
    ]
    import re as _re
    if any(_re.search(p, mn) for p in indicadores_diretos):
        return "direta"

    if len(m.split()) > 2:
        return "direta"

    return "saudacao"

def _instrucao_saudacao(mensagem, primeira_mensagem):
    """
    Retorna instrução de saudação apenas quando realmente faz sentido.
    - primeira_mensagem=False → sem instrução
    - primeira_mensagem=True + saudacao pura → apresenta-se e convida
    - primeira_mensagem=True + pergunta direta → responde direto, menciona nome só no fim se necessário
    """
    if not primeira_mensagem:
        return ""

    tipo = _classificar_primeira_msg(mensagem)

    if tipo == "saudacao":
        return (
            "GREETING ONLY MESSAGE: The user just said hello. "
            "Introduce yourself warmly by name in ONE sentence, then invite them to share their situation. "
            "Do NOT answer any question yet — just greet and invite.\n\n"
        )
    else:
        return (
            "FIRST INTERACTION: Answer the question directly and naturally. "
            "You may briefly mention your name at the end if it flows naturally, "
            "but do NOT start with a greeting — go straight to the answer.\n\n"
        )

def _prompt_kb(conteudo_kb, followup="", primeira_mensagem=False, mensagem="", kb_score=1.0):
    intro = _instrucao_saudacao(mensagem, primeira_mensagem)
    aviso_match_parcial = ""
    if 0.65 <= kb_score < 1.0:
        aviso_match_parcial = (
            "⚠️ ATTENTION: The KB content below has only a PARTIAL match with the user's question "
            f"(relevance score: {kb_score:.2f}/2.0). The content may be related but might NOT "
            "directly answer what was asked. If the user's specific question is NOT clearly "
            "addressed by the content below:\n"
            "1. Be transparent: 'Sobre esse ponto específico, não tenho uma informação direta.'\n"
            "2. Share ONLY what IS clearly in the content (do not extrapolate).\n"
            "3. Suggest reliable sources for the specific question.\n"
            "4. Do NOT pretend the content fully answers when it doesn't.\n\n"
        )
    return (
        f"{intro}"
        f"{aviso_match_parcial}"
        "CRITICAL INSTRUCTION — VERIFIED DATABASE CONTENT BELOW:\n"
        "You MUST use ONLY the information provided below to answer.\n"
        "DO NOT use your training memory for any specific numbers, percentages, "
        "dates or legal values — they may be outdated.\n"
        "The content below is the authoritative, current source.\n\n"
        "IF THE USER'S QUESTION IS NOT FULLY COVERED by the content below:\n"
        "• Answer ONLY what IS covered, do NOT make up the rest.\n"
        "• Acknowledge clearly: 'Sobre esse ponto específico, não tenho informação detalhada na minha base.'\n"
        "• Suggest where to find it: Procon, consumidor.gov.br, advogado, órgão regulador.\n"
        "• NEVER invent article numbers, fines, percentages, deadlines, jurisprudence or court decisions.\n\n"
        "Respond naturally and warmly in the user's language.\n"
        "Give the essential answer first — do NOT list everything at once. "
        "Then ask ONE targeted question to understand the situation better "
        "before offering more details.\n\n"
        f"=== VERIFIED CONTENT (USE THIS EXACTLY) ===\n{conteudo_kb}\n"
        + (f"\n=== SUGGESTED FOLLOW-UP QUESTION ===\n{followup}" if followup else "")
    )

def _prompt_web(dado_web, primeira_mensagem=False, mensagem=""):
    intro     = _instrucao_saudacao(mensagem, primeira_mensagem)
    origem    = dado_web.get("origem","busca")
    confianca = dado_web.get("confianca","media")
    cache_hit = origem == "cache"
    idade     = dado_web.get("idade_horas")
    nota_origem = ""
    if cache_hit and idade:
        nota_origem = f"(cached {idade}h ago, still valid)"
    elif confianca == "alta":
        nota_origem = "(validated by 2 independent sources — high confidence)"
    elif confianca == "media":
        nota_origem = "(single source — use with normal confidence)"
    return (
        f"{intro}"
        f"REAL-TIME DATA {nota_origem}:\n"
        f"{dado_web['texto']}\n"
        f"Source: {dado_web.get('fonte','')}\n"
        f"Date: {dado_web.get('data_busca','today')}\n\n"
        "Use this data to answer. Mention the source naturally."
    )

def _prompt_kb_web(conteudo_kb, dado_web, followup="", primeira_mensagem=False, mensagem=""):
    intro = _instrucao_saudacao(mensagem, primeira_mensagem)
    return (
        f"{intro}"
        "CRITICAL INSTRUCTION — TWO VERIFIED SOURCES BELOW:\n"
        "Use BOTH sources to answer all parts of the user's question.\n"
        "Do NOT use your training memory for specific numbers or dates.\n\n"
        f"=== SOURCE 1: VERIFIED CDC LAW DATABASE ===\n{conteudo_kb}\n\n"
        f"=== SOURCE 2: REAL-TIME DATA (fetched now) ===\n"
        f"{dado_web['texto']}\nSource: {dado_web.get('fonte','')}\n"
        + (f"\n=== SUGGESTED FOLLOW-UP ===\n{followup}" if followup else "")
    )

def _prompt_livre(primeira_mensagem=False, mensagem=""):
    intro = _instrucao_saudacao(mensagem, primeira_mensagem)
    anti_alucinacao = (
        "ANTI-HALLUCINATION INSTRUCTION (CRITICAL):\n"
        "You do NOT have specific verified data for this question in your knowledge base.\n"
        "Rules to follow:\n"
        "• NEVER invent specific article numbers, deadlines, fines, percentages, court "
        "  decisions, jurisprudence numbers, or dates. If you're not 100% sure, say so.\n"
        "• If the user asks about a specific case, court ruling, fine value, or recent "
        "  legislation that you don't know with certainty, acknowledge the limitation:\n"
        "  Example: 'Não tenho na minha base uma informação específica sobre isso. "
        "  O ideal é consultar um advogado ou o Procon do seu estado para um caso assim.'\n"
        "• Stick to GENERAL CDC principles you know well — definitions, the existence "
        "  of articles, general rights. Avoid making up specifics.\n"
        "• ALWAYS suggest reliable sources: Procon, consumidor.gov.br, advogado, "
        "  bcb.gov.br, ans.gov.br, anatel.gov.br — depending on the topic.\n"
        "• If user asks something tangentially related to CDC but you have no specific "
        "  data, redirect to where they CAN find it.\n\n"
    )
    base = anti_alucinacao + (intro or "")
    return base if base else None

def _detectar_loop(mensagem, historico):
    if len(historico) < 3:
        return False
    mn = mensagem.lower().strip()
    ultimas = [h.get("usuario","").lower().strip() for h in historico[-4:]]
    if sum(1 for u in ultimas if u == mn) >= 3:
        return True
    if len(mn.split()) <= 2:
        if sum(1 for h in historico[-6:] if len(h.get("usuario","").split()) <= 2) >= 5:
            return True
    palavras = mn.split()
    if len(set(palavras)) == 1:
        if sum(1 for h in historico[-6:]
               if palavras[0] in h.get("usuario","").lower().split()) >= 4:
            return True
    return False

def _validar_relevancia_kb(mensagem, resultado_kb, kb_score):
    """
    Anti-alucinação: verifica se a KB recuperada realmente cobre a pergunta.
    Score entre 0.65-0.80 com palavras-chave distintas da KB = match parcial fraco.
    Retorna True se a KB cobre bem, False se o match é superficial.
    """
    if not resultado_kb or kb_score < 0.65:
        return False
    if kb_score >= 1.0:
        return True

    import re as _re
    mn = mensagem.lower()
    pedidos_dados_especificos = [
        r'\bquem\s+(criou|inventou|escreveu)\b',
        r'\bquanto\s+(custa|cobra|cobram|paga)\b',
        r'\bqual\s+a?\s*(multa|pena|sanção|sancao|punição)\b',
        r'\bqual\s+a?\s*idade\b',
        r'\bqual\s+(ministerio|ministério|orgao|órgão)\b',
        r'\bem\s+que\s+ano\b',
        r'\bonde\s+fica\b',
        r'\bquantos?\s+(artigos|capitulos|capítulos)\b',
        r'\bse\s+aplica\s+a\s+(igreja|partido|ong|sindicato)\b',
    ]
    for padrao in pedidos_dados_especificos:
        if _re.search(padrao, mn):
            conteudo = (resultado_kb.get('texto','') + ' ' +
                        resultado_kb.get('resumo','')).lower()
            palavras_pergunta = [w for w in mn.split()
                                 if len(w) > 4 and w not in
                                 ('cdc','codigo','consumidor','quem','quanto','qual','como','onde')]
            matches = sum(1 for p in palavras_pergunta if p in conteudo)
            if matches < 2:  
                return False
    return True

def _determinar_rota(mensagem, resultado_kb, kb_score, artigo_explicito, dado_web, intencao):
    if artigo_explicito is not None:
        tem_kb = True
    else:
        tem_kb = kb_score >= LIMIAR_KB and _validar_relevancia_kb(mensagem, resultado_kb, kb_score)

    tem_web      = dado_web is not None and dado_web.get("sucesso")
    precisa_web  = precisa_busca_web(mensagem)

    try:
        from chatbot.websearch import esta_fora_do_escopo, detectar_pressao_emocional
        fora = esta_fora_do_escopo(mensagem)
        if fora and detectar_pressao_emocional(mensagem) and not tem_kb:
            return "off_scope"
        if fora and not tem_kb and not tem_web:
            return "off_scope"
    except Exception:
        pass

    if tem_kb and tem_web:   return "kb_web_llm"
    if tem_kb:               return "kb_pura"
    if precisa_web:          return "llm_web"
    return "llm_livre"

def processar_mensagem(mensagem, historico, contexto):
    try:
        mensagem = str(mensagem or "").strip()[:800]
    except Exception:
        mensagem = ""

    if not mensagem:
        return _vazio(contexto)

    try:
        historico = [h for h in (historico if isinstance(historico, list) else [])
                     if isinstance(h, dict)]
    except Exception:
        historico = []

    try:
        contexto = contexto if isinstance(contexto, dict) else {}
    except Exception:
        contexto = {}

    nome_agente = contexto.get("nome_agente") or "Marina"
    revelar     = _perguntou_se_e_bot(mensagem) or contexto.get("revelado", False)
    if revelar:
        contexto["revelado"] = True

    try:
        é_reclamacao, prompt_reclamacao = montar_prompt_reclamacao(contexto, historico, mensagem)
        if é_reclamacao and prompt_reclamacao:
            r_rec = consultar_llm(mensagem, contexto_kb=prompt_reclamacao,
                                   historico=[], nome=nome_agente, revelar=revelar)
            if r_rec.get("sucesso") and r_rec.get("resposta"):
                novo_ctx = _atualizar_ctx(contexto, "reclamacao_formal", mensagem, {}, nome_agente, revelar)
                return _resultado(mensagem, "reclamacao_formal",
                                   r_rec["resposta"], "gerador_reclamacao",
                                   0.0, None, True, r_rec.get("tempo_ms"), False,
                                   novo_ctx, [])
    except Exception as e:
        logger.warning(f"Gerador reclamação: {e}")

    try:
        é_prazo, data_encontrada, resultado_prazo = montar_prompt_prazos(
            contexto, historico, mensagem)
        if é_prazo:
            if resultado_prazo:
                tabela = formatar_prazos_para_llm(resultado_prazo, contexto)
                prompt_prazos = (
                    f"O usuário perguntou sobre prazos. Use a tabela abaixo para responder "
                    f"de forma clara e em linguagem natural. Destaque os prazos urgentes ou vencidos.\n\n"
                    f"{tabela}\n\n"
                    f"Responda no idioma do usuário com tom conversacional."
                )
                r_pz = consultar_llm(mensagem, contexto_kb=prompt_prazos,
                                      historico=historico[-3:], nome=nome_agente, revelar=revelar)
                resp_prazos = r_pz.get("resposta") if r_pz.get("sucesso") else tabela
            else:
                resp_prazos = (
                    "Para calcular seus prazos preciso saber a data da compra ou do recebimento. "
                    "Me informa a data (ex: 10/05/2026) que calculo tudo para você!"
                )
            novo_ctx = _atualizar_ctx(contexto, "calculo_prazo", mensagem, {}, nome_agente, revelar)
            return _resultado(mensagem, "calculo_prazo", resp_prazos, "calculadora_prazos",
                               0.0, None, resultado_prazo is not None,
                               None, False, novo_ctx, [])
    except Exception as e:
        logger.warning(f"Calculadora prazos: {e}")

    eh_primeira_mensagem = len(historico) == 0

    try:
        if _detectar_loop(mensagem, historico):
            r_loop = consultar_llm(
                mensagem,
                contexto_kb=(
                    "The user has been sending the same or very short messages repeatedly. "
                    "Gently break the loop: ask them warmly to describe their actual situation "
                    "from scratch. Respond in the user's language."
                ),
                historico=historico[-4:],
                nome=nome_agente,
                revelar=revelar,
            )
            resp = (r_loop.get("resposta")
                    or "Parece que estamos em loop! Me conta o que está acontecendo de verdade.")
            novo_ctx = _atualizar_ctx(contexto, "desconhecida", mensagem, {}, nome_agente, revelar)
            return _resultado(mensagem, "loop", resp, "anti_loop", 0.0,
                              None, True, r_loop.get("tempo_ms"), False, novo_ctx, [])
    except Exception as e:
        logger.error(f"Anti-loop erro: {e}")

    dado_web = None
    try:
        if precisa_busca_web(mensagem):
            dado_web = buscar_com_validacao(mensagem)
            if dado_web and not dado_web.get("sucesso"):
                dado_web = None
    except Exception as e:
        logger.warning(f"Web search erro: {e}")
        dado_web = None

    resultado_kb = None
    kb_score     = 0.0
    artigo_explicito = None
    try:
        artigo_explicito = _extrair_artigo(mensagem)
        resultado_kb = (buscar_artigo_exato(artigo_explicito)
                        if artigo_explicito else buscar_kb(mensagem))
        kb_score = resultado_kb["score"] if resultado_kb else 0.0
    except Exception as e:
        logger.error(f"KB erro: {e}")

    intencao, confianca, palavras, entidades = "desconhecida", 0, [], {}
    try:
        intencao, confianca, palavras, entidades = identificar_intencao(mensagem)
        ultima = obter_ultima_intencao(historico)
        if _herdar(mensagem, intencao, ultima):
            intencao = ultima
    except Exception as e:
        logger.error(f"NLP erro: {e}")
    try:
        rota = _determinar_rota(mensagem, resultado_kb, kb_score,
                                 artigo_explicito, dado_web, intencao)
    except Exception as e:
        logger.error(f"Rota erro: {e}")
        rota = "llm_livre"

    resposta_final = None
    fonte          = None
    meta_llm       = None
    followup       = FOLLOWUP.get(intencao, "")
    caso_resumo    = resumo_caso(contexto)
    tom_usuario    = contexto.get("tom", "neutro")
    agora          = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    caso_header    = (
        f"USER_TOM={tom_usuario}\n"
        f"TIMESTAMP={agora}\n"
        + (f"CASE CONTEXT (from conversation): {caso_resumo}\n" if caso_resumo else "")
        + "\n"
    ) if (tom_usuario != "neutro" or caso_resumo) else ""

    try:
        if rota == "off_scope":
            caso_anterior = contexto.get("caso", {})
            tem_historico = len(historico) > 0 and caso_anterior

            try:
                from chatbot.websearch import detectar_pressao_emocional
                sob_pressao = detectar_pressao_emocional(mensagem)
            except Exception:
                sob_pressao = False

            if tem_historico:
                instrucao_pressao = (
                    "\nIMPORTANT: The user is using emotional pressure or insistence to make "
                    "you answer an off-scope question. Stay warm and acknowledge their feelings, "
                    "but DO NOT give in and DO NOT answer the off-scope topic. Hold the boundary "
                    "kindly but firmly. Never say 'just this once' or 'since you insist'.\n"
                ) if sob_pressao else ""
                prompt_redirect = (
                    f"{caso_header}"
                    "USER ASKED SOMETHING OFF-TOPIC (outside Brazilian Consumer Law / CDC scope). "
                    "Politely redirect to consumer law. If there is CASE CONTEXT above, gently "
                    "remind the user of what was being discussed and offer to continue. "
                    "Be warm, brief (2 sentences max), and natural — not robotic. "
                    "Vary your phrasing — never use the same opening twice. "
                    + instrucao_pressao +
                    "Examples of good redirects:\n"
                    "- 'Olha, esse assunto foge um pouco da minha praia — sou especialista em direito "
                    "  do consumidor. Mas voltando ao seu caso da [empresa], onde paramos?'\n"
                    "- 'Aí já é fora da minha área de atuação. Posso te ajudar com algo sobre compras, "
                    "  contratos, garantia? E aquele problema que você mencionou?'\n"
                    "Be conversational, not a script."
                )
                r_llm = consultar_llm(mensagem, contexto_kb=prompt_redirect,
                                      historico=historico[-4:], nome=nome_agente, revelar=revelar)
                meta_llm = r_llm
                if r_llm.get("sucesso") and r_llm.get("resposta"):
                    resposta_final = r_llm["resposta"]
                else:
                    resposta_final = _redirect_off_scope_variado(caso_anterior)
            else:
                resposta_final = _redirect_off_scope_variado(None)
            fonte = "off_scope_redirect"

        elif rota == "kb_pura":
            conteudo_kb = _montar_kb(resultado_kb)
            r_llm = consultar_llm(
                mensagem,
                contexto_kb=caso_header + _prompt_kb(conteudo_kb, followup, eh_primeira_mensagem, mensagem, kb_score),
                historico=historico,
                nome=nome_agente,
                revelar=revelar,
            )
            meta_llm = r_llm
            if r_llm.get("sucesso") and r_llm.get("resposta"):
                resposta_final = r_llm["resposta"]
            else:
                partes = [conteudo_kb]
                if followup: partes.append(followup)
                resposta_final = "\n\n".join(partes)
            fonte = "base_conhecimento"

        elif rota == "llm_web":
            ctx_web = (caso_header + _prompt_web(dado_web, eh_primeira_mensagem, mensagem)) if dado_web else caso_header or None
            r_llm = consultar_llm(
                mensagem,
                contexto_kb=ctx_web,
                historico=historico,
                nome=nome_agente,
                revelar=revelar,
                usar_websearch=(dado_web is None),
            )
            meta_llm = r_llm
            if r_llm.get("sucesso") and r_llm.get("resposta"):
                resposta_final = r_llm["resposta"]
                fonte = r_llm.get("fonte", "llm")
            elif dado_web:
                resposta_final = f"{dado_web['texto']}\n\n_Fonte: {dado_web.get('fonte','')}_"
                fonte = "web_fallback"
            else:
                resposta_final = _sem_dados()
                fonte = "fallback_local"

        elif rota == "kb_web_llm":
            conteudo_kb = _montar_kb(resultado_kb)
            r_llm = consultar_llm(
                mensagem,
                contexto_kb=_prompt_kb_web(conteudo_kb, dado_web, followup, eh_primeira_mensagem, mensagem),
                historico=historico,
                nome=nome_agente,
                revelar=revelar,
            )
            meta_llm = r_llm
            if r_llm.get("sucesso") and r_llm.get("resposta"):
                resposta_final = r_llm["resposta"]
                fonte = "base_conhecimento+web"
            else:
                resposta_final = conteudo_kb + "\n\n" + dado_web["texto"]
                fonte = "base_conhecimento_fallback"

        else:
            ctx_livre = None
            if caso_header or eh_primeira_mensagem:
                ctx_livre = caso_header + (_prompt_livre(eh_primeira_mensagem, mensagem) or "")
            r_llm = consultar_llm(
                mensagem,
                contexto_kb=ctx_livre or None,
                historico=historico,
                nome=nome_agente,
                revelar=revelar,
            )
            meta_llm = r_llm
            if r_llm.get("sucesso") and r_llm.get("resposta"):
                resposta_final = r_llm["resposta"]
                fonte = "llm"
            else:
                resposta_final = _fallback_inteligente(resultado_kb, kb_score, intencao, contexto)
                fonte = "fallback_inteligente"

    except Exception as e:
        logger.error(f"Execução rota '{rota}' erro: {e}")
        resposta_final = _sem_dados()
        fonte = "erro_interno"

    try:
        relacionados = [{"tag": t, "label": ROTULOS.get(t, t.replace("_"," "))}
                        for t in RELACIONADOS.get(intencao, [])]
        novo_ctx = _atualizar_ctx(contexto, intencao, mensagem, entidades, nome_agente, revelar)
    except Exception as e:
        logger.error(f"Resultado erro: {e}")
        relacionados = []
        novo_ctx = contexto

    usou_web = dado_web is not None and dado_web.get("sucesso", False)
    usou_llm = fonte not in ("fallback_local", "erro_interno", "sistema")

    return _resultado(
        mensagem, intencao,
        resposta_final or _sem_dados(),
        fonte or "fallback_local",
        kb_score, resultado_kb,
        usou_llm,
        meta_llm.get("tempo_ms") if meta_llm else None,
        usou_web, novo_ctx, relacionados,
        dado_web=dado_web,
    )

def _resultado(mensagem, intencao, resposta, fonte, kb_score, resultado_kb,
               usou_llm, llm_ms, usou_web, contexto, relacionados, dado_web=None):
    agora_ts = datetime.datetime.now()
    return {
        "mensagem_usuario":     mensagem,
        "intencao":             intencao,
        "confianca":            0,
        "palavras_encontradas": [],
        "contexto":             contexto,
        "resposta":             resposta,
        "fonte":                fonte,
        "timestamp":            agora_ts.strftime("%d/%m/%Y %H:%M:%S"),
        "timestamp_iso":        agora_ts.isoformat(),
        "kb_score":             round(float(kb_score or 0), 3),
        "kb_resultado":         {
            "titulo":  resultado_kb.get("titulo"),
            "score":   kb_score,
            "artigo":  resultado_kb.get("art_num"),
        } if resultado_kb else None,
        "usou_llm":     bool(usou_llm),
        "usou_web":     bool(usou_web),
        "llm_tempo_ms": llm_ms,
        "dado_web":     {
            "confianca":  dado_web.get("confianca", "media"),
            "fonte":      dado_web.get("fonte", ""),
            "data_busca": dado_web.get("data_busca", ""),
        } if dado_web else None,
        "dicas":        [],
        "relacionados": relacionados or [],
        "oferta":       "",
    }

def _atualizar_ctx(contexto, intencao, mensagem, entidades, nome_agente, revelar):
    try:
        novo = atualizar_contexto(contexto, intencao, mensagem, entidades)
        novo["nome_agente"] = nome_agente
        novo["revelado"]    = contexto.get("revelado", False) or revelar
        return novo
    except Exception:
        return {**contexto, "nome_agente": nome_agente, "revelado": revelar}

def _perguntou_se_e_bot(mensagem):
    try:
        m = mensagem.lower()
        return any(g in m for g in [
            "voce e um bot","você é um bot","e robo","é robô","voce e humano","você é humano",
            "voce e ia","você é ia","are you a bot","are you human","are you ai","are you real",
            "is this a bot","eres un bot","eres humano","you are a bot","who are you","what are you",
            "quem e voce","quem é você",
        ])
    except Exception:
        return False

def _extrair_artigo(texto):
    try:
        m = re.search(r'\bart(?:igo)?\.?\s*(\d+)', normalizar(texto))
        return int(m.group(1)) if m else None
    except Exception:
        return None

def _herdar(msg, intencao, ultima):
    try:
        if not ultima or intencao != "desconhecida": return False
        gatilhos = ["sim","ok","certo","beleza","quero","pode","vai","sigo","continue","mais","e ai"]
        m = msg.lower().strip()
        return any(m.startswith(g) for g in gatilhos) or len(m.split()) <= 3
    except Exception:
        return False

def _montar_kb(kb):
    try:
        if not kb: return ""
        tipo = kb.get("tipo","")
        if tipo == "artigo":
            linhas = [f"**{kb.get('titulo','')} (Art. {kb.get('art_num','')} CDC)**",
                      kb.get("resumo",""), kb.get("texto","")]
            prazos = kb.get("prazos",{})
            if prazos:
                linhas.append("**Prazos:** " + " | ".join(
                    f"{k.replace('_',' ')}: {v}" for k,v in prazos.items()))
            opcoes = kb.get("opcoes",[])
            if opcoes:
                linhas.append("**Suas opções:** " + " | ".join(opcoes))
            return "\n\n".join(l for l in linhas if l)
        elif tipo == "fluxo":
            return f"**{kb.get('titulo','')}**\n\n" + "\n".join(kb.get("passos",[]))
        elif tipo in ("orgao","dado_atualizado"):
            titulo   = kb.get("titulo","")
            conteudo = kb.get("resumo") or kb.get("descricao","")
            como     = kb.get("como","")
            fonte    = kb.get("fonte","")
            resp     = f"**{titulo}**\n\n{conteudo}"
            if como:  resp += f"\n\nComo acionar: {como}"
            if fonte: resp += f"\n\n_Fonte: {fonte}_"
            return resp
        return ""
    except Exception as e:
        logger.error(f"_montar_kb erro: {e}")
        return ""

_AVISOS_INSTABILIDADE = [
    "Tive uma instabilidade momentânea aqui, mas dá pra adiantar isso:",
    "Achei algo na base enquanto recupero a conexão completa:",
    "Não consegui processar tudo agora, mas tem isso pra te orientar:",
    "Olha, com base no que tenho aqui posso te dizer o seguinte:",
]
_PEDIDOS_REFORMULAR = [
    "Não peguei bem essa parte — pode me contar de outro jeito?",
    "Me perdeu um pouco aí. Consegue reformular?",
    "Não entendi muito bem. Pode dar mais detalhes do que aconteceu?",
    "Dei uma travada nesse ponto. Pode reescrever de outra forma?",
    "Não captei direito. Conta de novo, mas com mais contexto?",
]

_OFF_SCOPE_VARIACOES_SEM_CASO = [
    "Esse assunto foge da minha área — sou especialista em direito do consumidor. "
    "Mas se você tiver alguma dúvida sobre compra, contrato, garantia ou cobrança, "
    "manda aí que ajudo!",

    "Aí já não é minha praia. Meu negócio é direitos do consumidor — produto com defeito, "
    "cobrança indevida, problemas com empresa, esse tipo de coisa. Posso te ajudar com algo assim?",

    "Hmm, não é bem comigo. Eu cuido de questões de consumidor — Procon, CDC, garantia, "
    "reembolso, plano de saúde, banco. Tem algo nessa linha em que posso ajudar?",

    "Esse tema escapa do que faço. Eu sou focado em CDC — direitos do consumidor brasileiro. "
    "Que tal? Algum problema com loja, banco, prestador de serviço?",

    "Aí já não é minha especialidade. Minha praia é direitos do consumidor: compras, "
    "garantia, cobranças, contratos. Quer falar sobre algo nessa linha?",
]

_OFF_SCOPE_VARIACOES_COM_CASO = [
    "Esse assunto não é bem comigo. Mas voltando ao seu caso{empresa_str}, em que mais posso ajudar?",
    "Aí já foge da minha área. Sobre {tema} que conversamos antes, quer continuar de onde paramos?",
    "Esse tema escapa do meu foco. E aquele assunto{empresa_str} — resolveu ou ainda precisa de ajuda?",
    "Hmm, não é minha especialidade. Mas sobre o que comentou antes{empresa_str}, posso te ajudar?",
]

def _redirect_off_scope_variado(caso):
    """Retorna um redirecionamento variado, com referência ao caso se houver."""
    if caso:
        var = random.choice(_OFF_SCOPE_VARIACOES_COM_CASO)
        empresa = caso.get("empresa", "")
        empresa_str = f" (da {empresa})" if empresa else ""
        tema = caso.get("objeto") or caso.get("problema") or "o que você comentou"
        return var.format(empresa_str=empresa_str, tema=tema)
    return random.choice(_OFF_SCOPE_VARIACOES_SEM_CASO)


def _fallback_inteligente(resultado_kb, kb_score, intencao, contexto):
    """
    Fallback inteligente: usa o que tiver disponível em vez de resposta genérica.
    Prioridade: KB parcial > fluxo de ação > dica de órgão > pedir reformulação.
    """
    try:
        if resultado_kb and kb_score > 0.25:
            conteudo = _montar_kb(resultado_kb)
            if conteudo:
                aviso = random.choice(_AVISOS_INSTABILIDADE)
                return f"{aviso}\n\n{conteudo}"

        sugestoes = {
            "garantia":             "Produto com defeito: registre a reclamação no consumidor.gov.br e exija reparo em 30 dias (Art. 18 CDC).",
            "cobranca_indevida":    "Cobrança indevida: conteste com o fornecedor por escrito e guarde o protocolo. Valor cobrado a mais: devolução em dobro (Art. 42 CDC).",
            "arrependimento":       "Compra online: você tem 7 dias para desistir após o recebimento (Art. 49 CDC). Notifique a empresa por escrito.",
            "atraso_entrega":       "Entrega atrasada: exija cumprimento, aceite equivalente ou cancele com reembolso (Art. 35 CDC).",
            "empresa_negou_solucao":"Empresa negou solução: tente consumidor.gov.br (resposta em 10 dias) ou o Procon do seu estado.",
            "procon":               "Procon: acesse procon.{estado}.gov.br ou vá pessoalmente com documentos do caso, nota fiscal e protocolos.",
        }
        if intencao in sugestoes:
            return f"Tive uma instabilidade momentânea, mas posso adiantar:\n\n{sugestoes[intencao]}"

        return random.choice(_PEDIDOS_REFORMULAR)
    except Exception:
        return "Pode reformular sua pergunta?"

def _sem_dados():
    try:
        return random.choice(_PEDIDOS_REFORMULAR)
    except Exception:
        return "Pode reformular sua pergunta?"

def _vazio(ctx):
    try:
        return _resultado("","vazia","Por favor, escreva sua dúvida.","sistema",
                          0.0,None,False,None,False,ctx or {},[])
    except Exception:
        return {"resposta":"Por favor, escreva sua dúvida.","fonte":"sistema",
                "usou_llm":False,"usou_web":False,"relacionados":[],"dicas":[],"oferta":"",
                "kb_score":0.0,"kb_resultado":None,"llm_tempo_ms":None,
                "intencao":"vazia","confianca":0,"palavras_encontradas":[],"contexto":{}}
