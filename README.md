# Chatbot-
Trabalho de chat bot da matéria Inteligência Artificial e machine learning 
​Título do Projeto: Chatbot Educativo de Defesa do Consumidor

Descrição:

Este projeto consiste no desenvolvimento de um chatbot temático com interface web interativa, focado em orientar os usuários de forma prática sobre os direitos básicos do consumidor. Utilizando a biblioteca NLTK em Python para o Processamento de Linguagem Natural (PLN), o sistema é capaz de interpretar desabafos e dúvidas comuns do dia a dia , como problemas com garantias, atrasos em entregas, propagandas enganosas e o direito de arrependimento em compras online.
​A aplicação adota uma arquitetura moderna, com o back-end em Python atuando como uma API para processar a intenção da mensagem e o front-end garantindo uma experiência de conversa fluida no navegador. O objetivo principal é identificar as necessidades do usuário a partir da linguagem natural e entregar orientações claras e focadas na resolução do problema de consumo, mantendo a linguagem simples e acessível.

Grupo: Bernardo Souza Siqueira, Mateus Ramos Vieira, Lucas Barra Machado, Lucas Pereira Mello, Thiago Prata de Figueredo

# Chatbot Educativo de Defesa do Consumidor

Chatbot temático com interface web, baseado no **Código de Defesa do Consumidor (CDC — Lei 8.078/90)**.

Desenvolvido com **Python + Flask + NLTK**, com:
- Memória de contexto (suporta 40+ interações contínuas)
- NLP com tokenização, stemming, stopwords e identificação de intenções
- Base de conhecimento ampla (18+ intenções cobrindo direitos do CDC)
- Interface web responsiva e moderna
- Respostas contextuais baseadas na última interação

---

## Estrutura do Projeto

```
chatbot_consumidor/
├── app.py                  # Servidor Flask
├── requirements.txt        # Dependências
├── README.md
├── chatbot/
│   ├── __init__.py
│   ├── intents.json        # Base de conhecimento
│   ├── nlp.py              # Processamento de Linguagem Natural (NLTK)
│   ├── memory.py           # Gestão de contexto e memória
│   └── service.py          # Lógica de resposta
├── templates/
│   └── index.html          # Interface web
└── static/
    ├── style.css
    └── script.js
```

---

## Como Executar

### 1. Pré-requisitos
- Python 3.8 ou superior instalado
- pip disponível no terminal

### 2. Instalar dependências
```bash
pip install -r requirements.txt
```

### 3. Executar
```bash
python app.py
```

### 4. Acessar no navegador
```
http://127.0.0.1:5000
```

Os downloads do NLTK (punkt, stopwords, rslp) são feitos automaticamente na primeira execução.

---

## Funcionalidades

O chatbot cobre os seguintes temas:

| Intenção | Descrição |
|---|---|
| Garantia/Defeito | Produtos com defeito, garantia legal e contratual |
| Troca/Devolução | Direitos de troca e políticas comerciais |
| Atraso na Entrega | Direitos quando a entrega não chega no prazo |
| Arrependimento | Direito de cancelamento em compras online (7 dias) |
| Propaganda Enganosa | Publicidade falsa ou indutora ao erro |
| Cobrança Indevida | Cobranças duplicadas ou não autorizadas |
| SAC/Atendimento | Atendimento deficiente e formalização de reclamações |
| Procon/Juizado | Como e onde registrar reclamações formais |
| Serviço Não Prestado | Serviços incompletos ou não realizados |
| Contrato Abusivo | Cláusulas abusivas e nulidade pelo CDC |
| Produto Não Entregue | Produto extraviado ou nunca entregue |
| Plano de Saúde | Negativas de cobertura e ANS |
| Banco/Financeiro | Cobranças bancárias, fraudes e Bacen |
| Telefonia/Internet | Problemas com operadoras e Anatel |
| Venda Casada | Prática abusiva proibida pelo CDC |
| Dano Moral | Indenização por constrangimento |
| Negativação Indevida | SPC/Serasa indevido e direitos |
| Direitos Básicos | Resumo do CDC e direitos fundamentais |

---

## Uso do NLTK

O sistema utiliza:
- `word_tokenize` com idioma português para tokenização
- `stopwords` em português para remoção de palavras irrelevantes
- `RSLPStemmer` para stemming (radicalização de palavras)
- Normalização com remoção de acentos via `unicodedata`

---

## Tecnologias

- **Python 3.8+**
- **Flask 3.0.2** — servidor web e API
- **NLTK 3.8.1** — processamento de linguagem natural
- **HTML5 + CSS3 + JavaScript** — interface web responsiva
