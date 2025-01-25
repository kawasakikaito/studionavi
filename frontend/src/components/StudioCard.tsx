import React from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Globe, Phone, MapPin, Clock } from "lucide-react";
import { Studio, AvailableTimeSlot } from "./StudioAvailabilityResults";
import AvailabilityTimeSlots from "./AvailabilityTimeSlots";

interface StudioCardProps {
  studio: Studio;
  availableRanges: AvailableTimeSlot[];
  hasError: boolean;
  errorMessage?: string;
  onWebReserve: () => void;
  onPhoneReserve: () => void;
}

const StudioCard: React.FC<StudioCardProps> = ({
  studio,
  availableRanges,
  hasError,
  errorMessage,
  onWebReserve,
  onPhoneReserve,
}) => {
  return (
    <Card className="overflow-hidden">
      <CardContent className="p-6">
        <div className="space-y-4">
          <div className="flex justify-between items-start">
            <div>
              <h3 className="text-lg sm:text-xl font-semibold">
                {studio.name}
              </h3>
              <div className="mt-2 sm:mt-3 space-y-1.5 sm:space-y-2">
                <div className="flex items-center text-xs sm:text-sm text-muted-foreground">
                  <MapPin className="h-3.5 w-3.5 sm:h-4 sm:w-4 mr-1.5 sm:mr-2" />
                  <span>{studio.address}</span>
                </div>
                <div className="flex items-center text-xs sm:text-sm text-muted-foreground">
                  <Clock className="h-3.5 w-3.5 sm:h-4 sm:w-4 mr-1.5 sm:mr-2" />
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

          {hasError && errorMessage && (
            <p className="text-sm text-yellow-600">{errorMessage}</p>
          )}

          {availableRanges.length > 0 && (
            <AvailabilityTimeSlots availableRanges={availableRanges} />
          )}

          <div className="grid grid-cols-2 gap-2 sm:gap-3 mt-4">
            <Button
              className="w-full flex items-center justify-center gap-1.5 sm:gap-2 px-2 sm:px-3 py-1.5 sm:py-2"
              variant={availableRanges.length > 0 ? "gradient" : "secondary"}
              disabled={availableRanges.length === 0 || hasError}
              onClick={onWebReserve}
            >
              <Globe className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
              <span className="text-xs sm:text-sm">Web予約</span>
            </Button>
            <Button
              variant="outline"
              className="w-full flex items-center justify-center gap-1.5 sm:gap-2 px-2 sm:px-3 py-1.5 sm:py-2"
              onClick={onPhoneReserve}
            >
              <Phone className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
              <span className="text-xs sm:text-sm">電話予約</span>
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default StudioCard;
