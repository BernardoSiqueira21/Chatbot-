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

