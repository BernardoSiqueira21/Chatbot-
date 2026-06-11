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
