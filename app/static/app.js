const loginForm = document.querySelector("#login-form");
const logoutButton = document.querySelector("#logout-button");
const authMessage = document.querySelector("#auth-message");
const dashboard = document.querySelector("#dashboard");
const currentUser = document.querySelector("#current-user");
const projectList = document.querySelector("#project-list");
const sampleList = document.querySelector("#sample-list");
const runList = document.querySelector("#run-list");

function setMessage(text, type = "neutral") {
  authMessage.textContent = text;
  authMessage.dataset.type = type;
}

function getToken() {
  return localStorage.getItem("labflow_token");
}

function setToken(token) {
  localStorage.setItem("labflow_token", token);
}

function clearToken() {
  localStorage.removeItem("labflow_token");
}

async function requestJson(path, options = {}) {
  const headers = new Headers(options.headers || {});
  const token = getToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  const response = await fetch(path, { ...options, headers });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || "Запрос не выполнен");
  }
  return response.json();
}

function renderList(target, values, formatter) {
  target.replaceChildren();
  if (!values.length) {
    const item = document.createElement("li");
    item.textContent = "Нет данных";
    target.append(item);
    return;
  }
  values.slice(0, 5).forEach((value) => {
    const item = document.createElement("li");
    item.textContent = formatter(value);
    target.append(item);
  });
}

async function loadDashboard() {
  if (!getToken()) {
    dashboard.hidden = true;
    return;
  }
  const [user, projects, samples, runs] = await Promise.all([
    requestJson("/users/me"),
    requestJson("/projects"),
    requestJson("/samples"),
    requestJson("/runs"),
  ]);
  currentUser.textContent = `${user.username} (${user.role})`;
  renderList(projectList, projects, (project) => `${project.title} - ${project.status}`);
  renderList(sampleList, samples, (sample) => `${sample.code} - ${sample.required_method}, приоритет ${sample.priority}`);
  renderList(runList, runs, (run) => `#${run.id}: образец ${run.sample_id}, ${run.scheduled_date}, ${run.status}`);
  dashboard.hidden = false;
}

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(loginForm);
  const body = new URLSearchParams();
  body.set("username", form.get("username"));
  body.set("password", form.get("password"));
  setMessage("Выполняется вход...");
  try {
    const payload = await requestJson("/auth/token", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
    });
    setToken(payload.access_token);
    await loadDashboard();
    setMessage("Вход выполнен. Демо-данные загружены.", "success");
  } catch (error) {
    clearToken();
    dashboard.hidden = true;
    setMessage(error.message, "error");
  }
});

logoutButton.addEventListener("click", () => {
  clearToken();
  dashboard.hidden = true;
  setMessage("Выход выполнен.");
});

loadDashboard().catch(() => {
  clearToken();
  dashboard.hidden = true;
});
