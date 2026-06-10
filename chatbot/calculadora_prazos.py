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

