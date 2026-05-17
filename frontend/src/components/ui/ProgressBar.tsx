"use client";

import { motion } from "framer-motion";

interface ProgressBarProps {
  value: number; // 0 to 100
  color?: string; // Hex or CSS variable string
  label?: string;
  showValue?: boolean;
}

export function ProgressBar({ value, color = "var(--neon-blue)", label, showValue = true }: ProgressBarProps) {
  return (
    <div className="w-full">
      {label && (
        <div className="flex justify-between items-center mb-1 text-sm font-medium text-gray-700 dark:text-gray-300">
          <span>{label}</span>
          {showValue && <span>{value}%</span>}
        </div>
      )}
      <div className="h-2.5 bg-gray-200 dark:bg-gray-800 rounded-full overflow-hidden w-full border border-black/5 dark:border-white/5">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${value}%` }}
          transition={{ duration: 1.5, ease: "easeOut", delay: 0.2 }}
          className="h-full rounded-full"
          style={{
            backgroundColor: color,
            boxShadow: `0 0 10px ${color}`,
          }}
        />
      </div>
    </div>
  );
}
