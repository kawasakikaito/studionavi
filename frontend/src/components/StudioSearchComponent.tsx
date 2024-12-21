import React, { useState, useRef, useEffect, useCallback } from "react";
import { Input } from "@/components/ui/input";
import { Search } from "lucide-react";
import { Loader2 } from "lucide-react";
import debounce from "lodash/debounce";

interface Studio {
  id: number;
  name: string;
  address: string;
  hours: string;
  self_booking_start: string;
}

interface StudioSearchComponentProps {
  onStudioSelect: (studio: Studio) => void;
  disabled?: boolean;
}

export function StudioSearchComponent({
  onStudioSelect,
  disabled,
}: StudioSearchComponentProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearchResultsOpen, setIsSearchResultsOpen] = useState(false);
  const [searchResults, setSearchResults] = useState<Studio[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const searchRef = useRef<HTMLDivElement>(null);

  // API呼び出し関数
  const fetchStudios = async (query: string) => {
    try {
      setIsLoading(true);
      setError(null);

      // APIエンドポイントを実際のものに置き換えてください
      const response = await fetch(
        `https://api.example.com/studios/search?q=${encodeURIComponent(query)}`
      );

      if (!response.ok) {
        throw new Error("検索中にエラーが発生しました");
      }

      const data = await response.json();
      setSearchResults(data);
      setIsSearchResultsOpen(true);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "予期せぬエラーが発生しました"
      );
      setSearchResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  // デバウンス処理を適用した検索関数
  const debouncedFetch = useCallback(
    debounce((query: string) => {
      if (query.length >= 2) {
        fetchStudios(query);
      } else {
        setSearchResults([]);
        setIsSearchResultsOpen(false);
      }
    }, 300),
    []
  );

  // 入力変更時のハンドラー
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const query = e.target.value;
    setSearchQuery(query);
    debouncedFetch(query);
  };

  // クリックアウト時の処理
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        searchRef.current &&
        !searchRef.current.contains(event.target as Node)
      ) {
        setIsSearchResultsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  // コンポーネントのクリーンアップ
  useEffect(() => {
    return () => {
      debouncedFetch.cancel();
    };
  }, [debouncedFetch]);

  return (
    <div ref={searchRef} className="relative">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          className="pl-9"
          placeholder="スタジオ名・エリアで検索"
          value={searchQuery}
          onChange={handleInputChange}
          disabled={disabled}
        />
        {isLoading && (
          <Loader2 className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 animate-spin text-muted-foreground" />
        )}
      </div>

      {error && (
        <div className="absolute z-10 w-full mt-1 p-2 bg-red-50 border border-red-200 rounded-md text-red-600 text-sm">
          {error}
        </div>
      )}

      {isSearchResultsOpen && searchResults.length > 0 && (
        <div className="absolute z-10 w-full mt-1 bg-background border rounded-md shadow-lg">
          {searchResults.map((studio) => (
            <button
              key={studio.id}
              className="w-full px-4 py-2 text-left hover:bg-muted"
              onClick={() => {
                onStudioSelect(studio);
                setSearchQuery("");
                setIsSearchResultsOpen(false);
              }}
            >
              <div className="font-medium">{studio.name}</div>
              <div className="text-sm text-muted-foreground">
                {studio.address}
              </div>
            </button>
          ))}
        </div>
      )}

      {isSearchResultsOpen &&
        searchQuery.length >= 2 &&
        searchResults.length === 0 &&
        !isLoading && (
          <div className="absolute z-10 w-full mt-1 p-2 bg-background border rounded-md text-muted-foreground text-sm">
            検索結果が見つかりませんでした
          </div>
        )}
    </div>
  );
}
