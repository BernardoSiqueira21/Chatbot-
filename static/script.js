// ===== CONSTANTS =====
const STORAGE_KEY   = "cbot_historico_v2";
const NOME_KEY      = "cbot_nome_atendente";
const THEME_KEY     = "cbot_theme";

const NOMES = [
    "Marina", "Camila", "Juliana", "Fernanda", "Patricia",
    "Amanda", "Beatriz", "Larissa", "Gabriela", "Aline",
    "Carolina", "Natalia", "Renata", "Bianca", "Vanessa"
];

const SAUDACOES = [
    "Olá! Sou {nome} e vou te orientar sobre questões do Código de Defesa do Consumidor. Me conta o que aconteceu.",
    "Oi! Aqui é a {nome}. Pode me descrever o seu caso com calma — eu acompanho cada detalhe.",
    "Olá! Sou a {nome}. Estou aqui para te ajudar a entender seus direitos como consumidor. O que aconteceu?",
    "Oi, tudo bem? Sou a {nome}. Me explica o que está acontecendo no seu caso que eu te oriento por partes.",
    "Olá! Sou a {nome}. Me diz com suas palavras o que aconteceu — pode ser breve mesmo, depois a gente detalha.",
];

// ===== DOM =====
const chatBox    = document.getElementById("chat-box");
const userInput  = document.getElementById("user-input");
const sendBtn    = document.getElementById("send-button");
const clearBtn   = document.getElementById("clear-button");
const agentName  = document.getElementById("agent-name");

// ===== THEME =====
function getTheme() {
    return localStorage.getItem(THEME_KEY) || "light";
}

function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem(THEME_KEY, theme);
}

function toggleTheme() {
    const current = getTheme();
    applyTheme(current === "light" ? "dark" : "light");
}

applyTheme(getTheme());

// ===== AGENT =====
function getNome() {
    let n = localStorage.getItem(NOME_KEY);
    if (!n) {
        n = NOMES[Math.floor(Math.random() * NOMES.length)];
        localStorage.setItem(NOME_KEY, n);
    }
    return n;
}

function getSaudacao() {
    const s = SAUDACOES[Math.floor(Math.random() * SAUDACOES.length)];
    return s.replace("{nome}", getNome());
}

// ===== HELPERS =====
function scrollBottom(smooth = true) {
    chatBox.scrollTo({ top: chatBox.scrollHeight, behavior: smooth ? "smooth" : "instant" });
}

function saveHistory() {
    try { localStorage.setItem(STORAGE_KEY, chatBox.innerHTML); } catch(e) {}
}

function formatTime() {
    return new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
}

// ===== AVATAR =====
function makeBotAvatar() {
    const d = document.createElement("div");
    d.className = "msg-avatar bot-avatar";
    d.textContent = getNome().charAt(0);
    return d;
}

function makeUserAvatar() {
    const d = document.createElement("div");
    d.className = "msg-avatar user-avatar";
    d.textContent = "Eu";
    return d;
}

// ===== MESSAGE BUILDER =====
function makeMessageGroup(text, type) {
    const group = document.createElement("div");
    group.className = `message-group ${type}`;

    const avatar = type === "bot" ? makeBotAvatar() : makeUserAvatar();

    const body = document.createElement("div");
    body.className = "msg-body";

    const author = document.createElement("div");
    author.className = "msg-author";
    author.textContent = type === "bot" ? getNome() : "Você";

    const bubble = document.createElement("div");
    bubble.className = `bubble ${type}-bubble`;
    bubble.innerHTML = text.replace(/\n/g, "<br>");

    body.appendChild(author);
    body.appendChild(bubble);
    group.appendChild(avatar);
    group.appendChild(body);
    return group;
}

// ===== CHIPS =====
function makeChipsSection(items, type, title) {
    if (!items || items.length === 0) return null;

    const section = document.createElement("div");
    section.className = "chips-section";

    const label = document.createElement("div");
    label.className = "chips-title";
    label.textContent = title;
    section.appendChild(label);

    const row = document.createElement("div");
    row.className = "chips-row";

    items.forEach(item => {
        const texto = typeof item === "string" ? item : "Quero saber sobre " + item.label;
        const btn = document.createElement("button");
        btn.className = `chip ${type === "question" ? "chip-question" : "chip-topic"}`;
        btn.textContent = typeof item === "string" ? item : item.label;
        btn.dataset.texto = texto;
        btn.type = "button";
        btn.onclick = () => usarExemplo(texto);
        row.appendChild(btn);
    });

    section.appendChild(row);
    return section;
}

function reconectarChips() {
    chatBox.querySelectorAll(".chip[data-texto]").forEach(chip => {
        chip.onclick = () => usarExemplo(chip.dataset.texto);
    });
}

// ===== TYPING INDICATOR =====
function showTyping() {
    const group = document.createElement("div");
    group.className = "message-group bot";
    group.id = "typing-indicator";

    const avatar = makeBotAvatar();

    const body = document.createElement("div");
    body.className = "msg-body";

    const bubble = document.createElement("div");
    bubble.className = "bubble bot-bubble typing-indicator";
    bubble.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';

    body.appendChild(bubble);
    group.appendChild(avatar);
    group.appendChild(body);
    chatBox.appendChild(group);
    scrollBottom();
}

