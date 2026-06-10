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
