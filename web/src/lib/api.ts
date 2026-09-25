import axios, { type AxiosError } from "axios";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

let accessToken: string | null = null;
let refreshToken: string | null = sessionStorage.getItem("forhire_refresh");

export function setTokens(access: string, refresh: string) {
  accessToken = access;
  refreshToken = refresh;
  sessionStorage.setItem("forhire_refresh", refresh);
}

export function clearTokens() {
  accessToken = null;
  refreshToken = null;
  sessionStorage.removeItem("forhire_refresh");
}

export function getAccessToken() {
  return accessToken;
}

const client = axios.create({ baseURL: API_BASE });

client.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

client.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    const original = error.config;
    if (
      error.response?.status === 401 &&
      refreshToken &&
      original &&
      !(original as { _retry?: boolean })._retry
    ) {
      (original as { _retry?: boolean })._retry = true;
      try {
        const { data } = await axios.post(`${API_BASE}/auth/token/refresh/`, {
          refresh: refreshToken,
        });
        accessToken = data.access;
        if (data.refresh) {
          refreshToken = data.refresh;
          sessionStorage.setItem("forhire_refresh", data.refresh);
        }
        original.headers.Authorization = `Bearer ${accessToken}`;
        return client(original);
      } catch {
        clearTokens();
      }
    }
    return Promise.reject(error);
  },
);

export const api = client;

export async function login(email: string, password: string) {
  const { data } = await api.post("/auth/token/", { email, password });
  setTokens(data.access, data.refresh);
  return data;
}

export async function bootstrapSession() {
  if (!refreshToken || accessToken) return;
  const { data } = await axios.post(`${API_BASE}/auth/token/refresh/`, {
    refresh: refreshToken,
  });
  accessToken = data.access;
  if (data.refresh) {
    refreshToken = data.refresh;
    sessionStorage.setItem("forhire_refresh", data.refresh);
  }
}
