import axios from "axios";

interface Studio {
  id: number;
  name: string;
  address: string;
  hours: string;
  selfBookingStart: string;
}

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || (import.meta.env.PROD 
    ? "/api" 
    : "http://127.0.0.1:8000/api"),
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
});

// デバッグ用：環境変数の値をログ出力
console.log("API Client Configuration:");
console.log("PROD:", import.meta.env.PROD);
console.log("VITE_API_BASE_URL:", import.meta.env.VITE_API_BASE_URL);
console.log("USING BASE_URL:", import.meta.env.VITE_API_BASE_URL || (import.meta.env.PROD ? "/api" : "http://127.0.0.1:8000/api"));

// リクエストインターセプター
apiClient.interceptors.request.use(
  (config) => {
    // デバッグ用：リクエスト情報をログ出力
    console.log("API Request:", {
      method: config.method,
      url: config.url,
      baseURL: config.baseURL,
      fullURL: `${config.baseURL}${config.url}`,
      params: config.params,
      headers: config.headers,
    });
    
    // 必要に応じて認証トークンなどを追加
    return config;
  },
  (error) => {
    console.error("API Request Error:", error);
    return Promise.reject(error);
  }
);

// レスポンスインターセプター
apiClient.interceptors.response.use(
  (response) => {
    // デバッグ用：レスポンス情報をログ出力
    console.log("API Response:", {
      status: response.status,
      statusText: response.statusText,
      headers: response.headers,
      data: response.data,
    });
    return response;
  },
  (error) => {
    // デバッグ用：エラー情報をログ出力
    console.error("API Response Error:", {
      message: error.message,
      code: error.code,
      config: error.config,
      response: error.response ? {
        status: error.response.status,
        statusText: error.response.statusText,
        data: error.response.data,
      } : null,
      request: error.request ? "Request object exists" : null,
    });
    
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
