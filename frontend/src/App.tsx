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
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
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
  SheetDescription,
} from "@/components/ui/sheet";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { format } from "date-fns";
import { cn } from "@/lib/utils";
import { Calendar as CalendarComponent } from "@/components/ui/calendar";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { ja } from "date-fns/locale";
import { StudioSearchComponent } from "@/components/StudioSearchComponent";
import StudioAvailabilityResults from "./components/StudioAvailabilityResults";
import { SignupForm } from "@/components/SignupForm";
import { Toaster } from "@/components/ui/toaster";

interface Studio {
  id: number;
  name: string;
  address: string;
  hours: string;
  selfBookingStart: string;
}

const PRESET_STUDIOS: Studio[] = [
  {
    id: 1,
    name: "パッドスタジオ",
    address: "東京都渋谷区神南1-2-3",
    hours: "10:00 - 26:00",
    selfBookingStart: "前日 12:00〜",
  },
  {
    id: 2,
    name: "ベースオントップ アメ村店",
    address: "東京都新宿区高田馬場4-5-6",
    hours: "9:00 - 27:00",
    selfBookingStart: "3日前 10:00〜",
  },
  {
    id: 97,
    name: "Rock Heaven",
    address: "東京都北区王子7-8-9",
    hours: "10:00 - 25:00",
    selfBookingStart: "当日 0:00〜",
  },
  {
    id: 98,
    name: "Studio Mission",
    address: "東京都世田谷区下北沢1-10-12",
    hours: "11:00 - 26:00",
    selfBookingStart: "2日前 15:00〜",
  },
  {
    id: 99,
    name: "Jam Station",
    address: "東京都港区六本木13-14-15",
    hours: "8:00 - 27:00",
    selfBookingStart: "前日 18:00〜",
  },
];

const timeOptions = Array.from({ length: 25 }, (_, i) => {
  const hour = i.toString().padStart(2, "0");
  return `${hour}:00`;
});

const FOOTER_SECTIONS = [
  {
    title: "サービス",
    links: [
      { label: "スタジオ検索", href: "/search" },
      { label: "料金案内", href: "/pricing" },
      { label: "設備情報", href: "/facilities" },
      { label: "ご利用ガイド", href: "/guide" },
    ],
  },
  {
    title: "サポート",
    links: [
      { label: "よくある質問", href: "/faq" },
      { label: "お問い合わせ", href: "/contact" },
      { label: "利用規約", href: "/terms" },
      { label: "プライバシーポリシー", href: "/privacy" },
    ],
  },
  {
    title: "運営会社",
    links: [
      { label: "会社概要", href: "/company" },
      { label: "採用情報", href: "/careers" },
      { label: "ニュース", href: "/news" },
      { label: "ブログ", href: "/blog" },
    ],
  },
];

