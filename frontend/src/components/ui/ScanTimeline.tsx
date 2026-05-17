"use client";

import { motion } from "framer-motion";
import { CheckCircle2, Circle, Loader2 } from "lucide-react";

interface Step {
  id: number;
  message: string;
  status: "pending" | "scanning" | "completed";
}

interface ScanTimelineProps {
  steps: Step[];
}

export function ScanTimeline({ steps }: ScanTimelineProps) {
  return (
    <div className="flex flex-col space-y-6 w-full max-w-md mx-auto">
      {steps.map((step, index) => (
        <div key={step.id} className="flex items-center space-x-4 relative">
          {/* Vertical line connector */}
          {index < steps.length - 1 && (
            <div className="absolute left-3 top-8 bottom-[-24px] w-0.5 bg-gray-300 dark:bg-gray-800" />
          )}

          <div className="flex-shrink-0 relative z-10 bg-[var(--background)]">
            {step.status === "completed" ? (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: "spring", stiffness: 300, damping: 20 }}
              >
                <CheckCircle2 className="w-6 h-6 text-[var(--neon-green)] drop-shadow-[0_0_8px_rgba(57,255,20,0.8)]" />
              </motion.div>
            ) : step.status === "scanning" ? (
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ repeat: Infinity, duration: 1, ease: "linear" }}
              >
                <Loader2 className="w-6 h-6 text-[var(--neon-blue)] drop-shadow-[0_0_8px_rgba(0,240,255,0.8)]" />
              </motion.div>
            ) : (
              <Circle className="w-6 h-6 text-gray-400 dark:text-gray-700" />
            )}
          </div>

          <motion.div
            initial={{ opacity: 0, x: -10 }}
            animate={{ 
              opacity: step.status === "pending" ? 0.4 : 1, 
              x: 0 
            }}
            transition={{ duration: 0.3 }}
            className={`text-lg ${
              step.status === "scanning" ? "text-[#191847] dark:text-white font-medium" : 
              step.status === "completed" ? "text-gray-700 dark:text-gray-300" : "text-gray-500 dark:text-gray-400"
            }`}
          >
            {step.message}
          </motion.div>
        </div>
      ))}
    </div>
  );
}
