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

def _detectar_chave(mensagem):
    """Detecta qual dado está sendo pedido e retorna a chave do cache."""
    mn = _norm(mensagem)

    # Importa o mapa de moedas do websearch para consistência
    try:
        from chatbot.websearch import _MOEDAS_MAP, _norm as _ws_norm
        mn_ws = _ws_norm(mensagem)
        for termo in sorted(_MOEDAS_MAP.keys(), key=len, reverse=True):
            par, _ = _MOEDAS_MAP[termo]
            if termo in mn_ws:
                # Usa o par como chave de cache (ex: "USD-BRL", "CNY-BRL")
                return par.replace("-","_").lower()
    except Exception:
        pass

    # Fallback para assuntos não-moeda
    mapeamento = [
        (["ibovespa","bolsa"],                              "ibovespa"),
        (["selic","taxa selic","taxa basica"],              "selic"),
        (["ipca","inflacao","igpm"],                        "ipca"),
        (["salario minimo","piso salarial"],                "salario_minimo"),
        (["teto inss","inss maximo","previdencia teto"],    "inss_teto"),
        (["imposto renda","irpf"],                          "imposto_renda"),
        (["fgts"],                                          "fgts"),
        (["bolsa familia","bpc","auxilio"],                 "bolsa_familia"),
        (["juros rotativo","rotativo cartao",
          "juros cartao","limite juros cartao"],            "juros_rotativo"),
        (["gasolina","combustivel"],                        "gasolina"),
    ]
    for termos, chave in mapeamento:
        if any(t in mn for t in termos):
            return chave
    return None

def _norm(t):
    return "".join(c for c in unicodedata.normalize("NFD", t.lower())
                   if unicodedata.category(c) != "Mn")

def get_cache(mensagem):
    """
    Retorna dado em cache se válido, ou None se expirado/inexistente.
    """
    chave = _detectar_chave(mensagem)
    if not chave:
        return None

    cache = _carregar_cache()
    entrada = cache.get(chave)
    if not entrada:
        return None

    ttl = TTL.get(CATEGORIAS.get(chave, "anual"), 24*3600)
    idade = time.time() - entrada.get("timestamp", 0)

    if idade > ttl:
        logger.debug(f"Cache expirado para '{chave}' ({idade/3600:.1f}h)")
        return None

    entrada["cache_hit"] = True
    entrada["idade_horas"] = round(idade / 3600, 1)
    return entrada

def set_cache(mensagem, texto, fonte, confianca="media"):
    """
    Salva dado no cache com timestamp e nível de confiança.
    """
    chave = _detectar_chave(mensagem)
    if not chave:
        return

    cache = _carregar_cache()
    cache[chave] = {
        "texto":      texto,
        "fonte":      fonte,
        "confianca":  confianca,
        "timestamp":  time.time(),
        "chave":      chave,
        "categoria":  CATEGORIAS.get(chave, "anual"),
    }
    _salvar_cache(cache)
    logger.debug(f"Cache salvo: {chave} (confianca={confianca})")

def validar_duplo(texto1, fonte1, texto2, fonte2):
    """
    Compara dois valores numéricos encontrados em dois textos.
    Retorna (texto_final, fonte_final, confianca).

    Confiança ALTA: os dois valores numéricos principais concordam (±2%)
    Confiança MÉDIA: divergem, usa o texto1 (mais recente/prioritário)
    """
    nums1 = _extrair_numeros(texto1)
    nums2 = _extrair_numeros(texto2)

    if not nums1 or not nums2:
        return texto1, fonte1, "media"

    # Compara o primeiro número significativo de cada
    n1, n2 = nums1[0], nums2[0]
    if n1 == 0 or n2 == 0:
        return texto1, fonte1, "media"

    diferenca = abs(n1 - n2) / max(n1, n2)
    if diferenca <= 0.02:  # concordam com margem de 2%
        return texto1, f"{fonte1} + {fonte2}", "alta"
    else:
        logger.info(f"Validação divergiu: {n1} vs {n2} ({diferenca:.1%})")
        return texto1, fonte1, "media"

def _extrair_numeros(texto):
    """Extrai números relevantes de um texto (preços, taxas, percentuais)."""
    nums = []
    # Normaliza: troca vírgula decimal por ponto, remove separadores de milhar
    texto_norm = re.sub(r'(\d)\.(\d{3})', r'\1\2', texto)  # remove ponto de milhar
    texto_norm = texto_norm.replace(',', '.')               # vírgula → ponto decimal
    for m in re.finditer(r'\d+\.?\d*', texto_norm):
        try:
            n = float(m.group())
            if n > 0.001:
                nums.append(n)
        except Exception:
            pass
    return nums

def listar_cache():
    """Retorna resumo do cache atual (para debug/admin)."""
    cache = _carregar_cache()
    agora = time.time()
    resultado = {}
    for chave, entrada in cache.items():
        ttl = TTL.get(CATEGORIAS.get(chave,"anual"), 24*3600)
        idade = agora - entrada.get("timestamp", 0)
        expirado = idade > ttl
        resultado[chave] = {
            "confianca": entrada.get("confianca","?"),
            "idade_horas": round(idade/3600, 1),
            "expirado": expirado,
            "fonte": entrada.get("fonte","?"),
            "preview": entrada.get("texto","")[:80],
        }
    return resultado

def limpar_cache():
    """Limpa todo o cache (para testes ou reset manual)."""
    try:
        if CACHE_FILE.exists():
            CACHE_FILE.unlink()
        logger.info("Cache limpo")
    except Exception as e:
        logger.warning(f"Erro ao limpar cache: {e}")
