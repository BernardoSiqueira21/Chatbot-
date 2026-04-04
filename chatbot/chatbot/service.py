import random
from chatbot.nlp import identificar_intencao, INTENTS_DB
from chatbot.memory import (
    obter_ultima_intencao,
    obter_ultima_mensagem_usuario,
    obter_ultimas_intencoes,
    contar_intencao_no_historico,
    atualizar_contexto,
    obter_temas_visitados,
    detectar_tom_usuario,
)

# Aberturas variadas para soar mais humano
ABERTURAS_HUMANAS = [
    "Entendi.",
    "Certo.",
    "Faz sentido.",
    "Agora ficou mais claro.",
    "Estou acompanhando.",
    "Perfeito.",
    "Entendi o ponto principal.",
    "Compreendido.",
    "Ok.",
    "Sim, esse tipo de situação acontece bastante.",
    "Consigo acompanhar o que aconteceu.",
    "Certo, vou continuar por esse ponto.",
    "",
    "",
    "",
]

ABERTURAS_FRUSTRACAO = [
    "Entendo sua frustração — é completamente compreensível se sentir assim nessa situação.",
    "Pelo que você descreveu, foi mesmo uma experiência bem desgastante.",
    "Faz todo sentido ficar incomodado com isso.",
    "Imagino que essa situação esteja sendo bastante cansativa.",
    "É uma situação realmente incômoda.",
    "Dá para entender o incômodo com isso.",
]

ABERTURAS_URGENCIA = [
    "Entendido. Vou direto ao que você precisa saber.",
    "Certo, vamos focar no essencial.",
    "Sem enrolação — o que é mais importante agora:",
    "Entendi a urgência.",
]

TRANSICOES_CONTEXTO = [
    "Ainda nesse ponto,",
    "Continuando,",
    "Pensando no que você disse,",
    "Dentro desse mesmo assunto,",
    "Levando isso em conta,",
    "Seguindo esse raciocínio,",
    "Com base no que você me contou,",
    "Aprofundando nisso,",
    "Complementando o que falamos,",
]

RETOMADAS_LONGA_CONVERSA = [
    "Já percorremos bastante terreno nesse caso. Se quiser, posso resumir o que vimos ou mudar o foco para outro ponto.",
    "Estamos avançando bem. Quer que eu consolide o que foi dito ou prefere continuar por esse caminho?",
    "Passamos por vários ângulos desse caso. Posso continuar nesse ponto ou mudar o foco se precisar.",
    "Já abordamos muita coisa. Se precisar, posso reforçar algum ponto ou abrirmos um tema diferente.",
]

RESPOSTAS_NAO_ENTENDEU = [
    "Não consegui entender direito. Pode descrever com mais detalhes o que aconteceu?",
    "Não ficou totalmente claro. Me conta com mais calma o que está acontecendo no seu caso.",
    "Hmm, não acompanhei bem. Tenta descrever o problema com suas próprias palavras.",
    "Pode reformular? Não consegui entender bem. Qualquer detalhe já ajuda.",
    "Não entendi direito. Me diz em poucas palavras: qual é o problema principal?",
    "Não acompanhei totalmente. Pode me dar mais contexto? Por exemplo: o que foi comprado, o que aconteceu de errado.",
]

GATILHOS_CONTINUIDADE = [
    "continue", "continua", "continuar", "continue por favor", "pode continuar",
    "quero sim", "quero", "me explica", "me explica isso", "explique isso",
    "quero saber", "quero entender melhor", "fale mais", "me diga mais",
    "como seria isso", "o que fazer", "como fazer", "e se", "mas e",
    "nesse caso", "e agora", "isso muda", "me mostra", "me mostre",
    "aprofunda", "aprofundar", "pode aprofundar", "segue", "siga",
    "vai por esse caminho", "me fala disso", "qual seria",
    "quero a dica", "me da a dica", "me de a dica",
    "opcao 1", "opcao 2", "opcao 3",
    "sim", "claro", "pode ser", "vamos", "ok", "certo", "beleza",
    "ta", "tá", "tá bom", "entendido", "combinado", "vai",
    "me conta mais", "conta mais", "pode continuar", "sigo", "segue",
    "e ai", "e aí", "continua", "prossiga", "vai em frente",
]

