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
  ChevronRight,
  Globe,
  Phone,
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
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
  SheetClose,
  SheetDescription,
} from "@/components/ui/sheet";
import { format } from "date-fns";
import { cn } from "@/lib/utils";
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
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <h1 className="text-xl font-bold">スタジオナビ</h1>
              </div>
              {/* Desktop Navigation */}
              <nav className="hidden md:ml-6 md:flex md:space-x-8">
                <a className="border-primary text-foreground inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium">
                  スタジオを探す
                </a>
              </nav>
            </div>
            {/* Desktop Buttons */}
            <div className="hidden md:flex md:items-center md:space-x-4">
              <Button variant="outline" className="h-9">
                <LogIn className="h-4 w-4 mr-2" />
                ログイン
              </Button>
              <Button variant="gradient" className="h-9">
                <User className="h-4 w-4 mr-2" />
                新規登録
              </Button>
            </div>

            {/* Mobile Menu - Sheetコンポーネントを更新 */}
            <div className="flex items-center md:hidden">
              <Sheet>
                <SheetTrigger asChild>
                  <Button variant="ghost" size="icon" className="h-9 w-9">
                    <Menu className="h-5 w-5" />
                  </Button>
                </SheetTrigger>
                <SheetContent side="right">
                  <SheetHeader>
                    <SheetTitle>メニュー</SheetTitle>
                    <SheetDescription>
                      スタジオナビのメニューです。アカウント管理や各種設定にアクセスできます。
                    </SheetDescription>
                  </SheetHeader>
                  <div className="flex flex-col space-y-4 mt-6">
                    <div className="space-y-3">
                      <a className="flex items-center text-sm font-medium text-primary">
                        スタジオを探す
                      </a>
                    </div>
                    <div className="pt-6 border-t space-y-3">
                      <Button
                        variant="outline"
                        className="w-full justify-start h-9"
                      >
                        <LogIn className="h-4 w-4 mr-2" />
                        ログイン
                      </Button>
                      <Button
                        variant="gradient"
                        className="w-full justify-start h-9"
                      >
                        <User className="h-4 w-4 mr-2" />
                        新規登録
                      </Button>
                    </div>
                  </div>
                </SheetContent>
              </Sheet>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="container mx-auto py-4 px-4 sm:py-6 sm:px-6">
        <div className="space-y-4 sm:space-y-6">
          {/* スタジオ選択セクション */}
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <div className="space-y-1">
                  <CardTitle className="text-xl sm:text-2xl">
                    スタジオを選択
                  </CardTitle>
                  <p className="text-sm text-muted-foreground">
                    複数のスタジオを同時に検索できます（最大5件）
                  </p>
                </div>
                <Badge variant="secondary">{selectedStudios.length}/5</Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* 検索バー */}
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

                {/* 検索結果ドロップダウン */}
                {isSearchResultsOpen && searchResults.length > 0 && (
                  <Card className="absolute z-50 w-full mt-2">
                    <CardContent className="p-0">
                      {searchResults.map((studio) => (
                        <Button
                          key={studio.id}
                          onClick={() => addStudio(studio)}
                          variant="ghost"
                          className="w-full justify-start h-auto py-3 px-4 hover:bg-accent"
                        >
                          <div className="flex-1">
                            <div className="font-medium">{studio.name}</div>
                            <div className="text-sm text-muted-foreground flex items-center mt-1">
                              <MapPin className="h-3 w-3 mr-1 flex-shrink-0" />
                              {studio.address}
                            </div>
                          </div>
                          <ChevronRight className="h-4 w-4 text-muted-foreground ml-2" />
                        </Button>
                      ))}
                    </CardContent>
                  </Card>
                )}
              </div>

              {/* 選択されたスタジオのリスト */}
              <div className="space-y-2">
                {selectedStudios.map((studio) => (
                  <Card key={studio.id} className="overflow-hidden">
                    <div className="p-4 sm:p-6">
                      <div className="flex items-start gap-4">
                        <div className="flex-1 min-w-0">
                          <h3 className="text-base font-semibold truncate">
                            {studio.name}
                          </h3>
                          <div className="mt-2 space-y-1">
                            <div className="flex items-center text-sm text-muted-foreground">
                              <MapPin className="h-3 w-3 mr-2 flex-shrink-0" />
                              <span className="truncate">{studio.address}</span>
                            </div>
                            <div className="flex items-center text-sm text-muted-foreground">
                              <Clock className="h-3 w-3 mr-2 flex-shrink-0" />
                              <span className="truncate">{studio.hours}</span>
                            </div>
                            <div className="flex items-center text-sm text-muted-foreground">
                              <Calendar className="h-3 w-3 mr-2 flex-shrink-0" />
                              <span className="truncate">
                                予約開始：{studio.bookingStart}
                              </span>
                            </div>
                          </div>
                        </div>
                        <Button
                          variant="destructive"
                          size="icon"
                          className="flex-shrink-0"
                          onClick={() => removeStudio(studio.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </Card>
                ))}

                {selectedStudios.length === 0 && (
                  <div className="text-center py-8 bg-muted rounded-lg">
                    <Plus className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
                    <p className="text-sm text-muted-foreground">
                      スタジオを検索して追加してください
                    </p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Date and Time Selection */}
          <Card>
            <CardHeader>
              <div className="space-y-1.5">
                <CardTitle className="text-2xl">日時を選択</CardTitle>
                <p className="text-sm text-muted-foreground">
                  2ヶ月先までの予約が可能です
                </p>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-10 gap-4">
                {/* Date Picker */}
                <div className="col-span-4">
                  <Popover>
                    <PopoverTrigger asChild>
                      <Button
                        variant="outline"
                        className={cn(
                          "w-full justify-start text-left",
                          !selectedDate && "text-muted-foreground"
                        )}
                      >
                        <CalendarIcon className="h-4 w-4" />
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
                </div>

                {/* Time Selection */}
                <div className="col-span-3">
                  <Select value={selectedTime} onValueChange={setSelectedTime}>
                    <SelectTrigger
                      className={cn(
                        "w-full text-left justify-start",
                        !selectedTime && "text-muted-foreground"
                      )}
                    >
                      <Clock className="mr-2 h-4 w-4" />
                      <SelectValue placeholder="開始時間を選択" />
                    </SelectTrigger>
                    <SelectContent>
                      {timeOptions.map((time) => (
                        <SelectItem key={time} value={time}>
                          {time}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Duration Selection */}
                <div className="col-span-3">
                  <Select
                    value={selectedDuration}
                    onValueChange={setSelectedDuration}
                  >
                    <SelectTrigger
                      className={cn(
                        "w-full text-left justify-start",
                        !selectedDuration && "text-muted-foreground"
                      )}
                    >
                      <Clock className="mr-2 h-4 w-4" />
                      <SelectValue placeholder="利用時間を選択" />
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
              </div>

              <Button
                className="w-full"
                variant="gradient"
                disabled={
                  !selectedDate ||
                  !selectedTime ||
                  !selectedDuration ||
                  selectedStudios.length === 0
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
              <CardHeader className="space-y-1">
                <CardTitle className="text-2xl">検索結果</CardTitle>
                <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
                  <span>
                    {format(selectedDate!, "yyyy年MM月dd日 (eee)", {
                      locale: ja,
                    })}
                  </span>
                  <span>•</span>
                  <span>{selectedTime}</span>
                  <span>•</span>
                  <span>{selectedDuration}</span>
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {selectedStudios.map((studio) => (
                    <Card key={studio.id} className="flex flex-col">
                      <CardContent className="flex-1 p-4">
                        <div className="space-y-4">
                          <div>
                            <h3 className="text-lg font-semibold line-clamp-1">
                              {studio.name}
                            </h3>
                            <div className="mt-3 space-y-2">
                              <div className="flex items-start gap-2 text-sm text-muted-foreground">
                                <MapPin className="h-4 w-4 mt-0.5 flex-shrink-0" />
                                <span className="line-clamp-2">
                                  {studio.address}
                                </span>
                              </div>
                              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                <Clock className="h-4 w-4 flex-shrink-0" />
                                <span>{studio.hours}</span>
                              </div>
                              <div className="pt-2">
                                <Badge
                                  variant="secondary"
                                  className="bg-emerald-100 text-emerald-700 hover:bg-emerald-100"
                                >
                                  予約可能
                                </Badge>
                              </div>
                            </div>
                          </div>
                          <div className="grid grid-cols-2 gap-3">
                            <Button
                              className="w-full flex items-center justify-center gap-2"
                              variant="gradient"
                            >
                              <Globe className="h-4 w-4" />
                              <span className="hidden sm:inline">Web</span>予約
                            </Button>
                            <Button
                              variant="outline"
                              className="w-full flex items-center justify-center gap-2"
                            >
                              <Phone className="h-4 w-4" />
                              <span className="hidden sm:inline">電話</span>予約
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
                <div className="flex justify-center mt-6">
                  <Button
                    variant="outline"
                    className="w-full sm:w-auto min-w-[200px]"
                    onClick={resetSearch}
                  >
                    新しく検索
                  </Button>
                </div>
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
