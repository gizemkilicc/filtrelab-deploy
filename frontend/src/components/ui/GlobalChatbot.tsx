"use client";

import { usePathname } from "next/navigation";
import { Chatbot } from "./Chatbot";

export function GlobalChatbot() {
  const pathname = usePathname();

  if (!pathname.startsWith("/dashboard")) {
    return null;
  }

  return <Chatbot />;
}
