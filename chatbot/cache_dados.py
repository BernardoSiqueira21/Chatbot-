"""
cache_dados.py — Cache com validação dupla para dados voláteis
Funciona assim:
  1. Primeira busca: pega dado da web
  2. Valida com segunda fonte independente
  3. Se concordam → salva com confiança ALTA e TTL longo
  4. Se divergem → salva o mais recente com confiança MÉDIA e TTL curto
  5. Próximas perguntas usam o cache até expirar
  6. Dados financeiros: TTL de 4h | Dados anuais: TTL de 24h
"""
import json, os, time, logging, re, unicodedata
from pathlib import Path

logger = logging.getLogger(__name__)

CACHE_FILE = Path(__file__).parent.parent / "dados_cache.json"

# TTL em segundos
TTL = {
    "cambio":   4 * 3600,
    "mercado":  4 * 3600,
    "anual":    24 * 3600,
    "inflacao": 12 * 3600,
    "juridico": 7 * 24 * 3600,
}

CATEGORIAS = {
    # Pares de câmbio (todos com TTL cambio)
    "usd_brl":"cambio","eur_brl":"cambio","gbp_brl":"cambio","jpy_brl":"cambio",
    "cny_brl":"cambio","chf_brl":"cambio","cad_brl":"cambio","aud_brl":"cambio",
    "ars_brl":"cambio","mxn_brl":"cambio","sek_brl":"cambio","nok_brl":"cambio",
    "dkk_brl":"cambio","rub_brl":"cambio","try_brl":"cambio","zar_brl":"cambio",
    "krw_brl":"cambio","inr_brl":"cambio","nzd_brl":"cambio","sgd_brl":"cambio",
    "thb_brl":"cambio","czk_brl":"cambio","huf_brl":"cambio","pln_brl":"cambio",
    "aed_brl":"cambio",
    # Cripto
    "btc_brl":"mercado","eth_brl":"mercado","ltc_brl":"mercado",
    # Índices
    "ibovespa":"mercado",
    # Econômicos
    "selic":"inflacao","ipca":"inflacao","igpm":"inflacao",
    # Anuais
    "salario_minimo":"anual","inss_teto":"anual","imposto_renda":"anual",
    "fgts":"anual","bolsa_familia":"anual","gasolina":"mercado",
    # Jurídicos
    "juros_rotativo":"juridico","limite_juros":"juridico",
}

def _carregar_cache():
    try:
        if CACHE_FILE.exists():
            with open(CACHE_FILE, encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Cache leitura: {e}")
    return {}

def _salvar_cache(cache):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"Cache escrita: {e}")

