"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Send, Sparkles } from "lucide-react";
import {
  chatWithAssistant,
  type AIAnalysisResult,
  type ChatMessage,
} from "@/lib/apiClient";

const CHAT_STORAGE_KEY = "filtre_chat_history";
const ANALYSIS_STORAGE_KEY = "filtre_last_analysis";
const FALLBACK_REPLY = "Şu anda yanıt oluşturamadım, tekrar dener misin?";

function loadStoredMessages(): ChatMessage[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(CHAT_STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed)
      ? parsed.filter((item) => item?.role && item?.content).slice(-24)
      : [];
  } catch {
    return [];
  }
}

function loadStoredAnalysis(): AIAnalysisResult | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(ANALYSIS_STORAGE_KEY);
    return raw ? (JSON.parse(raw) as AIAnalysisResult) : null;
  } catch {
    return null;
  }
}

export function Chatbot() {
  const [isOpen, setIsOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    setMessages(loadStoredMessages());
  }, []);

  // Open chatbot when "Asistanı Keşfet" button dispatches this event
  useEffect(() => {
    const handler = () => setIsOpen(true);
    window.addEventListener("filtre:open-chatbot", handler);
    return () => window.removeEventListener("filtre:open-chatbot", handler);
  }, []);

  useEffect(() => {
    if (typeof window !== "undefined") {
      localStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(messages.slice(-24)));
    }
    scrollRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, isLoading]);

  const visibleMessages = useMemo<ChatMessage[]>(
    () =>
      messages.length > 0
        ? messages
        : [
            {
              role: "assistant",
              content:
                "Hoş geldin. Ürün linki analiz edildiyse onun üzerinden fiyat, yorum, kullanım amacı ve alternatifleri birlikte değerlendirebilirim.",
            },
          ],
    [messages]
  );

  const toggleChat = () => setIsOpen((open) => !open);

  const handleSubmit = async (e?: React.FormEvent) => {
    e?.preventDefault();
    const cleanMessage = message.trim();
    if (!cleanMessage || isLoading) return;

    const userMessage: ChatMessage = { role: "user", content: cleanMessage };
    const nextHistory = [...messages, userMessage].slice(-24);
    const analysis = loadStoredAnalysis();

    setMessages(nextHistory);
    setMessage("");
    setIsLoading(true);

    const response = await chatWithAssistant(cleanMessage, analysis, nextHistory.slice(-12));
    const assistantMessage: ChatMessage = {
      role: "assistant",
      content: response.success ? response.reply : FALLBACK_REPLY,
    };

    setMessages([...nextHistory, assistantMessage].slice(-24));
    setIsLoading(false);
  };

  return (
    <div className="fixed bottom-10 right-6 z-[200] flex flex-col items-end pointer-events-none sm:right-8 md:bottom-12">
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 40, scale: 0.95, filter: "blur(10px)" }}
            animate={{ opacity: 1, y: 0, scale: 1, filter: "blur(0px)" }}
            exit={{ opacity: 0, y: 40, scale: 0.95, filter: "blur(10px)" }}
            transition={{ type: "spring", damping: 25, stiffness: 200 }}
            className="mb-6 w-[340px] sm:w-[380px] liquid-glass-heavy gloss-overlay rounded-[2.5rem] overflow-hidden shadow-[0_25px_60px_rgba(0,0,0,0.1)] flex flex-col pointer-events-auto border border-white/80 dark:border-white/10 bg-white/80 dark:bg-gray-950/85"
            style={{ height: "550px" }}
          >
            <div className="p-5 border-b border-white/50 dark:border-white/10 bg-white/70 dark:bg-gray-950/70 relative z-10 backdrop-blur-2xl shadow-[0_4px_20px_rgba(0,0,0,0.02)]">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="relative">
                    <div className="w-11 h-11 rounded-full bg-white dark:bg-white/10 flex items-center justify-center shadow-[inset_0_2px_4px_rgba(255,255,255,1),0_4px_10px_rgba(0,0,0,0.06)] dark:shadow-none border border-white/80 dark:border-white/10 backdrop-blur-xl">
                      <Sparkles className="w-5 h-5 text-gray-700 dark:text-gray-200 drop-shadow-sm" />
                    </div>
                    <div className="absolute bottom-0 right-0 w-3 h-3 bg-[#34c759] rounded-full border-2 border-white shadow-sm" />
                  </div>
                  <div>
                    <h3 className="text-[#191847] dark:text-white font-semibold text-[17px] tracking-tight">FiltreLAB</h3>
                    <p className="text-[11px] text-gray-500 dark:text-gray-400 font-medium tracking-[0.15em] uppercase">Alışveriş Asistanı</p>
                  </div>
                </div>
                <button onClick={toggleChat} className="text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-all hover:scale-110 hover:bg-white dark:hover:bg-white/10 p-2.5 bg-white/70 dark:bg-white/5 rounded-full shadow-[inset_0_1px_3px_rgba(255,255,255,1),0_2px_5px_rgba(0,0,0,0.04)] dark:shadow-none border border-white/50 dark:border-white/10">
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            <div className="flex-1 p-6 overflow-y-auto flex flex-col space-y-4 relative custom-scrollbar z-10 bg-[#f8fafc]/70 dark:bg-gray-950/60">
              {visibleMessages.map((item, index) => (
                <motion.div
                  key={`${item.role}-${index}-${item.content.slice(0, 18)}`}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={item.role === "user" ? "self-end max-w-[85%]" : "self-start max-w-[85%]"}
                >
                  <div
                    className={
                      item.role === "user"
                        ? "bg-gray-900 dark:bg-white text-white dark:text-[#191847] rounded-[1.25rem] rounded-tr-sm p-4 text-[14px] font-light leading-relaxed shadow-[0_4px_15px_rgba(0,0,0,0.08)]"
                        : "bg-white dark:bg-white/10 backdrop-blur-3xl rounded-[1.25rem] rounded-tl-sm p-4 text-[14px] text-gray-800 dark:text-gray-200 font-light leading-relaxed shadow-[0_4px_15px_rgba(0,0,0,0.04),inset_0_1px_3px_rgba(255,255,255,1)] dark:shadow-none border border-white/80 dark:border-white/10 whitespace-pre-line"
                    }
                  >
                    {item.content}
                  </div>
                </motion.div>
              ))}

              {isLoading && (
                <div className="self-start max-w-[85%]">
                  <div className="bg-white dark:bg-white/10 rounded-[1.25rem] rounded-tl-sm p-4 text-[14px] text-gray-500 dark:text-gray-300 font-light border border-white/80 dark:border-white/10">
                    FiltreLAB düşünüyor...
                  </div>
                </div>
              )}
              <div ref={scrollRef} />
            </div>

            <div className="p-4 border-t border-white/60 dark:border-white/10 bg-white/80 dark:bg-gray-950/80 backdrop-blur-2xl relative z-10">
              <form onSubmit={handleSubmit} className="relative flex items-center group">
                <input
                  type="text"
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  disabled={isLoading}
                  placeholder="Ürün hakkında bir şey sor..."
                  className="w-full bg-white/90 dark:bg-white/10 border border-white dark:border-white/10 rounded-[2rem] py-4 pl-5 pr-14 text-[14px] text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-gray-500 focus:outline-none focus:border-white focus:bg-white dark:focus:bg-white/15 transition-all shadow-[inset_0_2px_4px_rgba(0,0,0,0.02),0_2px_10px_rgba(0,0,0,0.02)] dark:shadow-none font-light disabled:opacity-70"
                />
                <button
                  type="submit"
                  disabled={isLoading || !message.trim()}
                  className="absolute right-2.5 p-3 bg-white dark:bg-white/15 hover:bg-gray-50 dark:hover:bg-white/20 text-gray-800 dark:text-white rounded-full transition-all active:scale-95 flex items-center justify-center shadow-[inset_0_2px_4px_rgba(255,255,255,1),0_4px_12px_rgba(0,0,0,0.08)] dark:shadow-none border border-white/80 dark:border-white/10 backdrop-blur-md disabled:opacity-50"
                  aria-label="Mesaj gönder"
                >
                  <Send className="w-[18px] h-[18px]" />
                </button>
              </form>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <motion.button
        onClick={toggleChat}
        className="relative w-16 h-16 sm:w-[72px] sm:h-[72px] rounded-full flex items-center justify-center text-gray-800 transition-all duration-500 group will-change-transform outline-none pointer-events-auto shadow-[0_12px_40px_rgba(0,0,0,0.12)] hover:shadow-[0_16px_50px_rgba(0,0,0,0.15)]"
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        aria-label="FiltreLAB sohbetini aç"
      >
        <div className="absolute inset-[-6px] rounded-full bg-white/80 opacity-60 blur-[12px] group-hover:opacity-100 group-hover:blur-[20px] transition-all duration-700" />
        <div className="absolute inset-0 rounded-full bg-white/80 backdrop-blur-3xl border border-white shadow-[inset_0_4px_10px_rgba(255,255,255,1)] z-10 overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-[55%] bg-gradient-to-b from-white to-transparent rounded-t-full pointer-events-none mix-blend-overlay" />
          <div className="absolute top-0 left-0 right-0 h-[40%] bg-gradient-to-b from-white/90 to-transparent rounded-t-full pointer-events-none" />
        </div>
        <div className="absolute inset-2 rounded-full bg-gradient-to-br from-white via-white/80 to-pink-100/50 z-20 shadow-[inset_0_0_15px_rgba(255,255,255,1)] blur-[1px]" />

        <div className="relative flex items-center justify-center w-full h-full z-30">
          <AnimatePresence mode="wait">
            {isOpen ? (
              <motion.div key="close" initial={{ rotate: -90, opacity: 0 }} animate={{ rotate: 0, opacity: 1 }} exit={{ rotate: 90, opacity: 0 }} transition={{ duration: 0.3 }}>
                <X className="w-7 h-7 text-gray-600 drop-shadow-sm" />
              </motion.div>
            ) : (
              <motion.div key="chat" initial={{ rotate: 90, opacity: 0 }} animate={{ rotate: 0, opacity: 1 }} exit={{ rotate: -90, opacity: 0 }} transition={{ duration: 0.3 }}>
                <Sparkles className="w-7 h-7 text-gray-700 drop-shadow-sm" />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </motion.button>
    </div>
  );
}
