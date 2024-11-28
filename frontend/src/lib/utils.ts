// lib/utils.ts

import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// メインのグラデーション
export const mainGradient =
  "bg-gradient-to-r from-indigo-600 to-blue-500 rounded-lg shadow-xl";
