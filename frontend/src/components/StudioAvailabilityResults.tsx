import React, { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Globe, Phone, MapPin, Clock } from "lucide-react";
import { format } from "date-fns";
import { ja } from "date-fns/locale";
import _ from "lodash";

interface Studio {
  id: number;
  name: string;
  address: string;
  hours: string;
  selfBookingStart: string;
}

interface AvailableTimeSlot {
  start: string;
  end: string;
  roomName: string;
  startsAtThirty: boolean;
}

interface ApiErrorResponse {
  status: "error";
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}

interface ApiSuccessResponse {
  status: "success";
  data: {
    studioId: string;
    studioName: string;
    date: string;
    availableRanges: AvailableTimeSlot[];
    meta: {
      timezone: string;
    };
  };
}

type ApiResponse = ApiSuccessResponse | ApiErrorResponse;

interface StudioAvailability {
  studioId: number;
  studioName: string;
  availableRanges: AvailableTimeSlot[];
}

interface StudioAvailabilityResultsProps {
  studios: Studio[];
  selectedDate: Date;
  searchStartTime: string;
  searchEndTime: string;
  selectedDuration: string;
  onReset: () => void;
}

interface GroupedAvailability {
  roomName: string;
  timeRanges: string[];
}

class ApiError extends Error {
  constructor(
    message: string,
    public code: string,
    public details?: Record<string, unknown>
  ) {
    super(message);
    this.name = "ApiError";
  }
}

const fetchStudioAvailability = async (
  studioId: number,
  date: string,
  start: string,
  end: string,
  duration: number
): Promise<StudioAvailability> => {
  const params = new URLSearchParams({
    date,
    start,
    end,
    duration: duration.toString(),
  });

  try {
    const response = await fetch(
      `http://127.0.0.1:8000/api/studios/${studioId}/availability?${params}`
    );

    const data: ApiResponse = await response.json();

    if (!response.ok || data.status === "error") {
      const errorData = data as ApiErrorResponse;
      throw new ApiError(
        errorData.error.message,
        errorData.error.code,
        errorData.error.details
      );
    }

    const successData = data as ApiSuccessResponse;
    return {
      studioId: parseInt(successData.data.studioId),
      studioName: successData.data.studioName,
      availableRanges: successData.data.availableRanges,
    };
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new Error("空き状況の取得に失敗しました");
  }
};

const formatTimeRanges = (
  ranges: AvailableTimeSlot[]
): GroupedAvailability[] => {
  // 部屋名でグループ化
  const groupedByRoom = _.groupBy(ranges, "roomName");

  return Object.entries(groupedByRoom).map(([roomName, slots]) => {
    // 時間帯を文字列として整形
    const timeRanges = slots.map((slot) => `${slot.start}〜${slot.end}`);

    return {
      roomName: roomName || "指定なし",
      timeRanges,
    };
  });
};

