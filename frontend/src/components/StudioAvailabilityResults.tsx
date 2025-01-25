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

import axios, { isAxiosError } from "axios";
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
  } catch (error: unknown) {
    if (isAxiosError(error)) {
      if (error.response?.data?.status === "error") {
        const errorData = error.response.data as ApiErrorResponse;
        throw new ApiError(
          errorData.error.message,
          errorData.error.code,
          errorData.error.details
        );
      }
      throw new ApiError(
        error.message || "APIリクエストに失敗しました",
        error.code || "API_ERROR",
        {
          status: error.response?.status,
          url: error.config?.url,
        }
      );
    }
    if (error instanceof Error) {
      throw new ApiError(error.message, "UNKNOWN_ERROR");
    }
    throw new ApiError("予期せぬエラーが発生しました", "UNKNOWN_ERROR");
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
      <div className="space-y-6 animate-pulse">
        {/* Date and Time Skeleton */}
        <div className="flex flex-wrap items-center gap-2">
          <div className="h-4 bg-gray-200 rounded w-24"></div>
          <div className="h-4 bg-gray-200 rounded w-4"></div>
          <div className="h-4 bg-gray-200 rounded w-32"></div>
          <div className="h-4 bg-gray-200 rounded w-4"></div>
          <div className="h-4 bg-gray-200 rounded w-20"></div>
        </div>

        {/* Studio Cards Skeleton */}
        <div className="grid grid-cols-1 gap-6">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="rounded-lg border bg-white shadow-sm">
              <div className="p-6 space-y-4">
                {/* Header Skeleton */}
                <div className="flex justify-between items-start">
                  <div className="space-y-2">
                    <div className="h-6 bg-gray-200 rounded w-48"></div>
                    <div className="space-y-1">
                      <div className="h-4 bg-gray-200 rounded w-64"></div>
                      <div className="h-4 bg-gray-200 rounded w-56"></div>
                    </div>
                  </div>
                  <div className="h-6 bg-gray-200 rounded w-16"></div>
                </div>

                {/* Time Slots Skeleton */}
                <div className="space-y-3">
                  <div className="h-4 bg-gray-200 rounded w-32"></div>
                  <div className="flex flex-wrap gap-2">
                    {[...Array(4)].map((_, j) => (
                      <div
                        key={j}
                        className="h-6 bg-gray-200 rounded w-20"
                      ></div>
                    ))}
                  </div>
                </div>

                {/* Buttons Skeleton */}
                <div className="grid grid-cols-2 gap-3 mt-4">
                  <div className="h-10 bg-gray-200 rounded"></div>
                  <div className="h-10 bg-gray-200 rounded"></div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Progress Bar */}
        <div className="fixed bottom-0 left-0 right-0 h-1 bg-gray-200">
          <div
            className="h-full bg-blue-500 transition-all duration-300"
            style={{ width: `${progress}%` }}
          ></div>
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
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <svg
                className="h-5 w-5 text-yellow-400"
                viewBox="0 0 20 20"
                fill="currentColor"
                aria-hidden="true"
              >
                <path
                  fillRule="evenodd"
                  d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <div className="ml-3 flex-1">
              <h3 className="text-sm font-medium text-yellow-800">
                一部のスタジオで情報取得に失敗しました
              </h3>
              <div className="mt-2 text-sm text-yellow-700">
                <p>
                  以下のスタジオでエラーが発生しました。再度お試しいただくか、別の方法で予約をお願いします。
                </p>
                <ul className="mt-2 space-y-1 list-disc list-inside">
                  {Array.from(errors.entries()).map(([studioId, message]) => {
                    const studio = studios.find((s) => s.id === studioId);
                    return (
                      <li key={studioId}>
                        {studio?.name || "不明なスタジオ"}: {message}
                      </li>
                    );
                  })}
                </ul>
              </div>
              <div className="mt-4">
                <div className="-mx-2 -my-1.5 flex">
                  <button
                    type="button"
                    onClick={() => window.location.reload()}
                    className="rounded-md bg-yellow-50 px-2 py-1.5 text-sm font-medium text-yellow-800 hover:bg-yellow-100 focus:outline-none focus:ring-2 focus:ring-yellow-600 focus:ring-offset-2 focus:ring-offset-yellow-50"
                  >
                    ページをリロード
                  </button>
                  <button
                    type="button"
                    onClick={onReset}
                    className="ml-3 rounded-md bg-yellow-50 px-2 py-1.5 text-sm font-medium text-yellow-800 hover:bg-yellow-100 focus:outline-none focus:ring-2 focus:ring-yellow-600 focus:ring-offset-2 focus:ring-offset-yellow-50"
                  >
                    新しく検索
                  </button>
                </div>
              </div>
            </div>
          </div>
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
