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
    # DD/MM/AAAA ou DD/MM/AA
    m = re.search(r'\b(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{2,4})\b', texto)
    if m:
        d, mo, a = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if a < 100: a += 2000
        try:
            return datetime.date(a, mo, d)
        except ValueError:
            return None

    # "dia X de mês" por extenso
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

def _detectar_intencao_prazo(mensagem):
    m = mensagem.lower()
    return any(p in m for p in [
        "calcular prazo","calcular prazos","ainda tenho prazo","ainda estou no prazo",
        "qual o prazo","quanto tempo tenho","prazo venceu","perdi o prazo",
        "ja passou o prazo","tempo para reclamar","quando vence","prazo garantia",
        "quanto tempo ainda","posso ainda reclamar",
    ])

def montar_prompt_prazos(contexto, historico, mensagem_usuario):
    """
    Retorna (é_calculadora, data_encontrada, resultado_calculo).
    Busca data na mensagem atual, no histórico e no contexto do caso.
    """
    if not _detectar_intencao_prazo(mensagem_usuario):
        return False, None, None

    # Tenta extrair data
    data = _extrair_data(mensagem_usuario)

    # Se não encontrou na mensagem, busca no histórico
    if not data:
        for item in reversed(historico or []):
            data = _extrair_data(item.get("usuario",""))
            if data: break

    # Se não encontrou no histórico, busca no contexto do caso
    if not data and contexto.get("caso",{}).get("data_evento"):
        data = _extrair_data(contexto["caso"]["data_evento"])

    if not data:
        return True, None, None  # é calculadora mas sem data

    resultado = calcular_prazos(data, contexto)
    return True, data, resultado

def formatar_prazos_para_llm(resultado, contexto=None):
    """Formata o resultado para o LLM usar na resposta."""
    linhas = [
        f"CÁLCULO DE PRAZOS CDC — base: {resultado['data_base']} ({resultado['dias_passados']} dias atrás)",
        ""
    ]
    for p in resultado["prazos"]:
        if p["tipo"] == "anos": continue  # prescrição judicial — mostra separado
        emoji = "✅" if p["status"] == "ok" else "⚠️" if p["status"] == "urgente" else "❌"
        if p["status"] == "vencido":
            linhas.append(f"{emoji} {p['nome']} ({p['artigo']}): VENCIDO há {abs(p['restante'])} dia(s)")
        else:
            linhas.append(f"{emoji} {p['nome']} ({p['artigo']}): {p['restante']} dia(s) restante(s)")

    # Prescrição judicial separada
    prescricao = next((p for p in resultado["prazos"] if p["tipo"] == "anos"), None)
    if prescricao:
        linhas.append(f"\n⚖️  {prescricao['nome']} ({prescricao['artigo']}): "
                      f"{'VENCIDO' if prescricao['status'] == 'vencido' else str(prescricao['restante'])+' dias restantes'}")

    return "\n".join(linhas)
