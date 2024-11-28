import React, { useState, useMemo, useRef, useEffect } from "react";
import {
  Search,
  Trash2,
  MapPin,
  Clock,
  Calendar,
  Plus,
  Menu,
  User,
  LogIn,
  CalendarIcon,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { format } from "date-fns";
import { cn, mainGradient } from "@/lib/utils";
import { Calendar as CalendarComponent } from "@/components/ui/calendar";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { ja } from "date-fns/locale";

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

const timeOptions = [
  "10:00",
  "11:00",
  "12:00",
  "13:00",
  "14:00",
  "15:00",
  "16:00",
  "17:00",
  "18:00",
  "19:00",
  "20:00",
  "21:00",
  "22:00",
];

const durationOptions = ["1時間", "2時間", "3時間", "4時間", "5時間"];

const MusicStudioBookingApp = () => {
  const [selectedStudios, setSelectedStudios] = useState([
    PRESET_STUDIOS[0],
    PRESET_STUDIOS[2],
    PRESET_STUDIOS[4],
  ]);
  const [selectedDate, setSelectedDate] = useState<Date>();
  const [selectedTime, setSelectedTime] = useState("");
  const [selectedDuration, setSelectedDuration] = useState("");
  const [searchPerformed, setSearchPerformed] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearchResultsOpen, setIsSearchResultsOpen] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
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
    setSelectedDate(undefined);
    setSelectedTime("");
    setSelectedDuration("");
    setSearchPerformed(false);
    setSearchQuery("");
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="bg-background border-b">
        <div className="container mx-auto">
          <div className="flex justify-between h-16">
            <div className="flex">
              <div className="flex-shrink-0 flex items-center">
                <h1 className="text-xl font-bold">スタジオナビ</h1>
              </div>
              <nav className="hidden sm:ml-6 sm:flex sm:space-x-8">
                <a className="border-primary text-foreground inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium">
                  スタジオを探す
                </a>
                <a className="border-transparent text-muted-foreground hover:text-foreground inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium">
                  料金案内
                </a>
                <a className="border-transparent text-muted-foreground hover:text-foreground inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium">
                  設備情報
                </a>
              </nav>
            </div>
            <div className="hidden sm:ml-6 sm:flex sm:items-center sm:space-x-4">
              <Button variant="outline">
                <LogIn className="h-4 w-4 mr-2" />
                ログイン
              </Button>
              <Button variant="gradient">
                <User className="h-4 w-4 mr-2" />
                新規登録
              </Button>
            </div>
            <div className="flex items-center sm:hidden">
              <Button
                variant="default"
                size="icon"
                onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              >
                <Menu className="h-6 w-6" />
              </Button>
            </div>
          </div>
        </div>
      </header>
      {/* Mobile menu */}
      {isMobileMenuOpen && (
        <div className="sm:hidden bg-background border-b">
          <div className="pt-2 pb-3 space-y-1">
            <a className="bg-primary/10 border-primary text-primary block pl-3 pr-4 py-2 border-l-4 text-base font-medium">
              スタジオを探す
            </a>
            <a className="border-transparent text-muted-foreground hover:bg-accent hover:text-foreground block pl-3 pr-4 py-2 border-l-4 text-base font-medium">
              料金案内
            </a>
            <a className="border-transparent text-muted-foreground hover:bg-accent hover:text-foreground block pl-3 pr-4 py-2 border-l-4 text-base font-medium">
              設備情報
            </a>
          </div>
          <div className="pt-4 pb-3 border-t">
            <div className="space-y-1">
              <a className="block px-4 py-2 text-base font-medium text-muted-foreground hover:text-foreground hover:bg-accent">
                ログイン
              </a>
              <a className="block px-4 py-2 text-base font-medium text-muted-foreground hover:text-foreground hover:bg-accent">
                新規登録
              </a>
            </div>
          </div>
        </div>
      )}

      {/* Main content */}
      <main className="container mx-auto py-6">
        {/* Hero section */}
        <div className={cn(mainGradient, "mb-8 p-8 text-white")}>
          <h2 className="text-3xl font-bold mb-4">
            スタジオ予約をもっと簡単に
          </h2>
          <p className="text-lg mb-6">
            複数のスタジオの空き状況を一括検索。あなたの練習に最適な場所を見つけましょう。
          </p>
          <div className="flex space-x-4">
            <Button className="bg-white text-indigo-600 hover:bg-gray-50">
              ご利用ガイド
            </Button>
            <Button
              variant="default"
              className="text-white border-white hover:bg-white/10"
            >
              よくある質問
            </Button>
          </div>
        </div>

        {/* Studio selection */}
        <div className="space-y-8">
          <Card>
            <CardHeader className="border-b">
              <div className="flex justify-between items-center">
                <CardTitle className="text-2xl">選択中のスタジオ</CardTitle>
                <Badge variant="secondary">{selectedStudios.length}/5</Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-6 pt-6">
              <div className="relative" ref={searchRef}>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
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
                        <Button
                          key={studio.id}
                          onClick={() => addStudio(studio)}
                          variant="ghost"
                          className="w-full justify-start h-auto py-3 px-3"
                        >
                          <div>
                            <div className="font-medium">{studio.name}</div>
                            <div className="text-sm text-muted-foreground flex items-center mt-1">
                              <MapPin className="h-4 w-4 mr-1" />
                              {studio.address}
                            </div>
                          </div>
                        </Button>
                      ))}
                    </CardContent>
                  </Card>
                )}
              </div>
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {selectedStudios.map((studio) => (
                  <Card key={studio.id}>
                    <CardContent className="p-6">
                      <div className="flex justify-between items-start">
                        <div className="space-y-4">
                          <h3 className="text-lg font-semibold">
                            {studio.name}
                          </h3>
                          <div className="space-y-2 text-sm">
                            <div className="flex items-center text-muted-foreground">
                              <MapPin className="h-4 w-4 mr-2" />
                              {studio.address}
                            </div>
                            <div className="flex items-center text-muted-foreground">
                              <Clock className="h-4 w-4 mr-2" />
                              {studio.hours}
                            </div>
                            <div className="flex items-center text-muted-foreground">
                              <Calendar className="h-4 w-4 mr-2" />
                              {studio.bookingStart}
                            </div>
                          </div>
                        </div>
                        <Button
                          variant="destructive"
                          size="icon"
                          onClick={() => removeStudio(studio.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}

                {selectedStudios.length === 0 && (
                  <div className="col-span-full text-center py-12 bg-muted rounded-lg">
                    <Plus className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                    <p className="text-muted-foreground">
                      スタジオを検索して追加してください
                    </p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Date and Time Selection */}
          <Card>
            <CardHeader className="border-b">
              <CardTitle className="text-2xl">日時を選択</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 pt-6">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {/* 日付選択 */}
                <Popover>
                  <PopoverTrigger asChild>
                    <Button
                      variant="outline"
                      className={cn(
                        "w-full justify-start",
                        !selectedDate && "text-muted-foreground"
                      )}
                    >
                      <CalendarIcon className="mr-2 h-4 w-4" />
                      {selectedDate
                        ? format(selectedDate, "yyyy年MM月dd日 (eee)", {
                            locale: ja,
                          })
                        : "日付を選択"}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0" align="start">
                    <CalendarComponent
                      mode="single"
                      selected={selectedDate}
                      onSelect={setSelectedDate}
                      initialFocus
                      disabled={(date) =>
                        date < new Date(new Date().setHours(0, 0, 0, 0)) ||
                        date >
                          new Date(
                            new Date().setMonth(new Date().getMonth() + 2)
                          )
                      }
                    />
                  </PopoverContent>
                </Popover>

                {/* 時間選択 */}
                <Select value={selectedTime} onValueChange={setSelectedTime}>
                  <SelectTrigger
                    className={cn(
                      "w-full",
                      !selectedTime && "text-muted-foreground"
                    )}
                  >
                    <div className="flex items-center">
                      <Clock className="mr-2 h-4 w-4" />
                      <SelectValue placeholder="予約開始時間を選択" />
                    </div>
                  </SelectTrigger>
                  <SelectContent>
                    {timeOptions.map((time) => (
                      <SelectItem key={time} value={time}>
                        {time}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>

                {/* 利用時間 */}
                <Select
                  value={selectedDuration}
                  onValueChange={setSelectedDuration}
                >
                  <SelectTrigger
                    className={cn(
                      "w-full",
                      !selectedDuration && "text-muted-foreground"
                    )}
                  >
                    <div className="flex items-center">
                      <Clock className="mr-2 h-4 w-4" />
                      <SelectValue placeholder="利用時間を選択" />
                    </div>
                  </SelectTrigger>
                  <SelectContent>
                    {durationOptions.map((duration) => (
                      <SelectItem key={duration} value={duration}>
                        {duration}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <Button
                className="w-full"
                disabled={
                  !selectedDate || !selectedTime || selectedStudios.length === 0
                }
                onClick={handleSearch}
              >
                空き状況を検索
              </Button>
            </CardContent>
          </Card>
          {/* Search Results */}
          {searchPerformed && (
            <Card>
              <CardHeader className="border-b">
                <CardTitle className="text-2xl">空き状況</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6 pt-6">
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {selectedStudios.map((studio) => (
                    <Card key={studio.id}>
                      <CardContent className="p-6">
                        <div className="space-y-4">
                          <div>
                            <h3 className="text-lg font-semibold">
                              {studio.name}
                            </h3>
                            <div className="mt-4 space-y-2 text-sm">
                              <div className="flex items-center text-muted-foreground">
                                <MapPin className="h-4 w-4 mr-2" />
                                {studio.address}
                              </div>
                              <div className="flex items-center text-muted-foreground">
                                <Clock className="h-4 w-4 mr-2" />
                                {studio.hours}
                              </div>
                              <div className="flex items-center">
                                <Calendar className="h-4 w-4 mr-2" />
                                <span className="text-primary">
                                  {selectedDate &&
                                    format(selectedDate, "yyyy/MM/dd")}{" "}
                                  {selectedTime}
                                </span>
                              </div>
                              <Badge
                                variant="secondary"
                                className="bg-emerald-100 text-emerald-700 hover:bg-emerald-100"
                              >
                                予約可能
                              </Badge>
                            </div>
                          </div>
                          <div className="grid grid-cols-2 gap-4">
                            <Button variant="gradient">Web予約</Button>
                            <Button variant="outline">電話予約</Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={resetSearch}
                >
                  新しく検索
                </Button>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Footer */}
        <footer className="mt-16 pt-8 border-t">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">スタジオナビ</h3>
              <p className="text-sm text-muted-foreground">
                音楽スタジオの検索・予約を、もっと快適に。
              </p>
            </div>
            <div>
              <h4 className="font-medium mb-4">サービス</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>スタジオ検索</li>
                <li>料金案内</li>
                <li>設備情報</li>
                <li>ご利用ガイド</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium mb-4">サポート</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>よくある質問</li>
                <li>お問い合わせ</li>
                <li>利用規約</li>
                <li>プライバシーポリシー</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium mb-4">運営会社</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>会社概要</li>
                <li>採用情報</li>
                <li>ニュース</li>
                <li>ブログ</li>
              </ul>
            </div>
          </div>
          <div className="mt-8 pt-8 border-t">
            <p className="text-center text-sm text-muted-foreground">
              © 2024 スタジオナビ. All rights reserved.
            </p>
          </div>
        </footer>
      </main>
    </div>
  );
};

export default MusicStudioBookingApp;
