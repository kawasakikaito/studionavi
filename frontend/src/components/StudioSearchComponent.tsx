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
  selectedCount: number;
  maxSelections?: number;
  selectedStudios: Studio[]; // 追加: 選択済みスタジオの配列
}

export function StudioSearchComponent({
  onStudioSelect,
  selectedCount,
  maxSelections = 5,
  selectedStudios, // 追加: 選択済みスタジオの配列を受け取る
}: StudioSearchComponentProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearchResultsOpen, setIsSearchResultsOpen] = useState(false);
  const [searchResults, setSearchResults] = useState<Studio[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const searchRef = useRef<HTMLDivElement>(null);
  const resultsRef = useRef<HTMLDivElement>(null);

  const isMaxSelected = selectedCount >= maxSelections;

  const fetchStudios = async (query: string) => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await fetch(
        `http://127.0.0.1:8000/api/studio/search/?q=${encodeURIComponent(
          query
        )}`
      );

      if (!response.ok) {
        throw new Error("検索中にエラーが発生しました");
      }

      const data = await response.json();
      // 選択済みスタジオを除外
      const filteredResults = data.filter(
        (studio: Studio) =>
          !selectedStudios.some((selected) => selected.id === studio.id)
      );
      setSearchResults(filteredResults);
      setIsSearchResultsOpen(true);
      setSelectedIndex(-1);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "予期せぬエラーが発生しました"
      );
      setSearchResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  const debouncedFetch = useCallback(
    debounce((query: string) => {
      if (query.length >= 2) {
        fetchStudios(query);
      } else {
        setSearchResults([]);
        setIsSearchResultsOpen(false);
      }
    }, 300),
    [selectedStudios] // selectedStudiosを依存配列に追加
  );

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const query = e.target.value;
    setSearchQuery(query);
    debouncedFetch(query);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!isSearchResultsOpen || searchResults.length === 0) return;

    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        setSelectedIndex((prev) =>
          prev < searchResults.length - 1 ? prev + 1 : 0
        );
        break;
      case "ArrowUp":
        e.preventDefault();
        setSelectedIndex((prev) =>
          prev > 0 ? prev - 1 : searchResults.length - 1
        );
        break;
      case "Enter":
        e.preventDefault();
        if (selectedIndex >= 0 && !isMaxSelected) {
          onStudioSelect(searchResults[selectedIndex]);
          setSearchQuery("");
          setIsSearchResultsOpen(false);
          setSelectedIndex(-1);
        }
        break;
      case "Escape":
        setIsSearchResultsOpen(false);
        setSelectedIndex(-1);
        break;
    }
  };

  useEffect(() => {
    if (selectedIndex >= 0 && resultsRef.current) {
      const selectedElement = resultsRef.current.children[
        selectedIndex
      ] as HTMLElement;
      if (selectedElement) {
        selectedElement.scrollIntoView({
          block: "nearest",
        });
      }
    }
  }, [selectedIndex]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        searchRef.current &&
        !searchRef.current.contains(event.target as Node)
      ) {
        setIsSearchResultsOpen(false);
        setSelectedIndex(-1);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

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
          className="pl-9 disabled:bg-muted"
          placeholder={
            isMaxSelected
              ? "スタジオの選択上限に達しました"
              : "スタジオ名・エリアで検索"
          }
          value={searchQuery}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          disabled={isMaxSelected}
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

      {isSearchResultsOpen && searchResults.length > 0 && !isMaxSelected && (
        <div
          ref={resultsRef}
          className="absolute z-10 w-full mt-1 bg-background border rounded-md shadow-lg max-h-64 overflow-y-auto"
        >
          {searchResults.map((studio, index) => (
            <button
              key={studio.id}
              className={`w-full px-4 py-2 text-left hover:bg-muted ${
                index === selectedIndex ? "bg-muted" : ""
              }`}
              onClick={() => {
                if (!isMaxSelected) {
                  onStudioSelect(studio);
                  setSearchQuery("");
                  setIsSearchResultsOpen(false);
                  setSelectedIndex(-1);
                }
              }}
              onMouseEnter={() => setSelectedIndex(index)}
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

      {isMaxSelected && searchQuery && (
        <div className="absolute z-10 w-full mt-1 p-2 bg-yellow-50 border border-yellow-200 rounded-md text-yellow-600 text-sm">
          スタジオの選択上限（{maxSelections}件）に達しています
        </div>
      )}
    </div>
  );
}
