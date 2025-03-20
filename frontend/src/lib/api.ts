import axios from "axios";

// CSRFトークンを取得する関数
function getCookie(name: string): string | null {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop()?.split(";").shift() || null;
  return null;
}

// 環境変数からAPIのベースURLを取得、なければデフォルト値を使用
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://studionavi-alb-837030228.ap-northeast-1.elb.amazonaws.com/api";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
    "X-CSRFToken": getCookie("csrftoken") || "",
  },
  withCredentials: true, // CSRF tokenのために必要
});

// デバッグ用：APIの設定情報をログに出力
console.log("API設定:", {
  baseURL: API_BASE_URL,
  environment: import.meta.env.MODE || "development"
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