GATILHOS_MUDANCA_TEMA = [
    "agora outra coisa", "mudando de assunto", "outro tema",
    "outra duvida", "tenho outra pergunta",
    "quero falar de outro caso", "novo caso", "vamos para outro assunto",
    "quero mudar de assunto", "outro problema", "outra situacao",
    "novo tema", "muda o assunto", "tenho outra questao",
    "quero perguntar outra coisa", "posso perguntar outra coisa",
]

ROTULOS_TEMAS = {
    "reembolso": "reembolso",
    "sac": "atendimento e protocolo",
    "prova_documental": "provas e documentos",
    "produto_nao_entregue": "produto não entregue",
    "empresa_negou_solucao": "empresa negou solução",
    "garantia": "garantia e defeito",
    "troca": "troca do produto",
    "cancelamento": "cancelamento",
    "compra_online": "compra online",
    "atraso_entrega": "atraso na entrega",
    "cobranca_indevida": "cobrança indevida",
    "nota_fiscal": "nota fiscal",
    "defeito_apos_uso": "defeito após uso",
    "produto_diferente": "produto diferente do anunciado",
    "servico_com_problema": "serviço com problema",
    "arrependimento": "arrependimento na compra",
    "orientacao_geral": "orientação geral",
    "direito_basico": "direitos do consumidor",
    "procon": "Procon e órgãos de defesa",
    "assinatura_plano": "assinatura e planos",
    "tempo_prazo": "prazos legais",
    "propaganda_enganosa": "propaganda enganosa",
    "loja_fisica": "compra em loja física",
    "juizado_especial": "Juizado Especial",
    "frete_entrega": "frete e logística",
    "cartao_credito": "cartão de crédito",
    "pix_transferencia": "Pix e transferências",
    "voo_transporte": "voos e transporte",
    "saude_plano": "plano de saúde",
    "consumidor_gov": "consumidor.gov.br e plataformas",
    "contrato_clausula_abusiva": "cláusulas abusivas em contrato",
}

RELACIONADOS = {
    "cobranca_indevida": ["reembolso", "sac", "prova_documental"],
    "atraso_entrega": ["produto_nao_entregue", "prova_documental", "sac"],
    "produto_nao_entregue": ["atraso_entrega", "prova_documental", "sac"],
    "garantia": ["troca", "nota_fiscal", "empresa_negou_solucao"],
    "troca": ["garantia", "nota_fiscal", "empresa_negou_solucao"],
    "arrependimento": ["cancelamento", "reembolso", "compra_online"],
    "reembolso": ["cancelamento", "cobranca_indevida", "sac"],
    "nota_fiscal": ["prova_documental", "garantia", "troca"],
    "orientacao_geral": ["garantia", "atraso_entrega", "cobranca_indevida"],
    "direito_basico": ["garantia", "arrependimento", "cobranca_indevida"],
    "propaganda_enganosa": ["produto_diferente", "reembolso", "empresa_negou_solucao"],
    "servico_com_problema": ["sac", "empresa_negou_solucao", "reembolso"],
    "assinatura_plano": ["cancelamento", "cobranca_indevida", "reembolso"],
    "procon": ["sac", "empresa_negou_solucao", "prova_documental"],
    "compra_online": ["arrependimento", "produto_nao_entregue", "atraso_entrega"],
    "loja_fisica": ["troca", "garantia", "nota_fiscal"],
    "juizado_especial": ["procon", "empresa_negou_solucao", "prova_documental"],
    "frete_entrega": ["arrependimento", "produto_diferente", "reembolso"],
    "cartao_credito": ["cobranca_indevida", "reembolso", "sac"],
    "pix_transferencia": ["reembolso", "cobranca_indevida", "prova_documental"],
    "voo_transporte": ["reembolso", "empresa_negou_solucao", "prova_documental"],
    "saude_plano": ["cancelamento", "empresa_negou_solucao", "prova_documental"],
    "consumidor_gov": ["procon", "empresa_negou_solucao", "sac"],
    "contrato_clausula_abusiva": ["cancelamento", "empresa_negou_solucao", "direito_basico"],
}

