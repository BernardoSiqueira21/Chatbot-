"""
calculadora_prazos.py — Calculadora de prazos CDC
Calcula automaticamente todos os prazos relevantes baseado em datas da conversa
"""
import re, datetime

PRAZOS_CDC = [
    {
        "nome":        "Arrependimento (compra online/fora da loja)",
        "dias":        7,
        "artigo":      "Art. 49 CDC",
        "tipo":        "corridos",
        "marco":       "recebimento",
        "descricao":   "Para cancelar sem justificativa com reembolso integral",
    },
    {
        "nome":        "Reclamar defeito — produto não durável",
        "dias":        30,
        "artigo":      "Art. 26, I CDC",
        "tipo":        "corridos",
        "marco":       "aparecimento do defeito",
        "descricao":   "Alimentos, cosméticos, produtos descartáveis",
    },
    {
        "nome":        "Reclamar defeito — produto durável",
        "dias":        90,
        "artigo":      "Art. 26, II CDC",
        "tipo":        "corridos",
        "marco":       "aparecimento do defeito",
        "descricao":   "Eletrônicos, eletrodomésticos, móveis, veículos",
    },
    {
        "nome":        "Empresa resolver o defeito",
        "dias":        30,
        "artigo":      "Art. 18 § 1° CDC",
        "tipo":        "corridos",
        "marco":       "reclamação do consumidor",
        "descricao":   "Após 30 dias sem solução: troca, reembolso ou desconto",
    },
    {
        "nome":        "Ação judicial por danos",
        "dias":        5 * 365,
        "artigo":      "Art. 27 CDC",
        "tipo":        "anos",
        "marco":       "conhecimento do dano",
        "descricao":   "5 anos para entrar com ação por dano causado por produto/serviço",
    },
]

def _extrair_data(texto):
    """Extrai a primeira data encontrada no texto."""
    m = re.search(r'\b(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{2,4})\b', texto)
    if m:
        d, mo, a = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if a < 100: a += 2000
        try:
            return datetime.date(a, mo, d)
        except ValueError:
            return None

    meses = {"janeiro":1,"fevereiro":2,"março":3,"marco":3,"abril":4,"maio":5,
             "junho":6,"julho":7,"agosto":8,"setembro":9,"outubro":10,
             "novembro":11,"dezembro":12}
    for mes_nome, mes_num in meses.items():
        m = re.search(rf'\b(\d{{1,2}})\s+(?:de\s+)?{mes_nome}(?:\s+(?:de\s+)?(\d{{4}}))?', texto.lower())
        if m:
            d = int(m.group(1))
            a = int(m.group(2)) if m.group(2) else datetime.date.today().year
            try:
                return datetime.date(a, mes_num, d)
            except ValueError:
                return None
    return None

def calcular_prazos(data_base, contexto=None):
    """
    Calcula todos os prazos CDC a partir de uma data base.
    Retorna lista de resultados com status (OK/VENCIDO/URGENTE).
    """
    hoje    = datetime.date.today()
    diff    = (hoje - data_base).days
    resultados = []

    for prazo in PRAZOS_CDC:
        dias_prazo = prazo["dias"]
        restante   = dias_prazo - diff

        if restante > 7:
            status = "ok"
        elif restante > 0:
            status = "urgente"
        else:
            status = "vencido"

        resultados.append({
            "nome":        prazo["nome"],
            "artigo":      prazo["artigo"],
            "dias":        dias_prazo,
            "restante":    restante,
            "status":      status,
            "marco":       prazo["marco"],
            "descricao":   prazo["descricao"],
            "tipo":        prazo["tipo"],
        })

    return {
        "data_base":    data_base.strftime("%d/%m/%Y"),
        "hoje":         hoje.strftime("%d/%m/%Y"),
        "dias_passados": diff,
        "prazos":        resultados,
    }

