"""
atualizar_kb.py — Atualiza dados que mudam na knowledge_base.json
Execute periodicamente: python atualizar_kb.py
Ou agende com Windows Task Scheduler / cron.
"""
import json, re, time, logging, requests
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)

KB_PATH = Path(__file__).parent / "chatbot" / "knowledge_base.json"
TIMEOUT = 10

def _buscar_html(query):
    try:
        r = requests.get("https://html.duckduckgo.com/html/",
            params={"q": query},
            headers={"User-Agent": "Mozilla/5.0 (compatible; KBUpdater/1.0)",
                     "Accept-Language": "pt-BR"},
            timeout=TIMEOUT)
        if r.status_code != 200:
            return None
        snippets = re.findall(
            r'class="result__snippet"[^>]*>(.*?)</a>', r.text, re.DOTALL)
        if not snippets:
            return None
        texto = re.sub(r'<[^>]+>', '', snippets[0]).strip()
        return re.sub(r'\s+', ' ', texto)[:400]
    except Exception as e:
        logger.warning(f"Busca erro: {e}")
        return None

ATUALIZACOES = [
    {
        "chave": "salario_minimo_2025",
        "query": "salário mínimo Brasil 2026 valor atual decreto",
        "titulo": "Salário Mínimo 2026",
    },
    {
        "chave": "cartao_credito_juros",
        "query": "limite juros rotativo cartão crédito 2025 2026 banco central percentual",
        "titulo": "Juros do Rotativo do Cartão de Crédito",
    },
    {
        "chave": "taxa_selic",
        "query": "taxa selic atual 2026 banco central copom",
        "titulo": "Taxa Selic Atual",
    },
]

def atualizar():
    with open(KB_PATH, encoding="utf-8") as f:
        kb = json.load(f)

    dados = kb.setdefault("dados_atualizados", {})
    atualizados = 0

    for item in ATUALIZACOES:
        logger.info(f"Buscando: {item['titulo']}...")
        texto = _buscar_html(item["query"])
        if texto and len(texto) > 40:
            if item["chave"] in dados:
                dados[item["chave"]]["conteudo_web"] = texto
                dados[item["chave"]]["ultima_atualizacao"] = time.strftime("%Y-%m-%d")
                atualizados += 1
                logger.info(f"  Atualizado: {texto[:80]}...")
            else:
                logger.warning(f"  Chave '{item['chave']}' nao encontrada na KB")
        else:
            logger.warning(f"  Sem resultado para: {item['titulo']}")
        time.sleep(1)

    if atualizados > 0:
        with open(KB_PATH, "w", encoding="utf-8") as f:
            json.dump(kb, f, ensure_ascii=False, indent=2)
        logger.info(f"KB salva com {atualizados} atualizacoes.")
    else:
        logger.info("Nenhuma atualizacao disponivel.")

if __name__ == "__main__":
    atualizar()
