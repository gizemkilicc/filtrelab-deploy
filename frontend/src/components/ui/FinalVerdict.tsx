"use client";

import { motion } from "framer-motion";
import { AlertTriangle, CheckCircle, Clock, Eye } from "lucide-react";
import { cn } from "./AnimatedCard";

interface FinalVerdictProps {
  decision: "ALINABİLİR" | "DİKKATLİ İNCELE" | "BEKLE";
  reason: string;
  confidenceLevel?: "HIGH_CONFIDENCE" | "MEDIUM_CONFIDENCE" | "LOW_CONFIDENCE";
  dataWarning?: string | null;
}

const CONFIDENCE_LABEL: Record<string, string> = {
  HIGH_CONFIDENCE: "Yüksek Güven",
  MEDIUM_CONFIDENCE: "Orta Güven",
  LOW_CONFIDENCE: "Düşük Güven",
};

const CONFIDENCE_COLOR: Record<string, string> = {
  HIGH_CONFIDENCE: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
  MEDIUM_CONFIDENCE: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400",
  LOW_CONFIDENCE: "bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400",
};

export function FinalVerdict({ decision, reason, confidenceLevel, dataWarning }: FinalVerdictProps) {
  const config = {
    "ALINABİLİR": {
      color: "var(--neon-green)",
      bg: "bg-green-500/10",
      border: "border-green-500/30",
      glow: "shadow-[0_0_30px_rgba(57,255,20,0.3)]",
      icon: CheckCircle,
      text: "ALINABİLİR",
    },
    "DİKKATLİ İNCELE": {
      color: "#f97316",
      bg: "bg-orange-500/10",
      border: "border-orange-500/30",
      glow: "shadow-[0_0_30px_rgba(249,115,22,0.3)]",
      icon: Eye,
      text: "DİKKATLİ İNCELE",
    },
    "BEKLE": {
      color: "#fbbf24",
      bg: "bg-yellow-500/10",
      border: "border-yellow-500/30",
      glow: "shadow-[0_0_30px_rgba(251,191,36,0.3)]",
      icon: Clock,
      text: "BEKLE",
    },
  };

  const { color, bg, border, glow, icon: Icon, text } = config[decision] ?? config["DİKKATLİ İNCELE"];

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.8, type: "spring" }}
      className={cn(
        "rounded-3xl p-8 flex flex-col items-center justify-center text-center border backdrop-blur-md",
        bg, border, glow
      )}
    >
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ delay: 0.3, type: "spring", stiffness: 200 }}
        className="mb-4"
      >
        <Icon className="w-16 h-16" style={{ color, filter: `drop-shadow(0 0 10px ${color})` }} />
      </motion.div>

      <h2 className="text-sm font-semibold tracking-widest text-gray-500 dark:text-gray-400 uppercase mb-2">Nihai Karar</h2>

      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
      >
        <span
          className="text-4xl font-black tracking-tighter mb-4 block"
          style={{ color, textShadow: `0 0 20px ${color}` }}
        >
          {text}
        </span>
      </motion.div>

      {confidenceLevel && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
          className="mb-3"
        >
          <span className={cn(
            "text-xs font-semibold px-3 py-1 rounded-full",
            CONFIDENCE_COLOR[confidenceLevel] ?? CONFIDENCE_COLOR["LOW_CONFIDENCE"]
          )}>
            {CONFIDENCE_LABEL[confidenceLevel] ?? confidenceLevel}
          </span>
        </motion.div>
      )}

      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.8 }}
        className="text-gray-700 dark:text-gray-300 max-w-md mt-2 leading-relaxed"
      >
        {reason}
      </motion.p>

      {dataWarning && (
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.0 }}
          className="text-xs text-orange-600 dark:text-orange-400 max-w-md mt-4 leading-relaxed bg-orange-50 dark:bg-orange-900/20 px-4 py-2 rounded-xl border border-orange-200 dark:border-orange-800/40"
        >
          {dataWarning}
        </motion.p>
      )}
    </motion.div>
  );
}
