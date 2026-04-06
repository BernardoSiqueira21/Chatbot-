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

function hideTyping() {
    const el = document.getElementById("typing-indicator");
    if (el) el.remove();
}

// ===== ADD MESSAGES =====
function addBotMessage(data) {
    const group = makeMessageGroup(data.resposta || "Entendi. Pode continuar.", "bot");
    chatBox.appendChild(group);

    if (data.dicas && data.dicas.length > 0) {
        const chips = makeChipsSection(data.dicas, "question", "Dúvidas comuns sobre este tema");
        if (chips) chatBox.appendChild(chips);
    }

    if (data.relacionados && data.relacionados.length > 0) {
        const chips = makeChipsSection(data.relacionados, "topic", "Temas relacionados");
        if (chips) chatBox.appendChild(chips);
    }

    scrollBottom();
    saveHistory();
}

function addUserMessage(text) {
    const group = makeMessageGroup(text, "user");
    chatBox.appendChild(group);
    scrollBottom();
    saveHistory();
}

// ===== INITIAL MESSAGE =====
function renderInitial() {
    chatBox.innerHTML = "";

    // Date divider
    const divider = document.createElement("div");
    divider.className = "date-divider";
    divider.innerHTML = `<span>Hoje, ${formatTime()}</span>`;
    chatBox.appendChild(divider);

    // Greeting
    const group = makeMessageGroup(getSaudacao(), "bot");
    chatBox.appendChild(group);

    // Initial chips
    const starterChips = [
        "Produto com defeito, e agora?",
        "Tive um problema com entrega",
        "Me cobraram um valor errado",
        "Quero cancelar uma compra online",
        "A loja não quer trocar",
        "Quero conhecer meus direitos",
    ];
    const chips = makeChipsSection(starterChips, "question", "Por onde quer começar?");
    if (chips) chatBox.appendChild(chips);

    scrollBottom(false);
    saveHistory();
}

function loadHistory() {
    try {
        const saved = localStorage.getItem(STORAGE_KEY);
        if (saved) {
            chatBox.innerHTML = saved;
            reconectarChips();
            scrollBottom(false);
        } else {
            renderInitial();
        }
    } catch(e) {
        renderInitial();
    }
}

// ===== SEND =====
let sending = false;

async function sendMessage() {
    if (sending) return;
    const msg = (userInput.value || "").trim();
    if (!msg) return;

    sending = true;
    sendBtn.disabled = true;

    addUserMessage(msg);
    userInput.value = "";
    userInput.focus();

    // Human-like delay: random between 600ms and 1400ms
    const delay = 600 + Math.random() * 800;
    await new Promise(r => setTimeout(r, 250));
    showTyping();
    await new Promise(r => setTimeout(r, delay));

    try {
        const res = await fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ mensagem: msg })
        });

        let data;
        try { data = await res.json(); }
        catch(e) { data = { resposta: "Desculpe, houve um problema ao processar. Pode tentar novamente?" }; }

        hideTyping();

        if (data && data.resposta) {
            addBotMessage(data);
        } else {
            addBotMessage({ resposta: "Desculpe, ocorreu um erro. Pode tentar novamente?" });
        }
    } catch(err) {
        hideTyping();
        addBotMessage({ resposta: "Não foi possível conectar. Verifique sua conexão e tente novamente." });
    } finally {
        sending = false;
        sendBtn.disabled = false;
    }
}

function usarExemplo(text) {
    if (!text || sending) return;
    userInput.value = text;
    sendMessage();
}

// ===== CLEAR =====
function clearChat() {
    fetch("/reset", { method: "POST" }).catch(() => {});
    localStorage.removeItem(STORAGE_KEY);
    localStorage.removeItem(NOME_KEY);
    if (agentName) agentName.textContent = getNome() + " · Atendente virtual";
    renderInitial();
}

// ===== EVENTS =====
sendBtn.addEventListener("click", sendMessage);
clearBtn.addEventListener("click", clearChat);

userInput.addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// ===== INIT =====
window.addEventListener("load", () => {
    if (agentName) agentName.textContent = getNome() + " · Atendente virtual";
    loadHistory();
});
