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

_CAMBIO_GENERICO = [
    "cambio","cotacao","quanto vale","valor da moeda","conversao","conversor",
]
_FINANCEIRO = [
    "selic","taxa selic","ipca","igpm","inpc","inflacao","inflação",
    "cdi","taxa cdi","rendimento poupanca","rendimento cdi",
    "salario minimo","salário mínimo","piso salarial","inss","bpc","auxilio brasil",
    "bolsa familia","imposto renda","irpf","fgts saque","fgts aniversario",
    "gasolina","combustivel","diesel","etanol","preço gasolina",
    "fipe","tabela fipe","preco fipe","valor fipe",
    "tarifa energia","aneel","bandeira tarifaria","conta de luz",
    "tarifa agua","conta agua",
]
_PALAVRAS_TEMPO = [
    "hoje","agora","atual","atualmente","este ano","esse ano","recente","ultimo",
    "2025","2026","2027","agora mesmo","no momento","esta semana","este mes",
    "ultimamente","acumulado","corrente","vigente",
]
_RECALL_ANVISA = [
    "recall","produto recolhido","retirada do mercado","anvisa recall",
    "alerta anvisa","recall carro","recall medicamento","recall alimento",
]

_OFF_SCOPE_BLOCKLIST = [
    "horoscopo","signo","tarot","numerologia","mapa astral","oraculo",
    "loteria","mega sena","quina","lotofacil","loteria federal","jogo do bicho",
    "bolao","aposta esportiva",
    "futebol","copa","mundial","olimpiada","campeonato","torneio","placar",
    "quem ganhou","time","jogador","artilheiro","libertadores","brasileirao",
    "nba","nfl","formula 1","f1","tenis","volei",
    "clima","tempo em","temperatura","previsao tempo","vai chover","vai nevar",
    "umidade","tempestade","sensacao termica","graus celsius","fahrenheit",
    "previsao do tempo",
    "que horas","fuso horario","hora em","hora atual","horas em","horas agora",
    "feriado","carnaval","natal data","pascoa","corpus christi","calendario",
    "guerra","conflito armado","tensao","tensão","geopolitica","sancao","embargo",
    "ucrania","russia","israel","gaza","hormuz","iran","china taiwan","coreia",
    "ultima hora","breaking news","noticias hoje","noticia geral","atualidade",
    "concurso publico","enem","vestibular","fuvest","unicamp","sisu","prouni",
    "fies","encceja","oab","tcc","monografia",
    "receita de","como cozinhar","como fazer bolo","drink","cocktail","dieta",
    "chatgpt","gpt","ia generativa","google bard","gemini","claude ai","llm",
    "programar","codigo python","javascript","linguagem programacao",
    "direito penal","direito de familia","divorcio","pensao alimenticia",
    "heranca","inventario","crime","prisao",
    "ouro preco","preço ouro","preco ouro","ouro hoje",
    "prata preco","preço prata","preco prata",
    "petroleo brent","petróleo brent","barril petroleo",
    "bitcoin","ethereum","cripto","cryptocurrency","blockchain","nft",
    "musica","filme","novela","serie","cantor","ator","ingresso show",
    "eleicao","presidente","deputado","partido","ideologia",
    "religiao","biblia","corao","oracao",
]
