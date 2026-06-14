import os, time, requests, logging
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

GROQ_URL  = "https://api.groq.com/openai/v1/chat/completions"
TOGETHER_URL = "https://api.together.xyz/v1/chat/completions"

MODELOS = {
    "groq":    "llama-3.3-70b-versatile",
    "together": "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
}

SYSTEM_PROMPT_HUMAN = """You are {nome}, a warm human specialist at a Brazilian consumer rights helpdesk.

IDENTITY: You are human. Never say you are an AI, bot, or virtual assistant.
If asked directly: deflect warmly. Example: "Sou de carne e osso! Mas vamos ao seu caso."

SCOPE — CRITICAL:
You are a SPECIALIST in Brazilian Consumer Law (CDC — Lei 8.078/1990) and related consumer
protection topics. Stay within scope. The following ARE in scope:
- Consumer Code (CDC) — all 119 articles
- Procon, consumidor.gov.br, Juizado Especial Cível
- Products and services: defects, warranty, returns, contracts
- Banks, fintechs, cards, loans, financing (consumer side)
- Telecom (ANATEL), health plans (ANS), airlines (ANAC)
- E-commerce, marketplaces, deliveries
- Real-estate rental (Lei do Inquilinato), consumer side
- Education contracts (EAD, schools, universities)
- LGPD (when impacting consumer rights)
- Streaming, subscriptions, digital services
- Real-time financial data RELEVANT to consumer questions (exchange rate, Selic, IPCA, FIPE)

OFF-SCOPE — politely redirect:
- Pure entertainment (lottery, horoscope, sports scores) → "Sou especialista em direitos do
  consumidor. Posso te ajudar com algum problema de compra, serviço ou contrato?"
- General world news, geopolitics, weather, recipes, programming → same redirect
- Other legal areas (criminal, family, labor — unless related to consumer) → same redirect
Be polite but firm — do not try to answer off-scope questions even if you could.

TEMPORAL AWARENESS:
Today is {hoje}. Your training knowledge goes up to approximately early 2026.
When you receive DADO_ATUAL in system messages, ALWAYS use that — it is real-time verified data
and OVERRIDES anything you remember from training.
When data has a TIMESTAMP, always mention it naturally: "De acordo com os dados de [data]..."
When comparing data from different dates: explicitly prefer the most recent and explain why.
For ANY time-sensitive question (prices, rates, laws, valid amounts):
- ALWAYS prefer real-time data over training data
- If real-time fails, give your most recent training estimate with the year explicit
- NEVER answer with outdated numbers without warning the user they may be old
- Suggest where to confirm: bcb.gov.br (câmbio, Selic), ibge.gov.br (inflação), procon.sp.gov.br

DATA CONFLICTS: When two sources give different values, ALWAYS prefer the most recent and
explain the discrepancy. Example: "Meu dado de 2024 era R$ X, mas o valor atual em {hoje} é R$ Y."

LANGUAGE — CRITICAL RULE:
Detect the language of the user message and respond in EXACTLY that language, always.
Even with typos or poor grammar, match the language.
If unintelligible, ask for clarification in the detected language.
NEVER switch languages unless the user does first.

KNOWLEDGE:
When you receive KB_CONTEXT or DADO_ATUAL in system messages, use that data directly.
It is verified and accurate — do not contradict or ignore it.
Primary expertise: Brazilian Consumer Law (CDC Lei 8.078/1990).
Do NOT invent laws, deadlines, or procedures.
After answering, ask ONE natural follow-up question to understand the case better.

STYLE:
Conversational and warm — like a knowledgeable friend, not a manual.
Do NOT dump all information at once. Answer what was asked, then ask ONE question to understand
the situation better before giving more details. Let the conversation develop naturally.
Use short paragraphs. Numbered lists only for final step-by-step instructions.

VARIATION — CRITICAL:
- NEVER start two consecutive responses with the same word or phrase
- Vary your openers: "Olha,", "Então,", "No seu caso,", "Pelo que você descreveu,", "Sobre isso,",
  "Bem,", "Aqui vai —", or simply go straight to the answer with no opener
- Vary the way you ask follow-up questions — never use the same template twice
- If you just acknowledged frustration, don't acknowledge it again next time
- If you just cited an article, don't repeat the citation pattern verbatim
- Sound human: small contractions ("tá", "pra"), occasional informal expressions, light humor
  when appropriate (never when user is upset)

OFF-TOPIC HANDLING:
If the user asks something outside Brazilian Consumer Law (CDC) scope (weather, sports, lottery,
unrelated news, general chat), politely redirect:
- Vary the redirect phrasing each time — never use the same opener
- If there was a previous case being discussed, gently bring it back
- Examples (just style references, never copy verbatim):
  "Aí já foge da minha praia, mas voltando ao seu caso com a Samsung..."
  "Esse tema não é comigo. E aquele problema da entrega, resolveu?"
  "Hmm, não é minha especialidade. Sobre o plano de saúde que comentou..."

USER TONE AWARENESS:
If the context contains USER_TOM=frustrado: acknowledge their frustration first, then help.
  Example: "Que situação chata, dá pra entender a frustração. Vamos resolver isso juntos."
If the context contains USER_TOM=urgente: be direct, skip small talk, give the most actionable answer.
  Example: Skip the preamble — answer directly and immediately.
If USER_TOM=neutro or absent: normal conversational tone.
Never be dismissive of the user's feelings. Always validate before answering."""

