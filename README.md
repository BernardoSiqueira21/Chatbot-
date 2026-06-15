# ConsumidorBot — Chatbot de Defesa do Consumidor com Arquitetura Híbrida

**Trabalho Final — Inteligência Artificial e Machine Learning**
**UniAcademia — Centro Universitário | 7º Período**

**Autores:** Bernardo Siqueira, Lucas Barra, Lucas Mello, Mateus Ramos e Thiago Prata
**Professor:** Tassio Ferenzini Martins Sirqueira

---

## Sobre o Projeto

Chatbot especializado em orientações sobre o **Código de Defesa do Consumidor (CDC — Lei nº 8.078/1990)**.

A arquitetura híbrida combina:

- **NLTK** para pré-processamento e classificação de intenções (tokenização, stemming, remoção de stopwords)
- **Base de conhecimento estruturada** (JSON) com intenções curadas, palavras-chave e respostas verificadas
- **LLM open-source** (LLaMA via Groq) como mecanismo de *fallback* para perguntas não cobertas pela base

A proposta equilibra **confiabilidade** (respostas da base são rastreáveis e verificadas) com **cobertura** (o LLM garante que o usuário raramente fique sem resposta).

---

## Fluxo de Decisão

```
Usuário envia mensagem
        |
   [Pipeline PLN — NLTK]
   Tokenização → RSLPStemmer → Remoção de Stopwords
        |
   Pontuação de Intenção (similaridade léxica)
   Normalizada por √(nº de palavras-chave)
        |
   Score >= LIMIAR_CONFIANÇA?
   /              \
 SIM              NÃO
  |                |
Resposta         [LLM Fallback]
da Base          LLaMA (llama-3.1-70b-versatile)
(JSON curado)    via Groq API
        \              /
         Resposta ao usuário
         (+ indicação de origem: base | llm)
```

---

## Estrutura do Projeto

```
consumidorbot/
├── app.py                      # Flask: rotas REST e orquestração da lógica
├── requirements.txt
├── .env.example                # Configuração de variáveis de ambiente
├── chatbot/
│   ├── __init__.py
│   ├── agent.py                # Lógica central: roteamento KB → LLM
│   ├── nlp.py                  # Pipeline PLN com NLTK (tokenização, stemming, stopwords)
│   ├── llm.py                  # Integração com Groq (LLaMA)
│   ├── memory.py               # Histórico e contexto conversacional
│   ├── intents.json            # Base de intenções com palavras-chave e respostas curadas
│   └── knowledge_base.json     # Base estruturada: artigos do CDC, fluxos, órgãos
├── static/
│   ├── script.js               # Front-end com badge de origem (base/LLM) e estatísticas
│   └── style.css
└── templates/
    └── index.html
```

---

## Instalação e Uso

```bash
# 1. Clone o repositório e instale as dependências
pip install -r requirements.txt

# 2. Configure a chave da API do Groq
cp .env.example .env
# Edite .env e adicione sua GROQ_API_KEY

# 3. Execute
python app.py

# Acesse: http://localhost:5000
```

---

## Modelo LLM

| Atributo       | Valor                            |
|----------------|----------------------------------|
| **Modelo**     | `llama-3.1-70b-versatile`        |
| **Plataforma** | [Groq](https://groq.com)         |
| **Temperatura**| 0.3                              |
| **Max tokens** | 256                              |

**Justificativa da escolha:**

- Modelo aberto, sem dependência de provedores proprietários
- Excelente relação qualidade/parâmetros, superando modelos maiores em diversos benchmarks
- Já alinhado para seguir instruções (instruction tuning + RLHF), dispensando ajustes adicionais
- Acesso via Groq com latência competitiva para inferência remota

---

## API — Rotas REST

| Método | Rota          | Função                                        |
|--------|---------------|-----------------------------------------------|
| GET    | `/`           | Serve a interface de conversação              |
| POST   | `/chat`       | Recebe a mensagem e devolve resposta + origem |
| GET    | `/interacoes` | Lista as intenções disponíveis na base        |
| GET    | `/health`     | Verifica disponibilidade do serviço           |
| POST   | `/reset`      | Limpa o histórico da conversa                 |
| GET    | `/historico`  | Retorna o histórico da sessão                 |
| GET    | `/stats`      | Métricas de uso (respostas por origem)        |
| POST   | `/feedback`   | Registra avaliação do usuário sobre a resposta|

---

## Métricas de Desempenho

| Indicador                   | Valor         |
|-----------------------------|---------------|
| Respostas resolvidas pela base | ~60%       |
| Respostas via LLM (fallback)   | ~40%       |
| Tempo médio — base          | < 50 ms       |
| Tempo médio — LLM (Groq)    | ~40 s         |
| Rotas REST expostas         | 8             |

---

## Tecnologias de PLN Utilizadas

| Técnica                   | Biblioteca / Implementação | Uso                                        |
|---------------------------|----------------------------|--------------------------------------------|
| Tokenização               | NLTK `word_tokenize`       | Segmenta o texto em tokens                 |
| Stemming                  | NLTK `RSLPStemmer`         | Reduz palavras ao radical em português     |
| Remoção de stopwords      | NLTK corpus (`pt-BR`)      | Descarta termos sem valor semântico        |
| Pontuação de intenção     | Implementação própria      | Similaridade léxica normalizada por √(n)  |
| Geração de linguagem      | Transformer (LLaMA / Groq) | Respostas para perguntas fora da base      |

---

## Stack Tecnológico

- **Flask** — backend e API REST
- **NLTK + RSLPStemmer** — processamento de linguagem natural em português
- **Groq API** — acesso ao modelo LLaMA para geração de linguagem
- **JSON** — base de conhecimento estruturada e versionável


> **Aviso:** Este projeto tem fins exclusivamente acadêmicos e educativos.
> As orientações fornecidas pelo ConsumidorBot **não substituem aconselhamento jurídico profissional**.
