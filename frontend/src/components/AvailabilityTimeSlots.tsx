import React from "react";
import { Badge } from "@/components/ui/badge";
import { AvailableTimeSlot } from "./StudioAvailabilityResults";
import _ from "lodash";

interface GroupedAvailability {
  roomName: string;
  timeRanges: string[];
}

interface AvailabilityTimeSlotsProps {
  availableRanges: AvailableTimeSlot[];
}

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

const AvailabilityTimeSlots: React.FC<AvailabilityTimeSlotsProps> = ({
  availableRanges,
}) => {
  const groupedAvailabilities = formatTimeRanges(availableRanges);

  return (
    <div className="space-y-3 sm:space-y-4">
      <p className="text-sm sm:text-base font-medium">予約可能な時間帯</p>
      <div className="space-y-2 sm:space-y-3">
        {groupedAvailabilities.map((group, roomIdx) => (
          <div key={roomIdx} className="space-y-1.5 sm:space-y-2">
            <p className="text-xs sm:text-sm font-medium text-muted-foreground">
              {group.roomName}:
            </p>
            <div className="flex flex-wrap gap-1.5 sm:gap-2">
              {group.timeRanges.map((timeRange, timeIdx) => (
                <Badge
                  key={timeIdx}
                  variant="outline"
                  className="text-[10px] sm:text-xs px-2 py-1"
                >
                  {timeRange}
                </Badge>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default AvailabilityTimeSlots;