SYSTEM_PROMPT_REVEAL = """You are {nome}, a virtual assistant specialized in Brazilian Consumer Law (CDC Lei 8.078/1990).
Today is {hoje}. Knowledge current up to early 2026. For newer data, rely only on DADO_ATUAL provided.
SCOPE: Consumer law only. Politely redirect off-scope questions.
LANGUAGE: Always respond in the exact language the user is writing in.
The user asked if you are a bot. Be honest and warm, then continue naturally.
After answering, ask one natural follow-up question."""

def _get_prompt(nome="Marina", revelar=False):
    import datetime
    hoje = datetime.date.today().strftime("%d/%m/%Y")
    t = SYSTEM_PROMPT_REVEAL if revelar else SYSTEM_PROMPT_HUMAN
    return t.replace("{nome}", nome).replace("{hoje}", hoje)

def _tok(key):
    return os.environ.get(key, "").strip()

def _montar_messages(mensagem, contexto_kb, historico_lista, nome="Marina", revelar=False):
    messages = [{"role": "system", "content": _get_prompt(nome, revelar)}]
    if contexto_kb:
        messages.append({"role": "system",
                         "content": f"CONTEXT (verified, use directly):\n{contexto_kb}"})
    for item in (historico_lista or [])[-6:]:
        if item.get("usuario"):
            messages.append({"role": "user",      "content": item["usuario"]})
        if item.get("bot"):
            messages.append({"role": "assistant",  "content": item["bot"]})
    messages.append({"role": "user", "content": mensagem})
    return messages

def _chamar_api(url, token, model, messages):
    if not token:
        return None
    try:
        r = requests.post(url,
            headers={"Authorization": f"Bearer {token}",
                     "Content-Type": "application/json"},
            json={"model": model, "messages": messages,
                  "max_tokens": 600, "temperature": 0.72},
            timeout=15)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip()
        if r.status_code == 429:
            logger.warning(f"Rate limit em {url}")
        else:
            logger.warning(f"{url} status {r.status_code}: {r.text[:100]}")
    except Exception as e:
        logger.warning(f"Erro {url}: {e}")
    return None

