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

