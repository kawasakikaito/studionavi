import axios from "axios";

// CSRFトークンを取得する関数
function getCookie(name: string): string | null {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop()?.split(";").shift() || null;
  return null;
}

const api = axios.create({
  baseURL: "http://localhost:8000/api",
  headers: {
    "Content-Type": "application/json",
    "X-CSRFToken": getCookie("csrftoken") || "",
  },
  withCredentials: true, // CSRF tokenのために必要
});

// リクエストインターセプターでCSRFトークンを更新
api.interceptors.request.use((config) => {
  config.headers["X-CSRFToken"] = getCookie("csrftoken") || "";
  return config;
});

export interface User {
  id: number;
  username: string;
  email: string;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
}

export interface LoginData {
  username: string;
  password: string;
}

export interface AuthResponse {
  message: string;
  user: User;
}

export const register = async (data: RegisterData): Promise<AuthResponse> => {
  const response = await api.post<AuthResponse>("/auth/register/", data);
  return response.data;
};

export const login = async (data: LoginData): Promise<AuthResponse> => {
  const response = await api.post<AuthResponse>("/auth/login/", data);
  return response.data;
};

export const logout = async (): Promise<{ message: string }> => {
  const response = await api.post<{ message: string }>("/auth/logout/");
  return response.data;
};

export const getCurrentUser = async (): Promise<User | null> => {
  try {
    const response = await api.get<{ user: User }>("/auth/user/");
    return response.data.user;
  } catch (error) {
    return null;
  }
};

export default api;
