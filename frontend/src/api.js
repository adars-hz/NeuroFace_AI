
import axios from "axios";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000",
  timeout: 30000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("neuroface_token");

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

export async function login(username, password) {
  const response = await api.post(
    "/auth/login",
    new URLSearchParams({
      username,
      password,
    }),
    {
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
    }
  );

  const token = response.data.access_token;

  if (token) {
    localStorage.setItem("neuroface_token", token);
  }

  return response.data;
}

export async function getCurrentUser() {
  const response = await api.get("/auth/me");
  return response.data;
}

export async function getMyAttendanceSummary() {
  const response = await api.get("/attendance-summary/my");
  return response.data;
}

export function logout() {
  localStorage.removeItem("neuroface_token");
}

export default api;
