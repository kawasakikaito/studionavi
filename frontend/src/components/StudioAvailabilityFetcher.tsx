import { useEffect, useState } from "react";
import axios from "axios";
import { format } from "date-fns";
import {
  Studio,
  AvailableTimeSlot,
  ApiError,
  ApiErrorResponse,
  ApiSuccessResponse,
  StudioAvailability,
  FetchResult,
} from "./StudioAvailabilityResults";
import apiClient from "@/lib/apiClient";

const BATCH_SIZE = 1;
const FETCH_DELAY = 200;

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

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
    if (axios.isAxiosError(error)) {
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
      throw new ApiError(error.message, "UNKNOWN_ERROR", {
        originalError: error.toString()
      });
    }
    throw new ApiError("予期せぬエラーが発生しました", "UNKNOWN_ERROR", {
      error: String(error)
    });
  }
};

export const useStudioAvailability = (
  studios: Studio[],
  selectedDate: Date,
  searchStartTime: string,
  searchEndTime: string,
  selectedDuration: string
) => {
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
              setAvailabilityData((prev) => [...prev, result.data]);
              if (typeof result.error?.message === "string") {
                setErrors((prev) => {
                  const newErrors = new Map(prev);
                  newErrors.set(result.data.studioId, result.error!.message);
                  return newErrors;
                });
              }
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

  return {
    availabilityData,
    loading,
    progress,
    errors,
  };
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
      let errorResult: {
        message: string;
        code: string;
        details?: Record<string, unknown>;
      } = {
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
