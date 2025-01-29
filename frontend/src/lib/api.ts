import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8001/api",
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true, // CSRF tokenのために必要
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

export const getCurrentUser = async (): Promise<User | null> => {
  try {
    const response = await api.get<{ user: User }>("/auth/user/");
    return response.data.user;
  } catch (error) {
    return null;
  }
};

export default api;
