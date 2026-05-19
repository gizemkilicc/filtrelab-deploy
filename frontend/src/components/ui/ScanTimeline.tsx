"use client";

import { motion } from "framer-motion";
import { Check, Loader2 } from "lucide-react";

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
    <div className="flex w-full flex-col">
      {steps.map((step, index) => (
        <div key={step.id} className="relative flex items-center gap-4 py-3">
          {/* Dikey bağlayıcı çizgi */}
          {index < steps.length - 1 && (
            <div
              className="absolute left-[11px] top-9 w-px"
              style={{ height: "calc(100% - 12px)", background: "var(--ink-70)" }}
            />
          )}

          <div className="relative z-10 flex-shrink-0">
            {step.status === "completed" ? (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
                className="flex h-6 w-6 items-center justify-center rounded-[2px]"
                style={{ background: "var(--brass)" }}
              >
                <Check className="h-4 w-4" style={{ color: "#1a1610" }} />
              </motion.div>
            ) : step.status === "scanning" ? (
              <div
                className="flex h-6 w-6 items-center justify-center rounded-[2px] border"
                style={{ borderColor: "var(--brass)" }}
              >
                <Loader2 className="h-4 w-4 animate-spin" style={{ color: "var(--brass)" }} />
              </div>
            ) : (
              <div
                className="h-6 w-6 rounded-[2px] border"
                style={{ borderColor: "var(--ink-70)", background: "var(--bg-deep)" }}
              />
            )}
          </div>

          <motion.span
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: step.status === "pending" ? 0.45 : 1, x: 0 }}
            transition={{ duration: 0.3 }}
            className="fl-mono text-[12px] uppercase tracking-[0.1em]"
            style={{
              color:
                step.status === "scanning"
                  ? "var(--brass)"
                  : step.status === "completed"
                  ? "var(--paper)"
                  : "var(--ink-30)",
            }}
          >
            {step.message}
          </motion.span>
        </div>
      ))}
    </div>
  );
}
