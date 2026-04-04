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