DUVIDAS_COMUNS = {
    "cobranca_indevida": [
        "O que fazer se a empresa continuar cobrando?",
        "Quais provas eu devo guardar?",
        "E se eu já tiver pago esse valor?",
        "Como pedir o estorno de uma cobrança?",
    ],
    "atraso_entrega": [
        "O que muda se a empresa prometer um novo prazo?",
        "Quais provas devo guardar nesse caso?",
        "E se o sistema disser que foi entregue, mas eu não recebi?",
        "Posso cancelar o pedido por causa do atraso?",
    ],
    "produto_nao_entregue": [
        "Quais provas ajudam mais quando o produto não chega?",
        "E se constar como entregue, mas eu não recebi?",
        "O que fazer se a empresa jogar a culpa na transportadora?",
        "Tenho direito ao reembolso completo?",
    ],
    "garantia": [
        "O que fazer se a empresa negar solução?",
        "Quais provas ajudam mais nesse tipo de defeito?",
        "E se o problema apareceu depois de alguns dias?",
        "Tenho direito a produto novo ou só ao conserto?",
    ],
    "troca": [
        "O que fazer se a loja negar a troca?",
        "O que muda quando existe defeito?",
        "A nota fiscal ajuda nesse caso?",
        "E se o produto foi comprado em promoção?",
    ],
    "reembolso": [
        "O que fazer se a empresa demorar para devolver o valor?",
        "Quais documentos ajudam no pedido de reembolso?",
        "Como isso se conecta com cancelamento?",
        "Posso pedir reembolso em dinheiro mesmo pagando em cartão?",
    ],
    "arrependimento": [
        "Qual é o prazo para me arrepender de uma compra online?",
        "E se a loja se negar a aceitar a devolução?",
        "Preciso pagar o frete para devolver?",
        "E se o produto já foi aberto?",
    ],
    "cancelamento": [
        "A empresa pode cobrar multa por cancelamento?",
        "Qual o prazo para devolver o dinheiro?",
        "E se for uma assinatura com fidelidade?",
        "Como fazer o cancelamento formalmente?",
    ],
    "empresa_negou_solucao": [
        "O que fazer depois que a empresa nega?",
        "Quais órgãos posso acionar?",
        "Como o histórico de atendimento ajuda nesse caso?",
        "Posso ir direto ao Procon?",
    ],
    "sac": [
        "Como registrar um protocolo de forma correta?",
        "O que fazer se o SAC não resolver?",
        "Quanto tempo a empresa tem para responder?",
        "Devo preferir atendimento escrito ou por telefone?",
    ],
    "prova_documental": [
        "Quais documentos são mais importantes?",
        "Print de conversa serve como prova?",
        "E se eu não tiver nota fiscal?",
        "Como organizar as provas para um registro formal?",
    ],
    "nota_fiscal": [
        "Posso exigir nota fiscal em qualquer compra?",
        "E se a loja se negar a emitir nota?",
        "Como a nota fiscal ajuda no caso de defeito?",
        "Extrato bancário substitui a nota fiscal?",
    ],
    "compra_online": [
        "Qual é o prazo de arrependimento em compras pela internet?",
        "O que fazer se o site não entregar o produto?",
        "E se o produto chegar diferente do anunciado?",
        "Como identificar um vendedor confiável em marketplace?",
    ],
    "procon": [
        "Como abrir uma reclamação no Procon?",
        "O Procon pode obrigar a empresa a resolver?",
        "Qual a diferença entre Procon e consumidor.gov.br?",
        "Preciso ir pessoalmente ou posso fazer online?",
    ],
    "orientacao_geral": [
        "Quais são os problemas de consumo mais comuns?",
        "Quais provas costumam ser mais importantes?",
        "Por onde devo começar quando tenho um problema?",
        "Como saber qual é o tema principal do meu caso?",
    ],
    "propaganda_enganosa": [
        "O produto chegou diferente do anunciado. O que fazer?",
        "Quais provas devo guardar nesse caso?",
        "Posso pedir reembolso por propaganda enganosa?",
        "Onde posso denunciar propaganda enganosa?",
    ],
    "assinatura_plano": [
        "Posso cancelar uma assinatura a qualquer momento?",
        "A empresa pode cobrar multa por cancelamento antecipado?",
        "E se o plano mudou sem aviso prévio?",
        "Como fazer o cancelamento formalmente?",
    ],
    "servico_com_problema": [
        "O serviço foi feito de forma errada. O que fazer?",
        "Posso pedir reembolso se o serviço não foi prestado?",
        "A empresa tem prazo para corrigir o serviço?",
        "Como documentar o problema com um serviço?",
    ],
    "defeito_apos_uso": [
        "Quanto tempo tenho para reclamar de um defeito?",
        "E se a empresa disser que fui eu que estraguei?",
        "Quais provas ajudam nesse tipo de caso?",
        "A garantia cobre defeito que apareceu depois de algum uso?",
    ],
    "produto_diferente": [
        "O produto é diferente do que foi anunciado. O que fazer?",
        "Posso recusar o recebimento?",
        "A empresa é obrigada a trocar?",
        "E se eu já tiver assinado o recebimento?",
    ],
    "direito_basico": [
        "Quais são meus direitos básicos como consumidor?",
        "O que é o Código de Defesa do Consumidor?",
        "Quais órgãos protegem o consumidor no Brasil?",
        "O que posso fazer antes de ir ao Procon?",
    ],
    "loja_fisica": [
        "Loja física é obrigada a trocar um produto?",
        "Quais são as regras de troca em loja física?",
        "E se a política de troca da loja for diferente da lei?",
        "Como guardar provas de uma compra presencial?",
    ],
    "tempo_prazo": [
        "Qual o prazo para reclamar de um produto?",
        "O prazo de garantia pode ser estendido?",
        "O que é prescrição no direito do consumidor?",
        "Como o prazo muda conforme o tipo de produto?",
    ],
    "juizado_especial": [
        "Preciso de advogado no Juizado Especial?",
        "Qual o valor máximo para ir ao Juizado Especial sem advogado?",
        "Posso pedir dano moral?",
        "Como organizar os documentos para o Juizado?",
    ],
    "frete_entrega": [
        "Quem paga o frete de devolução?",
        "O frete pode ser cobrado diferente do anunciado?",
        "E se o frete não foi entregue no prazo?",
        "Posso recusar o produto na entrega?",
    ],
    "cartao_credito": [
        "Como fazer chargeback?",
        "Quanto tempo demora o estorno no cartão?",
        "Posso contestar uma compra parcelada?",
        "A operadora do cartão pode ajudar?",
    ],
    "saude_plano": [
        "O plano pode negar um procedimento do Rol da ANS?",
        "Como contestar uma negativa do plano?",
        "O que fazer em negativas de emergência?",
        "Qual é o papel da ANS?",
    ],
}

