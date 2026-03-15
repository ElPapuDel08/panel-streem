// Manejo de Navegación por Pestañas
document.querySelectorAll('.nav-item').forEach(button => {
    button.addEventListener('click', () => {
        // Remover activos anteriores
        document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
        
        // Activar actual
        button.classList.add('active');
        const tabId = button.getAttribute('data-tab');
        document.getElementById(`tab-${tabId}`).classList.add('active');
    });
});

// Comunicación con Python (Eel)
document.getElementById('btn-toggle-live').addEventListener('click', async () => {
    const user = document.getElementById('tiktok-user').value;
    if (!user) {
        alert("Por favor ingresa un usuario");
        return;
    }
    
    // Llamada a función expuesta en Python
    const result = await eel.toggle_bot_web(user)();
    console.log("Resultado de Python:", result);
});

document.getElementById('btn-open-test').addEventListener('click', () => {
    eel.open_test_window_web()();
});

// Función expuesta para que Python escriba en el Log
eel.expose(add_log_web);
function add_log_web(message) {
    const logArea = document.getElementById('event-log');
    const entry = document.createElement('div');
    entry.className = 'log-entry';
    entry.textContent = message;
    logArea.appendChild(entry);
    
    // Auto Scroll
    logArea.scrollTop = logArea.scrollHeight;
}

// Función para actualizar estado conexión
eel.expose(update_status_web);
function update_status_web(isOnline, text) {
    const dot = document.getElementById('connection-dot');
    const statusText = document.getElementById('status-text');
    const btn = document.getElementById('btn-toggle-live');
    
    if (isOnline) {
        dot.classList.add('online');
        statusText.textContent = text || "En Vivo";
        btn.textContent = "⏹ DETENER LIVE";
        btn.classList.add('btn-danger');
    } else {
        dot.classList.remove('online');
        statusText.textContent = text || "Desconectado";
        btn.textContent = "▶ INICIAR LIVE";
        btn.classList.remove('btn-danger');
    }
}
