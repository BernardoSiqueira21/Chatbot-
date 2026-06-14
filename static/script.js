// ===== CONSTANTS =====
const STORAGE_KEY   = "cbot_historico_minimal";
const NOME_KEY      = "cbot_nome_atendente";
const THEME_KEY     = "cbot_theme";

const NOMES = ["Marina", "Camila", "Juliana", "Fernanda", "Patricia"];
const SAUDACOES = [
    "Olá! Sou a {nome}. Como posso ajudar você com questões de Defesa do Consumidor hoje?",
    "Oi! Aqui é a {nome}. Me conte o seu problema para que eu possa orientá-lo.",
];

// ===== DOM =====
const chatBox   = document.getElementById("chat-box");
const userInput = document.getElementById("user-input");
const sendBtn   = document.getElementById("send-button");
const clearBtn  = document.getElementById("clear-button");
const agentName = document.getElementById("agent-name");

// ===== THEME =====
function getTheme() { return localStorage.getItem(THEME_KEY) || "light"; }
function applyTheme(t) { document.documentElement.setAttribute("data-theme", t); localStorage.setItem(THEME_KEY, t); }
function toggleTheme() { applyTheme(getTheme() === "light" ? "dark" : "light"); }
applyTheme(getTheme());

// ===== AGENT =====
function getNome() {
    let n = localStorage.getItem(NOME_KEY);
    if (!n) { n = NOMES[Math.floor(Math.random()*NOMES.length)]; localStorage.setItem(NOME_KEY, n); }
    return n;
}
function getSaudacao() { return SAUDACOES[Math.floor(Math.random()*SAUDACOES.length)].replace("{nome}", getNome()); }

// ===== HELPERS =====
function scrollBottom(smooth=true) { 
    chatBox.parentElement.scrollTo({top:chatBox.parentElement.scrollHeight, behavior:smooth?"smooth":"instant"}); 
}
function saveHistory() { try { localStorage.setItem(STORAGE_KEY, chatBox.innerHTML); } catch(e){} }

// ===== AVATAR =====
function makeBotAvatar() { 
    const d = document.createElement("div"); 
    d.className = "msg-avatar bot-avatar"; 
    d.textContent = getNome().charAt(0); 
    return d; 
}

// ===== BADGE KB / LLM / WEB / TIMESTAMP =====
function makeFonteBadge(data) {
    if (!data || !data.fonte || data.fonte === "sistema" || data.fonte === "anti_loop") return null;
    const badge = document.createElement("div");
    badge.className = "fonte-badge";

    let icone = "📚", rotulo = "Base", extra = "";

    if (data.usou_web) {
        icone = "🌐";
        rotulo = "Tempo real";
        if (data.dado_web && data.dado_web.confianca === "alta") extra = " ✓✓";
    } else if (data.fonte === "calculadora_prazos") {
        icone = "🗓️"; rotulo = "Calculadora";
    } else if (data.fonte === "gerador_reclamacao") {
        icone = "✍️"; rotulo = "Reclamação";
    } else if (data.usou_llm && !data.fonte.includes("base_conhecimento")) {
        icone = "⚡"; rotulo = "LLM";
    } else if (data.fonte.includes("base_conhecimento")) {
        icone = "📚"; rotulo = "Base CDC";
        if (data.kb_resultado && data.kb_resultado.artigo) {
            extra = ` · Art. ${data.kb_resultado.artigo}`;
        }
    }

    badge.textContent = `${icone} ${rotulo}${extra}`;

    if (data.timestamp) {
        const ts = document.createElement("span");
        ts.className = "badge-tempo";
        ts.textContent = data.timestamp.split(" ")[1] || data.timestamp;
        badge.appendChild(ts);
    }
    return badge;
}

