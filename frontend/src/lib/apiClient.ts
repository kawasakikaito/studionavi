import axios from "axios";

interface Studio {
  id: number;
  name: string;
  address: string;
  hours: string;
  selfBookingStart: string;
}

// 環境変数のデバッグ情報を詳細に出力
console.log("=== API設定デバッグ情報 ===");
console.log("PROD:", import.meta.env.PROD);
console.log("DEV:", import.meta.env.DEV);
console.log("MODE:", import.meta.env.MODE);
console.log("VITE_API_BASE_URL:", import.meta.env.VITE_API_BASE_URL);
console.log("全環境変数:", import.meta.env);
console.log("=========================");

// ブラウザの情報を出力
console.log("=== ブラウザ情報 ===");
console.log("ホスト名:", window.location.hostname);
console.log("プロトコル:", window.location.protocol);
console.log("ポート:", window.location.port);
console.log("パス:", window.location.pathname);
console.log("完全なURL:", window.location.href);
console.log("=================");

// 相対パスを使用して、ブラウザのプロトコルに合わせてAPIリクエストを送信
let baseURL;
if (import.meta.env.VITE_API_BASE_URL) {
  // 環境変数が設定されている場合はそれを優先
  // 絶対URLの場合はそのまま使用、相対パスの場合は先頭の/を確認
  if (import.meta.env.VITE_API_BASE_URL.startsWith('http')) {
    baseURL = import.meta.env.VITE_API_BASE_URL;
  } else {
    baseURL = import.meta.env.VITE_API_BASE_URL.startsWith('/') 
      ? import.meta.env.VITE_API_BASE_URL 
      : `/${import.meta.env.VITE_API_BASE_URL}`;
  }
  console.log("環境変数からbaseURLを設定:", baseURL);
} else if (import.meta.env.PROD) {
  // 本番環境では相対パスを使用（ブラウザのプロトコルに合わせる）
  baseURL = "/api";
  console.log("本番環境用の相対パスを使用:", baseURL);
} else {
  // 開発環境
  baseURL = "http://127.0.0.1:8000/api";
  console.log("開発環境用のエンドポイントを使用:", baseURL);
}

console.log("最終的に使用するbaseURL:", baseURL);

const apiClient = axios.create({
  baseURL: baseURL,
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
  // 本番環境でのCORS問題を回避するために、クレデンシャルを含める
  withCredentials: import.meta.env.PROD,
});

// デバッグ用：環境変数の値をログ出力
console.log("API Client Configuration:");
console.log("PROD:", import.meta.env.PROD);
console.log("VITE_API_BASE_URL:", import.meta.env.VITE_API_BASE_URL);
console.log("USING BASE_URL:", baseURL);
console.log("withCredentials:", import.meta.env.PROD);

// リクエストインターセプター
apiClient.interceptors.request.use(
  (config) => {
    // デバッグ用：リクエスト情報をログ出力
    console.log("API Request:", {
      method: config.method,
      url: config.url,
      baseURL: config.baseURL,
      fullURL: config.baseURL.startsWith('http') 
        ? `${config.baseURL}${config.url}` 
        : `${window.location.origin}${config.baseURL}${config.url}`,
      params: config.params,
      headers: config.headers,
      withCredentials: config.withCredentials,
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
      config: error.config ? {
        baseURL: error.config.baseURL,
        url: error.config.url,
        method: error.config.method,
        fullURL: error.config.baseURL.startsWith('http')
          ? `${error.config.baseURL}${error.config.url}`
          : `${window.location.origin}${error.config.baseURL}${error.config.url}`,
        withCredentials: error.config.withCredentials,
      } : null,
      response: error.response ? {
        status: error.response.status,
        statusText: error.response.statusText,
        data: error.response.data,
      } : null,
      request: error.request ? "Request object exists" : null,
    });
    
    if (error.response) {
      // サーバーからのエラーレスポンス
      console.error("サーバーからエラーレスポンスを受信:", error.response);
      const errorMessage =
        error.response.data?.message || "サーバーエラーが発生しました";
      return Promise.reject(new Error(errorMessage));
    } else if (error.request) {
      // リクエストが送信されたがレスポンスがない
      console.error("リクエスト送信後にレスポンスなし:", error.request);
      return Promise.reject(new Error("サーバーとの接続に失敗しました"));
    } else {
      // リクエスト設定時のエラー
      console.error("リクエスト設定時のエラー:", error.message);
      return Promise.reject(
        new Error("リクエストの設定中にエラーが発生しました")
      );
    }
  }
);

export const searchStudios = async (query: string): Promise<Studio[]> => {
  console.log(`スタジオ検索開始: クエリ="${query}"`);
  try {
    const fullUrl = baseURL.startsWith('http') 
      ? `${baseURL}/studios/search?q=${query}` 
      : `${window.location.origin}${baseURL}/studios/search?q=${query}`;
    console.log(`APIリクエスト実行: ${fullUrl}`);
    const response = await apiClient.get<Studio[]>("/studios/search", {
      params: { q: query },
    });
    console.log("スタジオ検索成功:", response.data);
    return response.data;
  } catch (error) {
    console.error("スタジオ検索エラー:", error);
    throw error;
  }
};

export default apiClient;
