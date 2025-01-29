import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { register } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

export const SignupForm = () => {
  const { toast } = useToast();
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // パスワード確認
    if (formData.password !== formData.confirmPassword) {
      toast({
        variant: "destructive",
        title: "エラー",
        description: "パスワードが一致しません",
      });
      return;
    }

    setIsLoading(true);
    try {
      const response = await register({
        username: formData.username,
        email: formData.email,
        password: formData.password,
      });

      toast({
        title: "登録完了",
        description: response.message,
      });

      // TODO: ログイン状態にして、ホーム画面にリダイレクト
    } catch (error: any) {
      const errorMessage = error.response?.data?.error || "登録に失敗しました";
      toast({
        variant: "destructive",
        title: "エラー",
        description: Array.isArray(errorMessage)
          ? errorMessage[0]
          : errorMessage,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  return (
    <div className="flex justify-center items-center min-h-screen bg-gray-100">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-2xl font-bold text-center">
            新規登録
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="username">ユーザー名</Label>
              <Input
                id="username"
                name="username"
                type="text"
                required
                value={formData.username}
                onChange={handleChange}
                placeholder="ユーザー名を入力"
                disabled={isLoading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">メールアドレス</Label>
              <Input
                id="email"
                name="email"
                type="email"
                required
                value={formData.email}
                onChange={handleChange}
                placeholder="メールアドレスを入力"
                disabled={isLoading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">パスワード</Label>
              <Input
                id="password"
                name="password"
                type="password"
                required
                value={formData.password}
                onChange={handleChange}
                placeholder="パスワードを入力"
                disabled={isLoading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirmPassword">パスワード（確認）</Label>
              <Input
                id="confirmPassword"
                name="confirmPassword"
                type="password"
                required
                value={formData.confirmPassword}
                onChange={handleChange}
                placeholder="パスワードを再入力"
                disabled={isLoading}
              />
            </div>
            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? "登録中..." : "登録"}
            </Button>
          </form>
          <div className="mt-4 text-center">
            <p className="text-sm text-gray-600">
              すでにアカウントをお持ちの方は
              <a href="/login" className="text-blue-600 hover:underline">
                ログイン
              </a>
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
