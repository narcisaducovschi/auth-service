const API_URL = "http://localhost:8000";

function saveTokens(accessToken, refreshToken) {
    localStorage.setItem("access_token", accessToken);
    localStorage.setItem("refresh_token", refreshToken);
}

function getAccessToken() {
    return localStorage.getItem("access_token");
}

function getRefreshToken() {
    return localStorage.getItem("refresh_token");
}

function clearTokens() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
}

// --- Fetch con manejo automático de refresh ---

async function authFetch(url, options = {}) {
    options.headers = {
        ...options.headers,
        "Authorization": `Bearer ${getAccessToken()}`,
    };

    let response = await fetch(url, options);

    if (response.status === 401) {
        const refreshed = await tryRefreshToken();

        if (refreshed) {
            options.headers["Authorization"] = `Bearer ${getAccessToken()}`;
            response = await fetch(url, options);
        } else {
            clearTokens();
            window.location.href = "/static/index.html";
            return null;
        }
    }

    return response;
}

async function tryRefreshToken() {
    const refreshToken = getRefreshToken();
    if (!refreshToken) return false;

    try {
        const response = await fetch(`${API_URL}/auth/refresh`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ refresh_token: refreshToken }),
        });

        if (!response.ok) return false;

        const data = await response.json();
        saveTokens(data.access_token, data.refresh_token);
        return true;
    } catch {
        return false;
    }
}

function showMessage(text, type = "error") {
    const el = document.getElementById("message");
    if (!el) return;
    el.textContent = text;
    el.className = `message ${type}`;
}

const loginForm = document.getElementById("login-form");
const registerForm = document.getElementById("register-form");
const forgotForm = document.getElementById("forgot-form");

if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const email = document.getElementById("login-email").value;
        const password = document.getElementById("login-password").value;

        try {
            const response = await fetch(`${API_URL}/auth/login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password }),
            });

            const data = await response.json();

            if (!response.ok) {
                showMessage(data.detail || "Error al iniciar sesión");
                return;
            }

            saveTokens(data.access_token, data.refresh_token);
            window.location.href = "/static/profile.html";
        } catch {
            showMessage("No se pudo conectar con el servidor");
        }
    });
}

if (registerForm) {
    registerForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const email = document.getElementById("register-email").value;
        const password = document.getElementById("register-password").value;

        try {
            const response = await fetch(`${API_URL}/auth/register`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password }),
            });

            const data = await response.json();

            if (!response.ok) {
                const detail = Array.isArray(data.detail)
                    ? data.detail[0].msg
                    : data.detail;
                showMessage(detail || "Error al registrarse");
                return;
            }

            showMessage("Cuenta creada. Ya puedes iniciar sesión.", "success");
            registerForm.style.display = "none";
            loginForm.style.display = "block";
            document.getElementById("form-title").textContent = "Iniciar sesión";
        } catch {
            showMessage("No se pudo conectar con el servidor");
        }
    });
}

if (forgotForm) {
    forgotForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const email = document.getElementById("forgot-email").value;

        try {
            const response = await fetch(`${API_URL}/auth/forgot-password`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email }),
            });

            const data = await response.json();
            showMessage(data.message + " (revisa la consola del servidor para ver el token de prueba)", "success");
        } catch {
            showMessage("No se pudo conectar con el servidor");
        }
    });
}

const toggleRegister = document.getElementById("toggle-register");
const toggleForgot = document.getElementById("toggle-forgot");
const formTitle = document.getElementById("form-title");

if (toggleRegister) {
    toggleRegister.addEventListener("click", () => {
        const showingLogin = loginForm.style.display !== "none";
        loginForm.style.display = showingLogin ? "none" : "block";
        registerForm.style.display = showingLogin ? "block" : "none";
        forgotForm.style.display = "none";
        formTitle.textContent = showingLogin ? "Crear cuenta" : "Iniciar sesión";
        toggleRegister.textContent = showingLogin ? "¿Ya tienes cuenta? Inicia sesión" : "¿No tienes cuenta? Regístrate";
    });
}

if (toggleForgot) {
    toggleForgot.addEventListener("click", () => {
        loginForm.style.display = "none";
        registerForm.style.display = "none";
        forgotForm.style.display = "block";
        formTitle.textContent = "Recuperar contraseña";
    });
}

const userInfoEl = document.getElementById("user-info");
const logoutBtn = document.getElementById("logout-btn");

if (userInfoEl) {
    (async () => {
        if (!getAccessToken()) {
            window.location.href = "/static/index.html";
            return;
        }

        const response = await authFetch(`${API_URL}/me`);
        if (!response) return;

        if (!response.ok) {
            window.location.href = "/static/index.html";
            return;
        }

        const user = await response.json();
        userInfoEl.innerHTML = `
            <strong>Email:</strong> ${user.email}<br>
            <strong>Rol:</strong> ${user.role}<br>
            <strong>Cuenta activa:</strong> ${user.is_active ? "Sí" : "No"}<br>
            <strong>Creada el:</strong> ${new Date(user.created_at).toLocaleString()}
        `;
    })();
}

if (logoutBtn) {
    logoutBtn.addEventListener("click", () => {
        clearTokens();
        window.location.href = "/static/index.html";
    });
}