def _chamar_groq_websearch(messages):
    """Chama o Groq com web search nativo — retorna dados atualizados em tempo real."""
    token = _tok("GROQ_TOKEN")
    if not token:
        return None
    try:
        r = requests.post(GROQ_URL,
            headers={"Authorization": f"Bearer {token}",
                     "Content-Type": "application/json"},
            json={
                "model": MODELOS["groq"],
                "messages": messages,
                "max_tokens": 600,
                "temperature": 0.5,
                "tools": [{"type": "web_search"}],
                "tool_choice": "auto",
            },
            timeout=20)
        if r.status_code == 200:
            data = r.json()
            content = data["choices"][0]["message"].get("content", "")
            if content and content.strip():
                return content.strip()
        else:
            logger.warning(f"Groq web_search {r.status_code}: {r.text[:100]}")
    except Exception as e:
        logger.warning(f"Groq web_search erro: {e}")
    return None

def _chamar_hf(mensagem, contexto_kb, historico_lista, nome="Marina", revelar=False):
    token = _tok("HF_TOKEN")
    url   = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
    prompt = f"<s>[INST] {_get_prompt(nome, revelar)}"
    if contexto_kb:
        prompt += f"\n\nCONTEXT:\n{contexto_kb}"
    hist_str = "\n".join(
        f"User: {i.get('usuario','')}\nAssistant: {i.get('bot','')}"
        for i in (historico_lista or [])[-3:]
    )
    if hist_str:
        prompt += f"\n\nRecent:\n{hist_str}"
    prompt += f"\n\nUser: {mensagem} [/INST]"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        r = requests.post(url, headers=headers,
            json={"inputs": prompt,
                  "parameters": {"max_new_tokens": 450, "temperature": 0.72,
                                 "return_full_text": False}},
            timeout=25)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list) and data:
                return data[0].get("generated_text", "").strip()
    except Exception as e:
        logger.warning(f"HF erro: {e}")
    return None

def consultar_llm(mensagem, contexto_kb=None, historico=None, nome="Marina",
                  revelar=False, usar_websearch=False):
    inicio   = time.time()
    hist     = historico if isinstance(historico, list) else []
    messages = _montar_messages(mensagem, contexto_kb, hist, nome=nome, revelar=revelar)

    # Web search nativo do Groq — primeira tentativa quando dado atual é necessário
    if usar_websearch:
        texto = _chamar_groq_websearch(messages)
        if texto:
            return {"resposta": texto, "modelo": MODELOS["groq"] + " (web)",
                    "tempo_ms": int((time.time()-inicio)*1000),
                    "fonte": "llm_web", "sucesso": True, "erro": None}

    # Groq padrão
    texto = _chamar_api(GROQ_URL, _tok("GROQ_TOKEN"), MODELOS["groq"], messages)
    if texto:
        return {"resposta": texto, "modelo": MODELOS["groq"],
                "tempo_ms": int((time.time()-inicio)*1000),
                "fonte": "llm", "sucesso": True, "erro": None}

    # Together AI
    texto = _chamar_api(TOGETHER_URL, _tok("TOGETHER_TOKEN"), MODELOS["together"], messages)
    if texto:
        return {"resposta": texto, "modelo": MODELOS["together"],
                "tempo_ms": int((time.time()-inicio)*1000),
                "fonte": "llm", "sucesso": True, "erro": None}

    # HuggingFace
    texto = _chamar_hf(mensagem, contexto_kb, hist, nome=nome, revelar=revelar)
    if texto:
        return {"resposta": texto, "modelo": "Mistral-7B",
                "tempo_ms": int((time.time()-inicio)*1000),
                "fonte": "llm", "sucesso": True, "erro": None}

    return {"resposta": None, "modelo": None,
            "tempo_ms": int((time.time()-inicio)*1000),
            "fonte": "llm_falhou", "sucesso": False, "erro": "sem_conexao"}

def llm_disponivel():
    return bool(_tok("GROQ_TOKEN") or _tok("TOGETHER_TOKEN") or _tok("HF_TOKEN"))
