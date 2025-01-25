import axios from "axios";

interface Studio {
  id: number;
  name: string;
  address: string;
  hours: string;
  selfBookingStart: string;
}

const apiClient = axios.create({
  baseURL: "http://127.0.0.1:8000/api",
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
});

// リクエストインターセプター
apiClient.interceptors.request.use(
  (config) => {
    // 必要に応じて認証トークンなどを追加
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// レスポンスインターセプター
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // サーバーからのエラーレスポンス
      const errorMessage =
        error.response.data?.message || "サーバーエラーが発生しました";
      return Promise.reject(new Error(errorMessage));
    } else if (error.request) {
      // リクエストが送信されたがレスポンスがない
      return Promise.reject(new Error("サーバーとの接続に失敗しました"));
    } else {
      // リクエスト設定時のエラー
      return Promise.reject(
        new Error("リクエストの設定中にエラーが発生しました")
      );
    }
  }
);

export const searchStudios = async (query: string): Promise<Studio[]> => {
  try {
    const response = await apiClient.get<Studio[]>("/studios/search", {
      params: { q: query },
    });
    return response.data;
  } catch (error) {
    throw error;
  }
};

export default apiClient;
