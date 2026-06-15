# ConsumidorBot v2 — Chatbot de Direito do Consumidor com LLM

**Trabalho Final — Processamento de Linguagem Natural**  
Chatbot hibrido: Base de Conhecimento (NLTK) + LLM Fallback (Hugging Face)

---

## Sobre o Projeto

Chatbot especializado em orientacoes sobre o **Codigo de Defesa do Consumidor (CDC - Lei 8.078/1990)**.

A arquitetura hibrida combina:
- **NLTK** para classificacao de intencoes e pre-processamento de texto
- **Base de conhecimento estruturada** (JSON) com artigos do CDC, fluxos de acao e orgaos de defesa
- **LLM open-source** (Mistral-7B-Instruct via Hugging Face) como fallback para perguntas nao cobertas pela base

## Fluxo de Decisao

```
Usuario envia mensagem
        |
   [NLTK - NLP]
   Tokenizacao, Stemming (RSLP), Stopwords
        |
   Identificacao de intencao (intents.json)
        |
   Busca na Base de Conhecimento (knowledge_base.json)
        |
   Score KB >= 0.5?
   /          \
 SIM          NAO
  |            |
Responde     [LLM Fallback]
pela base    Mistral-7B-Instruct
             (Hugging Face API)
```

## Estrutura do Projeto

```
chatbot_final/
├── app.py                      # Flask: rotas /chat, /stats, /health
├── requirements.txt
├── .env.example                # Configuracao de variaveis de ambiente
├── chatbot/
│   ├── __init__.py
│   ├── agent.py               # Logica central do agente (KB → LLM)
│   ├── nlp.py                 # NLTK: tokenizacao, stemming, identificacao de intencao
│   ├── llm.py                 # Integracao com Hugging Face (Mistral-7B)
│   ├── memory.py              # Contexto e historico da conversa
│   ├── intents.json           # Base de padroes e respostas (>30 intencoes)
│   └── knowledge_base.json    # Base estruturada: artigos CDC, fluxos, orgaos
├── static/
│   ├── script.js              # Frontend com badge KB/LLM e stats
│   └── style.css
└── templates/
    └── index.html
```

## Instalacao e Uso

```bash
# 1. Clone e instale dependencias
pip install -r requirements.txt

# 2. Configure o token da Hugging Face (opcional mas recomendado)
cp .env.example .env
# Edite .env e adicione seu HF_TOKEN

# 3. Execute
python app.py
# Acesse: http://localhost:5000
```

## Modelo LLM

**Modelo:** `mistralai/Mistral-7B-Instruct-v0.2`  
**Plataforma:** https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.2  
**Acesso:** Hugging Face Inference API (gratuita com limites)

**Justificativa da escolha:**
- Modelo instrucional open-source de alta qualidade
- Bom desempenho em portugues
- Disponivel gratuitamente via HF Inference API
- Tamanho adequado (7B params): bom balanco qualidade/velocidade
- Formato de prompt padronizado ([INST])

## API Endpoints

| Rota | Metodo | Descricao |
|------|--------|-----------|
| `/` | GET | Interface web |
| `/chat` | POST | Processar mensagem |
| `/reset` | POST | Resetar sessao |
| `/stats` | GET | Estatisticas de uso |
| `/health` | GET | Status do LLM |

## Tecnologias

- **Flask** — servidor web
- **NLTK** — tokenizacao, stopwords, stemming (RSLPStemmer)
- **Hugging Face Inference API** — acesso ao LLM
- **JSON** — base de conhecimento estruturada

## Tecnologias NLP Utilizadas

| Tecnica | Biblioteca | Uso |
|---------|-----------|-----|
| Tokenizacao | NLTK RegexpTokenizer | Divide texto em tokens |
| Stopwords | NLTK corpus | Remove palavras irrelevantes |
| Stemming | NLTK RSLPStemmer | Reduz palavras ao radical (pt-BR) |
| Normalizacao Unicode | Python unicodedata | Remove acentos |
| Correspondencia semantica | Implementacao propria | Matching por stems |
| Transformers | Hugging Face | LLM para perguntas complexas |

---

*Projeto academico — orientacao educativa, nao substitui advogado.*
