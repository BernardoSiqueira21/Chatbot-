import re, time, logging, unicodedata, datetime, os
import requests

logger    = logging.getLogger(__name__)
TIMEOUT   = 8
HOJE      = datetime.date.today()

def _norm(t):
    return "".join(c for c in unicodedata.normalize("NFD", t.lower())
                   if unicodedata.category(c) != "Mn")

_MOEDAS_MAP = {
    "dolar americano":    ("USD-BRL","Dólar americano"),
    "dolar canadense":    ("CAD-BRL","Dólar canadense"),
    "dolar australiano":  ("AUD-BRL","Dólar australiano"),
    "franco suico":       ("CHF-BRL","Franco suíço"),
    "libra esterlina":    ("GBP-BRL","Libra esterlina"),
    "peso argentino":     ("ARS-BRL","Peso argentino"),
    "peso mexicano":      ("MXN-BRL","Peso mexicano"),
    "peso chileno":       ("CLP-BRL","Peso chileno"),
    "dolar":    ("USD-BRL","Dólar americano"),
    "dollar":   ("USD-BRL","Dólar americano"),
    "euro":     ("EUR-BRL","Euro"),
    "libra":    ("GBP-BRL","Libra esterlina"),
    "iene":     ("JPY-BRL","Iene japonês"),
    "yen":      ("JPY-BRL","Iene japonês"),
    "yuan":     ("CNY-BRL","Yuan chinês"),
    "renminbi": ("CNY-BRL","Yuan chinês"),
    "rublo":    ("RUB-BRL","Rublo russo"),
    "usd": ("USD-BRL","Dólar americano"),
    "eur": ("EUR-BRL","Euro"),
    "gbp": ("GBP-BRL","Libra esterlina"),
    "jpy": ("JPY-BRL","Iene japonês"),
    "cny": ("CNY-BRL","Yuan chinês"),
}