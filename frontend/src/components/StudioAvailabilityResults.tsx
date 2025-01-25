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

interface FetchError {
  message: string;
  code: string;
  details?: Record<string, unknown>;
}

interface FetchResult {
  data: StudioAvailability;
  error?: FetchError;
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

const BATCH_SIZE = 1; // 一度に処理するスタジオの数
const FETCH_DELAY = 200; // バッチ間の待機時間（ミリ秒）

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

import apiClient from "@/lib/apiClient";

const fetchStudioAvailability = async (
  studioId: number,
  date: string,
  start: string,
  end: string,
  duration: number
): Promise<StudioAvailability> => {
  try {
    const response = await apiClient.get<ApiSuccessResponse>(
      `/studios/${studioId}/availability`,
      {
        params: {
          date,
          start,
          end,
          duration: duration.toString(),
        },
      }
    );

    return {
      studioId: parseInt(response.data.data.studioId),
      studioName: response.data.data.studioName,
      availableRanges: response.data.data.availableRanges,
    };
  } catch (error: any) {
    if (error.response?.data?.status === "error") {
      const errorData = error.response.data as ApiErrorResponse;
      throw new ApiError(
        errorData.error.message,
        errorData.error.code,
        errorData.error.details
      );
    }
    throw new Error("空き状況の取得に失敗しました");
  }
};

const processBatch = async (
  studios: Studio[],
  date: string,
  start: string,
  end: string,
  duration: number,
  onProgress: (result: FetchResult) => void
): Promise<void> => {
  const promises = studios.map(async (studio) => {
    try {
      const data = await fetchStudioAvailability(
        studio.id,
        date,
        start,
        end,
        duration
      );
      onProgress({ data });
    } catch (error) {
      let errorResult: FetchError = {
        message: "空き状況の取得に失敗しました",
        code: "FETCH_ERROR",
      };

      if (error instanceof ApiError) {
        errorResult = {
          message: error.message,
          code: error.code,
          details: error.details,
        };
      }

      onProgress({
        data: {
          studioId: studio.id,
          studioName: studio.name,
          availableRanges: [],
        },
        error: {
          message: errorResult.message,
          code: errorResult.code || "UNKNOWN_ERROR",
          details: errorResult.details,
        },
      });
    }
  });

  await Promise.all(promises);
};

const formatTimeRanges = (
  ranges: AvailableTimeSlot[]
): GroupedAvailability[] => {
  const groupedByRoom = _.groupBy(ranges, "roomName");

  return Object.entries(groupedByRoom).map(([roomName, slots]) => {
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
  const [progress, setProgress] = useState(0);
  const [errors, setErrors] = useState<Map<number, string>>(new Map());

  useEffect(() => {
    const fetchAllStudioAvailability = async () => {
      setLoading(true);
      setProgress(0);
      setErrors(new Map());
      setAvailabilityData([]);

      const formattedDate = format(selectedDate, "yyyy-MM-dd");
      const durationHours = parseInt(selectedDuration.replace("時間", ""));

      // バッチ処理の実行
      for (let i = 0; i < studios.length; i += BATCH_SIZE) {
        const batch = studios.slice(i, i + BATCH_SIZE);

        await processBatch(
          batch,
          formattedDate,
          searchStartTime,
          searchEndTime,
          durationHours,
          (result: FetchResult) => {
            if (result.data) {
              setAvailabilityData(
                (prev) => [...prev, result.data] as StudioAvailability[]
              );
            }
            if (result.error) {
              setErrors((prev) =>
                new Map(prev).set(result.data!.studioId, result.error!.message)
              );
            }
            setProgress((prev) => prev + 100 / studios.length);
          }
        );

        if (i + BATCH_SIZE < studios.length) {
          await sleep(FETCH_DELAY);
        }
      }

      setLoading(false);
    };

    fetchAllStudioAvailability();
  }, [studios, selectedDate, searchStartTime, searchEndTime, selectedDuration]);

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-[200px]">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto"></div>
          <p className="text-sm text-muted-foreground">
            空き状況を確認中... {Math.round(progress)}%
          </p>
        </div>
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

      {errors.size > 0 && (
        <div className="rounded-md bg-yellow-50 p-4 mb-4">
          <p className="text-sm text-yellow-700">
            一部のスタジオで取得に失敗しました。再度お試しください。
          </p>
        </div>
      )}

      <div className="grid grid-cols-1 gap-6">
        {studios.map((studio) => {
          const studioAvailability = availabilityData.find(
            (a) => a.studioId === studio.id
          );
          const availableRanges = studioAvailability?.availableRanges || [];
          const groupedAvailabilities = formatTimeRanges(availableRanges);
          const hasError = errors.has(studio.id);

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
                        hasError
                          ? "outline"
                          : availableRanges.length > 0
                          ? "secondary"
                          : "destructive"
                      }
                      className={
                        hasError
                          ? "border-yellow-500 text-yellow-700"
                          : availableRanges.length > 0
                          ? "bg-emerald-100 text-emerald-700 hover:bg-emerald-100"
                          : ""
                      }
                    >
                      {hasError
                        ? "取得失敗"
                        : availableRanges.length > 0
                        ? "空きあり"
                        : "満室"}
                    </Badge>
                  </div>

                  {hasError && (
                    <p className="text-sm text-yellow-600">
                      {errors.get(studio.id)}
                    </p>
                  )}

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
                      disabled={availableRanges.length === 0 || hasError}
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
