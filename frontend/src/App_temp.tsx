import React, { useState, useMemo, useRef, useEffect } from "react";
import { Search, Trash2, MapPin, Clock, Calendar, Plus } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";

interface Studio {
  id: number;
  name: string;
  address: string;
  hours: string;
  bookingStart: string;
}

const PRESET_STUDIOS: Studio[] = [
  {
    id: 1,
    name: "Sound Lab Studios",
    address: "東京都渋谷区神南1-2-3",
    hours: "10:00 - 26:00",
    bookingStart: "前日 12:00〜",
  },
  {
    id: 2,
    name: "Melody Box Studio",
    address: "東京都新宿区高田馬場4-5-6",
    hours: "9:00 - 27:00",
    bookingStart: "3日前 10:00〜",
  },
  {
    id: 3,
    name: "Rock Heaven",
    address: "東京都北区王子7-8-9",
    hours: "10:00 - 25:00",
    bookingStart: "当日 0:00〜",
  },
  {
    id: 4,
    name: "Studio Mission",
    address: "東京都世田谷区下北沢1-10-12",
    hours: "11:00 - 26:00",
    bookingStart: "2日前 15:00〜",
  },
  {
    id: 5,
    name: "Jam Station",
    address: "東京都港区六本木13-14-15",
    hours: "8:00 - 27:00",
    bookingStart: "前日 18:00〜",
  },
];

const MusicStudioBookingApp = () => {
  const [selectedStudios, setSelectedStudios] = useState([
    PRESET_STUDIOS[0],
    PRESET_STUDIOS[2],
    PRESET_STUDIOS[4],
  ]);
  const [selectedDate, setSelectedDate] = useState("");
  const [searchPerformed, setSearchPerformed] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearchResultsOpen, setIsSearchResultsOpen] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);

  const searchResults = useMemo(() => {
    if (!searchQuery) return [];
    const selectedIds = selectedStudios.map((s) => s.id);
    return PRESET_STUDIOS.filter((studio) => {
      const searchLower = searchQuery.toLowerCase();
      return (
        !selectedIds.includes(studio.id) &&
        (studio.name.toLowerCase().includes(searchLower) ||
          studio.address.toLowerCase().includes(searchLower))
      );
    });
  }, [searchQuery, selectedStudios]);

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
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const addStudio = (studio: Studio) => {
    if (selectedStudios.length < 5) {
      setSelectedStudios((prev) => [...prev, studio]);
      setSearchQuery("");
      setIsSearchResultsOpen(false);
    }
  };

  const removeStudio = (studioId: number) => {
    setSelectedStudios((prev) => prev.filter((s) => s.id !== studioId));
  };

  const handleSearch = () => {
    setSearchPerformed(true);
  };

  const resetSearch = () => {
    setSelectedStudios([]);
    setSelectedDate("");
    setSearchPerformed(false);
    setSearchQuery("");
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8">
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <CardTitle>選択中のスタジオ</CardTitle>
            <Badge variant="secondary">{selectedStudios.length}/5</Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="relative" ref={searchRef}>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
              <Input
                type="text"
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setIsSearchResultsOpen(true);
                }}
                onFocus={() => setIsSearchResultsOpen(true)}
                placeholder="スタジオを検索して追加..."
                className="pl-10"
                disabled={selectedStudios.length >= 5}
              />
            </div>

            {isSearchResultsOpen && searchResults.length > 0 && (
              <Card className="absolute z-50 w-full mt-2">
                <CardContent className="p-2">
                  {searchResults.map((studio) => (
                    <button
                      key={studio.id}
                      onClick={() => addStudio(studio)}
                      className="w-full text-left p-3 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
                    >
                      <div className="font-medium">{studio.name}</div>
                      <div className="text-sm text-gray-500 dark:text-gray-400 flex items-center mt-1">
                        <MapPin className="h-4 w-4 mr-1" />
                        {studio.address}
                      </div>
                    </button>
                  ))}
                </CardContent>
              </Card>
            )}
          </div>

          <div className="space-y-4">
            {selectedStudios.map((studio) => (
              <Card key={studio.id}>
                <CardContent className="p-6">
                  <div className="flex justify-between items-start">
                    <div className="space-y-4">
                      <h3 className="text-lg font-semibold">{studio.name}</h3>
                      <div className="space-y-2 text-sm">
                        <div className="flex items-center text-gray-600 dark:text-gray-400">
                          <MapPin className="h-4 w-4 mr-2" />
                          {studio.address}
                        </div>
                        <div className="flex items-center text-gray-600 dark:text-gray-400">
                          <Clock className="h-4 w-4 mr-2" />
                          {studio.hours}
                        </div>
                        <div className="flex items-center text-gray-600 dark:text-gray-400">
                          <Calendar className="h-4 w-4 mr-2" />
                          {studio.bookingStart}
                        </div>
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => removeStudio(studio.id)}
                      className="text-gray-500 hover:text-red-500"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}

            {selectedStudios.length === 0 && (
              <div className="text-center py-12">
                <Plus className="h-12 w-12 mx-auto text-gray-400 mb-4" />
                <p className="text-gray-500">
                  スタジオを検索して追加してください
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>日時を選択</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Input
              type="datetime-local"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
            />
            <Select defaultValue="2">
              <SelectTrigger>
                <SelectValue placeholder="利用時間" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1">1時間</SelectItem>
                <SelectItem value="2">2時間</SelectItem>
                <SelectItem value="3">3時間</SelectItem>
                <SelectItem value="4">4時間</SelectItem>
                <SelectItem value="5">5時間</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <Button
            className="w-full"
            disabled={selectedStudios.length === 0 || !selectedDate}
            onClick={handleSearch}
          >
            空き状況を検索
          </Button>
        </CardContent>
      </Card>

      {searchPerformed && (
        <Card>
          <CardHeader>
            <CardTitle>空き状況</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {selectedStudios.map((studio) => (
              <Card key={studio.id}>
                <CardContent className="p-6">
                  <div className="space-y-4">
                    <div>
                      <h3 className="text-lg font-semibold">{studio.name}</h3>
                      <div className="mt-4 space-y-2 text-sm">
                        <div className="flex items-center text-gray-600 dark:text-gray-400">
                          <MapPin className="h-4 w-4 mr-2" />
                          {studio.address}
                        </div>
                        <div className="flex items-center text-gray-600 dark:text-gray-400">
                          <Clock className="h-4 w-4 mr-2" />
                          {studio.hours}
                        </div>
                        <div className="flex items-center">
                          <Calendar className="h-4 w-4 mr-2" />
                          <span className="text-blue-600 dark:text-blue-400">
                            {new Date(selectedDate).toLocaleString("ja-JP")}
                          </span>
                        </div>
                        <Badge variant="success" className="mt-2">
                          予約可能
                        </Badge>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <Button variant="default">Web予約</Button>
                      <Button variant="secondary">電話予約</Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
            <Button variant="outline" className="w-full" onClick={resetSearch}>
              新しく検索
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default MusicStudioBookingApp;
