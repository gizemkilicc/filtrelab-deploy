"use client";

import { motion } from "framer-motion";
import { ReactNode } from "react";
import { twMerge } from "tailwind-merge";
import { clsx, type ClassValue } from "clsx";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface AnimatedCardProps {
  children: ReactNode;
  className?: string;
  delay?: number;
}

export function AnimatedCard({ children, className, delay = 0 }: AnimatedCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay, ease: "easeOut" }}
      whileHover={{ scale: 1.02, transition: { duration: 0.2 } }}
      className={cn(
        "glass-card rounded-2xl p-6 relative overflow-hidden group bg-white/75 dark:bg-white/5 border border-white/80 dark:border-white/10 text-[#191847] dark:text-white shadow-[0_18px_50px_rgba(25,24,71,0.08)] dark:shadow-[0_18px_50px_rgba(0,0,0,0.25)] backdrop-blur-xl",
        className
      )}
    >
      {/* Neon Glow Hover Effect */}
      <div className="absolute inset-0 bg-gradient-to-r from-[var(--neon-blue)] to-[var(--neon-purple)] opacity-0 group-hover:opacity-10 transition-opacity duration-500 rounded-2xl pointer-events-none" />
      {children}
    </motion.div>
  );
}