const StudioAvailabilityResults: React.FC<StudioAvailabilityResultsProps> = ({
  studios,
  selectedDate,
  searchStartTime,
  searchEndTime,
  selectedDuration,
  onReset,
}) => {
  const [availabilityData, setAvailabilityData] = useState<
    StudioAvailability[]
  >([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<{
    message: string;
    code?: string;
    details?: Record<string, unknown>;
  } | null>(null);

  useEffect(() => {
    const fetchAllStudioAvailability = async () => {
      setLoading(true);
      setError(null);

      try {
        const formattedDate = format(selectedDate, "yyyy-MM-dd");
        const durationHours = parseInt(selectedDuration.replace("時間", ""));

        const availabilityPromises = studios.map((studio) =>
          fetchStudioAvailability(
            studio.id,
            formattedDate,
            searchStartTime,
            searchEndTime,
            durationHours
          )
        );

        const results = await Promise.all(availabilityPromises);
        setAvailabilityData(results);
      } catch (err) {
        if (err instanceof ApiError) {
          setError({
            message: err.message,
            code: err.code,
            details: err.details,
          });
        } else {
          setError({
            message:
              "空き状況の取得中にエラーが発生しました。しばらく経ってから再度お試しください。",
          });
        }
      } finally {
        setLoading(false);
      }
    };

    fetchAllStudioAvailability();
  }, [studios, selectedDate, searchStartTime, searchEndTime, selectedDuration]);

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-[200px]">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto"></div>
          <p className="text-sm text-muted-foreground">空き状況を確認中...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center space-y-4 p-6">
        <div className="space-y-2">
          <p className="text-red-600">{error.message}</p>
          {error.code && (
            <p className="text-sm text-muted-foreground">
              エラーコード: {error.code}
            </p>
          )}
        </div>
        <Button variant="outline" onClick={onReset}>
          再試行
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
        <span>
          {format(selectedDate, "yyyy年MM月dd日 (eee)", { locale: ja })}
        </span>
        <span>•</span>
        <span>
          {searchStartTime} 〜 {searchEndTime}
        </span>
        <span>•</span>
        <span>{selectedDuration}</span>
      </div>

      <div className="grid grid-cols-1 gap-6">
        {studios.map((studio) => {
          const studioAvailability = availabilityData.find(
            (a) => a.studioId === studio.id
          );
          const availableRanges = studioAvailability?.availableRanges || [];
          const groupedAvailabilities = formatTimeRanges(availableRanges);

          return (
            <Card key={studio.id} className="overflow-hidden">
              <CardContent className="p-6">
                <div className="space-y-4">
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="text-lg font-semibold">{studio.name}</h3>
                      <div className="mt-2 space-y-1">
                        <div className="flex items-center text-sm text-muted-foreground">
                          <MapPin className="h-4 w-4 mr-2" />
                          <span>{studio.address}</span>
                        </div>
                        <div className="flex items-center text-sm text-muted-foreground">
                          <Clock className="h-4 w-4 mr-2" />
                          <span>{studio.hours}</span>
                        </div>
                      </div>
                    </div>
                    <Badge
                      variant={
                        availableRanges.length > 0 ? "secondary" : "destructive"
                      }
                      className={
                        availableRanges.length > 0
                          ? "bg-emerald-100 text-emerald-700 hover:bg-emerald-100"
                          : ""
                      }
                    >
                      {availableRanges.length > 0 ? "空きあり" : "満室"}
                    </Badge>
                  </div>

                  {groupedAvailabilities.length > 0 && (
                    <div className="space-y-3">
                      <p className="text-sm font-medium">予約可能な時間帯</p>
                      <div className="space-y-2">
                        {groupedAvailabilities.map((group, roomIdx) => (
                          <div key={roomIdx} className="space-y-1">
                            <p className="text-sm font-medium text-muted-foreground">
                              {group.roomName}:
                            </p>
                            <div className="flex flex-wrap gap-2">
                              {group.timeRanges.map((timeRange, timeIdx) => (
                                <Badge
                                  key={timeIdx}
                                  variant="outline"
                                  className="text-xs"
                                >
                                  {timeRange}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="grid grid-cols-2 gap-3 mt-4">
                    <Button
                      className="w-full flex items-center justify-center gap-2"
                      variant={
                        availableRanges.length > 0 ? "gradient" : "secondary"
                      }
                      disabled={availableRanges.length === 0}
                    >
                      <Globe className="h-4 w-4" />
                      <span>Web予約</span>
                    </Button>
                    <Button
                      variant="outline"
                      className="w-full flex items-center justify-center gap-2"
                    >
                      <Phone className="h-4 w-4" />
                      <span>電話予約</span>
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div className="flex justify-center mt-6">
        <Button
          variant="outline"
          className="w-full sm:w-auto min-w-[200px]"
          onClick={onReset}
        >
          新しく検索
        </Button>
      </div>
    </div>
  );
};

export default StudioAvailabilityResults;