OFERTAS_POR_INTENCAO = {
    "garantia": [
        "Posso continuar nesse ponto ou mudar para provas, troca ou resposta da empresa.",
        "Se quiser, posso aprofundar esse caso ou focar em documentos e próximos passos.",
    ],
    "troca": [
        "Posso continuar na troca ou ligar isso a defeito, nota fiscal ou negativa da loja.",
        "Se quiser, posso seguir por esse ponto ou mudar para prova da compra.",
    ],
    "atraso_entrega": [
        "Posso continuar nesse atraso ou mudar para rastreio, provas ou produto não entregue.",
        "Se quiser, posso aprofundar ou seguir por outro ponto ligado a prazo ou atendimento.",
    ],
    "produto_nao_entregue": [
        "Posso continuar nesse caso ou mudar para provas, transportadora ou atendimento da empresa.",
        "Se quiser, posso seguir por esse tema ou puxar um ponto relacionado.",
    ],
    "cobranca_indevida": [
        "Posso continuar nessa cobrança ou mudar para reembolso, provas ou resposta da empresa.",
        "Se quiser, posso aprofundar esse caso ou seguir para outro ponto.",
    ],
    "arrependimento": [
        "Posso continuar nesse ponto ou mudar para cancelamento, compra online ou reembolso.",
        "Se quiser, posso seguir por esse caminho ou abrir outro lado do caso.",
    ],
    "reembolso": [
        "Posso continuar nesse reembolso ou mudar para cancelamento, cobrança ou documentos.",
        "Se quiser, posso aprofundar esse ponto ou seguir para outro tema relacionado.",
    ],
    "orientacao_geral": [
        "Posso continuar de forma geral ou focar em um problema específico como defeito, entrega, cobrança ou cancelamento.",
        "Se quiser, posso sair dessa visão mais ampla e entrar em um caso concreto.",
    ],
    "direito_basico": [
        "Posso continuar na visão geral dos direitos ou aplicar isso a um caso específico.",
        "Se quiser, posso transformar isso em exemplos práticos.",
    ],
    "mudanca_tema": [
        "Pode me contar o novo caso que eu sigo por esse outro assunto.",
        "Me diga o novo problema.",
    ],
    "procon": [
        "Posso continuar sobre o Procon ou voltar ao problema principal.",
        "Se quiser, posso detalhar como funciona o processo ou seguir para outro tema.",
    ],
    "sac": [
        "Posso continuar sobre protocolo e atendimento ou mudar para Procon ou próximos passos.",
        "Se quiser, posso aprofundar como usar o atendimento a seu favor.",
    ],
    "empresa_negou_solucao": [
        "Posso continuar sobre o que fazer após uma negativa ou mudar para provas e Procon.",
        "Se quiser, posso detalhar os próximos passos concretos.",
    ],
    "juizado_especial": [
        "Posso continuar sobre o Juizado ou voltar para o Procon e consumidor.gov.br.",
        "Se quiser, posso explicar como organizar os documentos para o Juizado.",
    ],
    "cartao_credito": [
        "Posso continuar sobre o cartão ou mudar para o que fazer com a empresa.",
        "Se quiser, posso explicar como funciona o chargeback com mais detalhe.",
    ],
    "frete_entrega": [
        "Posso continuar sobre o frete ou passar para a parte de reembolso e devolução.",
        "Se quiser, posso seguir por esse ponto ou abrir outro tema.",
    ],
}