// ===== MESSAGE BUILDER =====
function makeMessageGroup(text, type, data) {
    const group = document.createElement("div");
    group.className = `message-group ${type}`;
    
    if (type === "bot") group.appendChild(makeBotAvatar());
    
    const body = document.createElement("div");
    body.className = "msg-body";
    
    const bubble = document.createElement("div");
    bubble.className = `bubble ${type}-bubble`;
    
    // Contêiner de texto com suporte a colapso estrutural
    const bubbleText = document.createElement("div");
    bubbleText.className = "bubble-text";
    bubbleText.innerHTML = text.replace(/\*\*(.+?)\*\*/g,"<strong>$1</strong>").replace(/_(.+?)_/g,"<em>$1</em>").replace(/\n/g,"<br>");
    bubble.appendChild(bubbleText);

    // Regra dinâmina de colapso de texto longo (> 380 caracteres)
    if (text.length > 380) {
        bubbleText.classList.add("collapsed");
        const toggleBtn = document.createElement("button");
        toggleBtn.className = "toggle-expand-btn";
        toggleBtn.textContent = "... mostrar mais";
        toggleBtn.type = "button";
        toggleBtn.onclick = () => {
            if (bubbleText.classList.contains("collapsed")) {
                bubbleText.classList.remove("collapsed");
                toggleBtn.textContent = "Mostrar menos";
            } else {
                bubbleText.classList.add("collapsed");
                toggleBtn.textContent = "... mostrar mais";
            }
            scrollBottom(true);
        };
        bubble.appendChild(toggleBtn);
    }
    
    body.appendChild(bubble);
    
    // Barra inferior de ações (Badges + Copiar)
    const actionsRow = document.createElement("div");
    actionsRow.className = "msg-actions";
    
    if (type === "bot" && data) {
        const badge = makeFonteBadge(data);
        if (badge) actionsRow.appendChild(badge);
    }
    
    // Botão nativo de cópia rápida
    const copyBtn = document.createElement("button");
    copyBtn.className = "action-btn";
    copyBtn.type = "button";
    copyBtn.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg> <span>Copiar</span>`;
    copyBtn.onclick = () => {
        navigator.clipboard.writeText(text).then(() => {
            const txtSpan = copyBtn.querySelector("span");
            txtSpan.textContent = "Copiado!";
            setTimeout(() => { txtSpan.textContent = "Copiar"; }, 1800);
        }).catch(()=>{});
    };
    
    actionsRow.appendChild(copyBtn);
    body.appendChild(actionsRow);
    group.appendChild(body);
    
    return group;
}

// ===== CHIPS =====
function makeChipsSection(items) {
    if (!items || items.length === 0) return null;
    const section = document.createElement("div");
    section.className = "chips-section";
    
    items.forEach(item => {
        const texto = typeof item === "string" ? item : item.label;
        const btn = document.createElement("button");
        btn.className = "chip";
        btn.textContent = texto;
        btn.dataset.texto = typeof item === "string" ? item : "Quero saber sobre "+item.label;
        btn.type = "button";
        btn.onclick = () => usarExemplo(btn.dataset.texto);
        section.appendChild(btn);
    });
    return section;
}

function reconectarChips() { 
    chatBox.querySelectorAll(".chip").forEach(c => { c.onclick = () => usarExemplo(c.dataset.texto); }); 
    chatBox.querySelectorAll(".toggle-expand-btn").forEach(btn => {
        const txt = btn.previousSibling;
        btn.onclick = () => {
            if (txt.classList.contains("collapsed")) {
                txt.classList.remove("collapsed");
                btn.textContent = "Mostrar menos";
            } else {
                txt.classList.add("collapsed");
                btn.textContent = "... mostrar mais";
            }
            scrollBottom(true);
        };
    });
}

// ===== TYPING =====
function showTyping() {
    const group = document.createElement("div");
    group.className = "message-group bot";
    group.id = "typing-indicator";
    group.appendChild(makeBotAvatar());
    
    const body = document.createElement("div");
    body.className = "msg-body";
    
    const bubble = document.createElement("div");
    bubble.className = "bubble bot-bubble typing-indicator";
    bubble.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';
    
    body.appendChild(bubble);
    group.appendChild(body);
    chatBox.appendChild(group);
    scrollBottom();
}

function hideTyping() { 
    const el = document.getElementById("typing-indicator"); 
    if(el) el.remove(); 
}

// ===== ADD MESSAGES =====
function addBotMessage(data) {
    chatBox.appendChild(makeMessageGroup(data.resposta || "Entendi.", "bot", data));
    
    let chipsData = [];
    if (data.dicas) chipsData = chipsData.concat(data.dicas);
    if (data.relacionados) chipsData = chipsData.concat(data.relacionados);
    
    if (chipsData.length > 0) { 
        const c = makeChipsSection(chipsData.slice(0, 4));
        if(c) chatBox.appendChild(c); 
    }
    
    scrollBottom();
    saveHistory();
}

function addUserMessage(text) { 
    chatBox.appendChild(makeMessageGroup(text, "user")); 
    scrollBottom(); 
    saveHistory(); 
}

// ===== INITIAL =====
function renderInitial() {
    chatBox.innerHTML = "";
    chatBox.appendChild(makeMessageGroup(getSaudacao(), "bot", null));
    
    const chips = makeChipsSection([
        "Produto com defeito",
        "Atraso na entrega",
        "Cobrança indevida",
        "Arrependimento de compra"
    ]);
    if (chips) chatBox.appendChild(chips);
    
    scrollBottom(false);
    saveHistory();
}

function loadHistory() {
    try { 
        const s = localStorage.getItem(STORAGE_KEY); 
        if(s) { chatBox.innerHTML = s; reconectarChips(); scrollBottom(false); } 
        else { renderInitial(); } 
    }
    catch(e) { renderInitial(); }
}

// ===== STATS MONITOR =====
async function atualizarStats() {
    try {
        const res = await fetch("/stats");
        if (!res.ok) return;
        const s = await res.json();
        const panel = document.getElementById("stats-panel");
        
        // Regra restrita: Só aparece no DOM e fica visível se a contagem for maior que zero
        if (panel && s.total_mensagens > 0) {
            panel.style.display = "flex";
            panel.innerHTML = `
                <div class="stat-row">
                    <span class="stat-label">Mensagens</span>
                    <span class="stat-value">${s.total_mensagens}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">📚 Base</span>
                    <span class="stat-value">${s.taxa_base_pct}%</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">⚡ LLM</span>
                    <span class="stat-value">${s.taxa_llm_pct}%</span>
                </div>
                ${s.tempo_medio_llm_ms > 0 ? `
                <div class="stat-row">
                    <span class="stat-label">⏱ Avg</span>
                    <span class="stat-value">${s.tempo_medio_llm_ms}ms</span>
                </div>` : ''}
            `;
        } else if (panel) {
            panel.style.display = "none";
            panel.innerHTML = "";
        }
    } catch(e) {}
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
    
    // Reseta o textarea para o tamanho base padrão (1 linha)
    userInput.value = ""; 
    userInput.style.height = "auto";
    
    showTyping();
    
    try {
        const res = await fetch("/chat", {
            method:"POST",
            headers:{"Content-Type":"application/json"},
            body:JSON.stringify({mensagem:msg})
        });
        let data; 
        try { data = await res.json(); } catch(e) { data = {resposta:"Erro ao processar a resposta."}; }
        
        hideTyping();
        addBotMessage(data || {resposta:"Desculpe, ocorreu um erro na comunicação."});
        atualizarStats();
        
    } catch(err) {
        hideTyping();
        addBotMessage({resposta:"Não foi possível conectar. Verifique sua conexão com a internet."});
    } finally { 
        sending = false; 
        sendBtn.disabled = false;
        userInput.focus();
    }
}

function usarExemplo(text) { 
    if(!text || sending) return; 
    userInput.value = text; 
    sendMessage(); 
}

function clearChat() {
    fetch("/reset", {method:"POST"}).catch(()=>{});
    localStorage.removeItem(STORAGE_KEY); 
    renderInitial(); 
    
    // Zera os registros visualmente no cliente e oculta o painel imediatamente
    const panel = document.getElementById("stats-panel");
    if (panel) {
        panel.style.display = "none";
        panel.innerHTML = "";
    }
}

// Listener do botão de nova conversa
if (clearBtn) {
    clearBtn.addEventListener("click", clearChat);
}

// ===== INPUT DYNAMIC RESIZE & KEYS =====
userInput.addEventListener("input", function() {
    this.style.height = "auto";
    this.style.height = (this.scrollHeight - 4) + "px";
});

userInput.addEventListener("keydown", e => {
    // Enter envia a mensagem normalmente, Shift + Enter injeta quebra de linha nativa
    if(e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// ===== INIT =====
window.addEventListener("load", () => { 
    if(agentName) agentName.textContent = "ConsumidorBot"; 
    loadHistory(); 
    atualizarStats();
});