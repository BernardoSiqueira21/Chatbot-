"""
gerador_reclamacao.py — Gera texto formal de reclamação baseado no contexto do caso
"""
import datetime

def _detectar_intencao_reclamacao(mensagem):
    m = mensagem.lower()
    return any(p in m for p in [
        "gerar reclamacao","gerar reclamação","texto reclamacao","texto de reclamacao",
        "escrever reclamacao","redigir reclamacao","reclamacao formal","texto formal",
        "modelo reclamacao","carta reclamacao","reclamar formalmente","quero reclamar",
        "me ajuda a reclamar","como reclamar por escrito",
    ])

def _artigo_aplicavel(intencao):
    mapa = {
        "garantia":             ("Art. 18 CDC", "produto com vício/defeito"),
        "troca":                ("Art. 18 CDC", "recusa de troca"),
        "arrependimento":       ("Art. 49 CDC", "direito de arrependimento"),
        "atraso_entrega":       ("Art. 35 CDC", "descumprimento de prazo"),
        "produto_nao_entregue": ("Art. 35 CDC", "não entrega do produto"),
        "cobranca_indevida":    ("Art. 42 CDC", "cobrança indevida"),
        "reembolso":            ("Art. 18 CDC", "negativa de reembolso"),
        "cancelamento":         ("Art. 49 CDC", "cancelamento e reembolso"),
        "empresa_negou_solucao":("Art. 18 CDC", "recusa em resolver o problema"),
        "propaganda_enganosa":  ("Art. 37 CDC", "publicidade enganosa"),
        "saude_plano":          ("Art. 3 CDC",  "negativa de cobertura"),
        "servico_com_problema": ("Art. 20 CDC", "serviço mal executado"),
        "voo_transporte":       ("Art. 14 CDC", "falha na prestação do serviço"),
    }
    return mapa.get(intencao, ("Art. 6 CDC", "violação dos direitos do consumidor"))

def gerar_reclamacao(contexto, historico, mensagem_usuario):
    """Gera prompt para o LLM criar texto formal de reclamação."""
    caso   = contexto.get("caso", {})
    intencao = contexto.get("ultima_intencao", "desconhecida")
    artigo, motivo = _artigo_aplicavel(intencao)
    hoje = datetime.date.today().strftime("%d/%m/%Y")

    # Extrai informações do histórico para complementar
    info_adicional = []
    for item in (historico or [])[-8:]:
        u = item.get("usuario","")
        if u and len(u) > 20:
            info_adicional.append(u[:200])

    contexto_str = ""
    if caso.get("empresa"):     contexto_str += f"Empresa/Fornecedor: {caso['empresa']}\n"
    if caso.get("objeto"):      contexto_str += f"Produto/Serviço: {caso['objeto']}\n"
    if caso.get("valor"):       contexto_str += f"Valor envolvido: {caso['valor']}\n"
    if caso.get("data_evento"): contexto_str += f"Data do ocorrido: {caso['data_evento']}\n"
    if caso.get("canal"):       contexto_str += f"Canal de compra: {caso['canal']}\n"
    if caso.get("problema"):    contexto_str += f"Problema: {caso['problema']}\n"

    conversa_resumo = "\n".join(f"- {m}" for m in info_adicional) if info_adicional else "Informações da conversa anterior."

    return f"""Gere um texto formal de reclamação com base nas informações abaixo.

INFORMAÇÕES DO CASO:
{contexto_str or "Extraia as informações disponíveis da conversa."}

CONTEXTO DA CONVERSA:
{conversa_resumo}

PEDIDO DO USUÁRIO: {mensagem_usuario}

INSTRUÇÕES PARA O TEXTO:
- Escreva em português formal, tom firme mas respeitoso
- Estrutura: Identificação do problema → Fatos → Base legal → Pedido concreto
- Cite o {artigo} (motivo: {motivo})
- Mencione que pode recorrer ao Procon, consumidor.gov.br ou Juizado Especial se necessário
- Data: {hoje}
- Deixe espaços para: [NOME COMPLETO], [CPF], [ENDEREÇO], [E-MAIL], [TELEFONE]
- Máximo 3 parágrafos objetivos
- Ao final, inclua linha para assinatura

Gere APENAS o texto da reclamação, sem explicações adicionais."""

def montar_prompt_reclamacao(contexto, historico, mensagem_usuario):
    """Retorna (é_reclamação, prompt_para_llm)"""
    if not _detectar_intencao_reclamacao(mensagem_usuario):
        return False, None
    prompt = gerar_reclamacao(contexto, historico, mensagem_usuario)
    return True, prompt