def buscar_item_por_tag(tag):
    try:
        for item in INTENTS_DB.get("intents", []):
            if item.get("tag") == tag:
                return item
    except Exception:
        pass
    return None


def eh_pergunta_de_continuidade(mensagem):
    try:
        msg = mensagem.lower().strip()
        return any(msg.startswith(g) or msg == g for g in GATILHOS_CONTINUIDADE)
    except Exception:
        return False


def eh_mudanca_de_tema(mensagem):
    try:
        msg = mensagem.lower().strip()
        return any(g in msg for g in GATILHOS_MUDANCA_TEMA)
    except Exception:
        return False


def mensagem_curta_dependente_de_contexto(mensagem):
    try:
        return len(mensagem.lower().strip().split()) <= 6
    except Exception:
        return False


def montar_abertura(intencao, historico, contexto):
    try:
        tom = contexto.get("tom", "neutro")
        if tom == "frustrado":
            return random.choice(ABERTURAS_FRUSTRACAO)
        if tom == "urgente":
            return random.choice(ABERTURAS_URGENCIA)
        repeticoes = contar_intencao_no_historico(historico, intencao)
        if repeticoes >= 2:
            return random.choice(TRANSICOES_CONTEXTO)
        return random.choice(ABERTURAS_HUMANAS)
    except Exception:
        return ""


def montar_relacionados_texto(intencao):
    try:
        relacionados = RELACIONADOS.get(intencao, [])
        if not relacionados:
            return None
        temas = [ROTULOS_TEMAS.get(tag, tag.replace("_", " ")) for tag in relacionados]
        return "Temas relacionados: " + ", ".join(temas) + "."
    except Exception:
        return None


def montar_duvidas_comuns(intencao):
    try:
        return list(DUVIDAS_COMUNS.get(intencao, []))
    except Exception:
        return []