const durationOptions = ["1時間", "2時間", "3時間", "4時間", "5時間"];
const MusicStudioBookingApp = () => {
  const [selectedStudios, setSelectedStudios] = useState([
    PRESET_STUDIOS[0],
    PRESET_STUDIOS[1],
  ]);
  const [selectedDate, setSelectedDate] = useState<Date>();
  const [searchStartTime, setSearchStartTime] = useState("");
  const [searchEndTime, setSearchEndTime] = useState("");
  const [selectedDuration, setSelectedDuration] = useState("");
  const [searchPerformed, setSearchPerformed] = useState(false);
  const [isSignup, setIsSignup] = useState(false);

  const validateSearchConditions = () => {
    if (
      !selectedDate ||
      !searchStartTime ||
      !searchEndTime ||
      !selectedDuration ||
      selectedStudios.length === 0
    ) {
      alert("全ての項目を入力してください");
      return false;
    }

    const startIndex = timeOptions.indexOf(searchStartTime);
    const endIndex = timeOptions.indexOf(searchEndTime);
    const durationHours = parseInt(selectedDuration.replace("時間", ""));

    if (startIndex >= endIndex) {
      alert("終了時刻は開始時刻より後の時間を選択してください");
      return false;
    }

    if (endIndex - startIndex < durationHours) {
      alert(
        `検索時間範囲（${searchStartTime}～${searchEndTime}）が予約時間（${selectedDuration}）より短くなっています`
      );
      return false;
    }

    return true;
  };

  const addStudio = (studio: Studio) => {
    if (selectedStudios.length < 5) {
      setSelectedStudios((prev) => [...prev, studio]);
    }
  };

  const removeStudio = (studioId: number) => {
    setSelectedStudios((prev) => prev.filter((s) => s.id !== studioId));
  };

  const handleSearch = () => {
    if (validateSearchConditions()) {
      setSearchPerformed(true);
    }
  };

  const resetSearch = () => {
    setSelectedStudios([]);
    setSelectedDate(undefined);
    setSearchStartTime("");
    setSearchEndTime("");
    setSelectedDuration("");
    setSearchPerformed(false);
  };

  // スタジオが選択された時の処理
  const handleStudioSelect = (studio: Studio) => {
    // 既に選択されているスタジオかチェック
    const isAlreadySelected = selectedStudios.some(
      (selected) => selected.id === studio.id
    );

    if (!isAlreadySelected) {
      setSelectedStudios((prev) => [...prev, studio]);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto max-w-5xl px-2 sm:px-6">
        {/* Header */}
        <header className="bg-background border-b">
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
              <Button
                variant="gradient"
                className="h-9"
                onClick={() => setIsSignup(true)}
              >
                <User className="h-4 w-4 mr-2" />
                新規登録
              </Button>
            </div>

            {/* Mobile Menu */}
            <div className="md:hidden">
              <Sheet>
                <SheetTrigger asChild>
                  <Button variant="outline" size="icon" className="h-9 w-9">
                    <Menu className="h-4 w-4" />
                  </Button>
                </SheetTrigger>
                <SheetContent side="right">
                  <SheetHeader className="text-left">
                    <SheetTitle>スタジオナビ</SheetTitle>
                    <SheetDescription>
                      音楽スタジオの検索・予約を、もっと快適に。
                    </SheetDescription>
                  </SheetHeader>
                  <div className="py-4">
                    <div className="pt-4">
                      <div className="text-sm font-medium text-muted-foreground">
                        アカウント
                      </div>
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
                        onClick={() => setIsSignup(true)}
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
        </header>

        {/* Main content */}
        {isSignup ? (
          <SignupForm />
        ) : (
          <main className="py-4 px-2 sm:py-6 sm:px-6">
            <div className="relative overflow-hidden">
              {/* Decorative elements */}
              <div className="absolute top-4 left-4 w-32 sm:w-48 h-32 sm:h-48 bg-primary/10 rounded-full blur-3xl opacity-20" />
              <div className="absolute bottom-4 right-4 w-32 sm:w-48 h-32 sm:h-48 bg-primary/10 rounded-full blur-3xl opacity-20" />

              <div className="relative pt-6 sm:pt-8 pb-6 sm:pb-8 text-center px-4">
                {" "}
                {/* パディングを調整 */}
                <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold text-foreground">
                  スタジオ予約を、
                  <br className="sm:hidden" />
                  もっと簡単に
                </h1>
                <p className="mt-2 sm:mt-3 text-sm sm:text-base md:text-lg text-muted-foreground max-w-2xl mx-auto">
                  {" "}
                  {/* マージンを調整 */}
                  複数のスタジオの
                  <br className="sm:hidden" />
                  空き状況を一括確認
                </p>
                {/* Step indicators - 横並びのまま */}
                <div className="flex items-center justify-center mt-8 sm:mt-12 max-w-2xl mx-auto px-4">
                  <div className="flex-1 relative">
                    <div className="h-0.5 bg-gradient-to-r from-transparent via-muted to-muted absolute w-full top-5 sm:top-6" />
                    <div className="relative flex flex-col items-center">
                      <Badge
                        variant="gradient"
                        className="w-10 h-10 sm:w-12 sm:h-12 rounded-full flex items-center justify-center text-sm sm:text-base p-0"
                      >
                        1
                      </Badge>
                      <p className="mt-2 text-xs sm:text-sm font-medium whitespace-nowrap">
                        スタジオを選ぶ
                      </p>
                    </div>
                  </div>

                  <div className="flex-1 relative">
                    <div className="h-0.5 bg-gradient-to-r from-muted via-muted to-muted absolute w-full top-5 sm:top-6" />
                    <div className="relative flex flex-col items-center">
                      <Badge
                        variant="gradient"
                        className="w-10 h-10 sm:w-12 sm:h-12 rounded-full flex items-center justify-center text-sm sm:text-base p-0"
                      >
                        2
                      </Badge>
                      <p className="mt-2 text-xs sm:text-sm font-medium whitespace-nowrap">
                        日時を選ぶ
                      </p>
                    </div>
                  </div>

                  <div className="flex-1 relative">
                    <div className="h-0.5 bg-gradient-to-r from-muted via-transparent to-transparent absolute w-full top-5 sm:top-6" />
                    <div className="relative flex flex-col items-center">
                      <Badge
                        variant="gradient"
                        className="w-10 h-10 sm:w-12 sm:h-12 rounded-full flex items-center justify-center text-sm sm:text-base p-0"
                      >
                        3
                      </Badge>
                      <p className="mt-2 text-xs sm:text-sm font-medium whitespace-nowrap">
                        検索する
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

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
                        複数のスタジオを同時に検索できます{" "}
                        <br className="sm:hidden" />
                        （最大5件）
                      </p>
                    </div>
                    <Badge variant="secondary">
                      {selectedStudios.length}/5
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4 px-3 sm:px-6">
                  {/* 検索バー */}
                  <StudioSearchComponent
                    onStudioSelect={handleStudioSelect}
                    selectedCount={selectedStudios.length}
                    maxSelections={5}
                    selectedStudios={selectedStudios}
                  />

                  {/* 選択されたスタジオのリスト */}
                  <div className="space-y-2">
                    {selectedStudios.map((studio) => (
                      <Card key={studio.id} className="overflow-hidden">
                        <div className="p-4 sm:p-6">
                          <div className="flex items-stSart gap-4">
                            <div className="flex-1 min-w-0">
                              <h3 className="text-base font-semibold truncate">
                                {studio.name}
                              </h3>
                              <div className="mt-2 space-y-1">
                                <div className="flex items-center text-sm text-muted-foreground">
                                  <MapPin className="h-3 w-3 mr-2 flex-shrink-0" />
                                  <span className="truncate">
                                    {studio.address}
                                  </span>
                                </div>
                                <div className="flex items-center text-sm text-muted-foreground">
                                  <Clock className="h-3 w-3 mr-2 flex-shrink-0" />
                                  <span className="truncate">
                                    {studio.hours}
                                  </span>
                                </div>
                                <div className="flex items-center text-sm text-muted-foreground">
                                  <Calendar className="h-3 w-3 mr-2 flex-shrink-0" />
                                  <span className="truncate">
                                    予約開始：{studio.selfBookingStart}
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
              {/* 日時選択カード以降のコンポーネント */}
              <Card>
                <CardHeader>
                  <div className="space-y-1.5">
                    <CardTitle className="text-2xl">日時を選択</CardTitle>
                    <p className="text-sm text-muted-foreground">
                      希望する日付と時間帯を選択してください
                    </p>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4 px-3 sm:px-6">
                  <div className="grid grid-cols-1 sm:grid-cols-12 gap-4">
                    {/* 日付選択 - 5列 */}
                    <div className="sm:col-span-5">
                      <Label className="text-sm mb-2">日付</Label>
                      <Popover>
                        <PopoverTrigger asChild>
                          <Button
                            variant="outline"
                            className={cn(
                              "w-full justify-start text-left",
                              !selectedDate && "text-muted-foreground"
                            )}
                          >
                            <CalendarIcon className="h-4 w-4 mr-2 flex-shrink-0" />
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
                              date <
                                new Date(new Date().setHours(0, 0, 0, 0)) ||
                              date >
                                new Date(
                                  new Date().setMonth(new Date().getMonth() + 2)
                                )
                            }
                          />
                        </PopoverContent>
                      </Popover>
                    </div>

                    {/* 時間帯と予約時間 - 7列 */}
                    <div className="sm:col-span-7">
                      <Label className="text-sm mb-2">時間帯・予約時間</Label>
                      <div className="grid grid-cols-1 sm:grid-cols-7 gap-4">
                        {/* 時間帯 - 5列（常に横並び） */}
                        <div className="sm:col-span-5">
                          <div className="flex items-center gap-2">
                            <div className="flex-1">
                              <Select
                                value={searchStartTime}
                                onValueChange={setSearchStartTime}
                              >
                                <SelectTrigger
                                  className={cn(
                                    !searchStartTime && "text-muted-foreground"
                                  )}
                                >
                                  <SelectValue placeholder="開始時刻" />
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

                            <span className="flex-shrink-0 text-muted-foreground">
                              〜
                            </span>

                            <div className="flex-1">
                              <Select
                                value={searchEndTime}
                                onValueChange={setSearchEndTime}
                              >
                                <SelectTrigger
                                  className={cn(
                                    !searchEndTime && "text-muted-foreground"
                                  )}
                                >
                                  <SelectValue placeholder="終了時刻" />
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
                          </div>
                        </div>

                        {/* 予約時間 - 2列 */}
                        <div className="sm:col-span-2">
                          <Select
                            value={selectedDuration}
                            onValueChange={setSelectedDuration}
                          >
                            <SelectTrigger
                              className={cn(
                                !selectedDuration && "text-muted-foreground"
                              )}
                            >
                              <SelectValue placeholder="予約時間" />
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
                    </div>
                  </div>

                  <Button
                    className="w-full"
                    variant="gradient"
                    onClick={handleSearch}
                  >
                    空き状況を検索
                  </Button>
                </CardContent>
              </Card>

              {/* 検索結果 */}
              {searchPerformed && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-2xl">検索結果</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <StudioAvailabilityResults
                      studios={selectedStudios}
                      selectedDate={selectedDate!}
                      searchStartTime={searchStartTime}
                      searchEndTime={searchEndTime}
                      selectedDuration={selectedDuration}
                      onReset={resetSearch}
                    />
                  </CardContent>
                </Card>
              )}
            </div>
            {/* Footer */}
            <footer
              className="mt-16 w-full border-t"
              role="contentinfo"
              aria-label="サイトフッター"
            >
              <div className="container mx-auto max-w-5xl px-4">
                <div className="pt-8">
                  {/* モバイルレイアウト */}
                  <div className="md:hidden space-y-6">
                    <div className="space-y-4">
                      <h2 className="text-lg font-semibold">スタジオナビ</h2>
                      <p className="text-sm text-muted-foreground">
                        音楽スタジオの検索・予約を、もっと快適に。
                      </p>
                    </div>

                    <Accordion
                      type="single"
                      collapsible
                      className="w-full"
                      defaultValue={FOOTER_SECTIONS[0].title}
                    >
                      {FOOTER_SECTIONS.map((section) => (
                        <AccordionItem
                          key={section.title}
                          value={section.title}
                        >
                          <AccordionTrigger className="text-base font-medium">
                            {section.title}
                          </AccordionTrigger>
                          <AccordionContent>
                            <nav aria-label={`${section.title}ナビゲーション`}>
                              <ul className="space-y-3 py-2">
                                {section.links.map((link) => (
                                  <li key={link.label}>
                                    <a
                                      href={link.href}
                                      className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                                    >
                                      {link.label}
                                    </a>
                                  </li>
                                ))}
                              </ul>
                            </nav>
                          </AccordionContent>
                        </AccordionItem>
                      ))}
                    </Accordion>
                  </div>

                  {/* デスクトップレイアウト */}
                  <div className="hidden md:grid md:grid-cols-4 gap-8">
                    <div className="space-y-4">
                      <h2 className="text-lg font-semibold">スタジオナビ</h2>
                      <p className="text-sm text-muted-foreground">
                        音楽スタジオの検索・予約を、もっと快適に。
                      </p>
                    </div>
                    {FOOTER_SECTIONS.map((section) => (
                      <div key={section.title}>
                        <h2 className="font-medium mb-4">{section.title}</h2>
                        <nav aria-label={`${section.title}ナビゲーション`}>
                          <ul className="space-y-2">
                            {section.links.map((link) => (
                              <li key={link.label}>
                                <a
                                  href={link.href}
                                  className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                                >
                                  {link.label}
                                </a>
                              </li>
                            ))}
                          </ul>
                        </nav>
                      </div>
                    ))}
                  </div>
                </div>

                {/* コピーライト */}
                <div className="mt-8 pt-8 border-t">
                  <p className="text-center text-sm text-muted-foreground">
                    &copy; {new Date().getFullYear()} スタジオナビ. All rights
                    reserved.
                  </p>
                </div>
              </div>
            </footer>
          </main>
        )}
      </div>
      <Toaster />
    </div>
  );
};

export default MusicStudioBookingApp;
