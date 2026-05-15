"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Send, Sparkles } from "lucide-react";

export function Chatbot() {
  const [isOpen, setIsOpen] = useState(false);
  const [message, setMessage] = useState("");

  const toggleChat = () => setIsOpen(!isOpen);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim()) return;
    // Mock submit
    setMessage("");
  };

  return (
    <div className="fixed bottom-8 right-8 z-[100] flex flex-col items-end pointer-events-none">
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 40, scale: 0.95, filter: "blur(10px)" }}
            animate={{ opacity: 1, y: 0, scale: 1, filter: "blur(0px)" }}
            exit={{ opacity: 0, y: 40, scale: 0.95, filter: "blur(10px)" }}
            transition={{ type: "spring", damping: 25, stiffness: 200 }}
            className="mb-6 w-[340px] sm:w-[380px] liquid-glass-heavy gloss-overlay rounded-[2.5rem] overflow-hidden shadow-[0_25px_60px_rgba(0,0,0,0.1)] flex flex-col pointer-events-auto border border-white bg-white/60"
            style={{ height: "550px" }}
          >
            {/* Header */}
            <div className="p-5 border-b border-white/50 bg-white/40 relative z-10 backdrop-blur-2xl shadow-[0_4px_20px_rgba(0,0,0,0.02)]">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="relative">
                    {/* Elegant Apple-style AI Icon */}
                    <div className="w-11 h-11 rounded-full bg-white flex items-center justify-center shadow-[inset_0_2px_4px_rgba(255,255,255,1),0_4px_10px_rgba(0,0,0,0.06)] border border-white/80 backdrop-blur-xl">
                      <Sparkles className="w-5 h-5 text-gray-700 drop-shadow-sm" />
                    </div>
                    {/* Tiny green status dot */}
                    <div className="absolute bottom-0 right-0 w-3 h-3 bg-[#34c759] rounded-full border-2 border-white shadow-sm" />
                  </div>
                  <div>
                    <h3 className="text-gray-900 font-semibold text-[17px] tracking-tight">FiltreLAB</h3>
                    <p className="text-[11px] text-gray-500 font-medium tracking-[0.15em] uppercase">Stil Asistanı</p>
                  </div>
                </div>
                <button onClick={toggleChat} className="text-gray-500 hover:text-gray-900 transition-all hover:scale-110 hover:bg-white p-2.5 bg-white/70 rounded-full shadow-[inset_0_1px_3px_rgba(255,255,255,1),0_2px_5px_rgba(0,0,0,0.04)] border border-white/50">
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Chat Body */}
            <div className="flex-1 p-6 overflow-y-auto flex flex-col space-y-6 relative custom-scrollbar z-10 bg-[#f8fafc]/50">
              <motion.div 
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2 }}
                className="self-start max-w-[85%]"
              >
                <div className="bg-white backdrop-blur-3xl rounded-[1.25rem] rounded-tl-sm p-4 text-[14px] text-gray-800 font-light leading-relaxed shadow-[0_4px_15px_rgba(0,0,0,0.04),inset_0_1px_3px_rgba(255,255,255,1)] border border-white/80">
                  Hoş geldin. Ben FiltreLAB AI. Kusursuz stili bulmak ve ürünleri analiz etmek için buradayım. ✨
                </div>
              </motion.div>
            </div>

            {/* Input Area */}
            <div className="p-4 border-t border-white/60 bg-white/70 backdrop-blur-2xl relative z-10">
              <form onSubmit={handleSubmit} className="relative flex items-center group">
                <input
                  type="text"
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="Bir mesaj yazın..."
                  className="w-full bg-white/80 border border-white rounded-[2rem] py-4 pl-5 pr-14 text-[14px] text-gray-900 placeholder:text-gray-400 focus:outline-none focus:border-white focus:bg-white transition-all shadow-[inset_0_2px_4px_rgba(0,0,0,0.02),0_2px_10px_rgba(0,0,0,0.02)] font-light"
                />
                <button
                  type="submit"
                  className="absolute right-2.5 p-3 bg-white hover:bg-gray-50 text-gray-800 rounded-full transition-all active:scale-95 flex items-center justify-center shadow-[inset_0_2px_4px_rgba(255,255,255,1),0_4px_12px_rgba(0,0,0,0.08)] border border-white/80 backdrop-blur-md"
                >
                  <Send className="w-[18px] h-[18px]" />
                </button>
              </form>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Ultra Premium Glass AI Orb Button */}
      <motion.button
        onClick={toggleChat}
        className="relative w-16 h-16 sm:w-[72px] sm:h-[72px] rounded-full flex items-center justify-center text-gray-800 transition-all duration-500 group will-change-transform outline-none pointer-events-auto shadow-[0_12px_40px_rgba(0,0,0,0.12)] hover:shadow-[0_16px_50px_rgba(0,0,0,0.15)]"
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        {/* Soft Ambient Glow */}
        <div className="absolute inset-[-6px] rounded-full bg-white/80 opacity-60 blur-[12px] group-hover:opacity-100 group-hover:blur-[20px] transition-all duration-700" />
        
        {/* Apple VisionOS True Glass Layer */}
        <div className="absolute inset-0 rounded-full bg-white/80 backdrop-blur-3xl border border-white shadow-[inset_0_4px_10px_rgba(255,255,255,1)] z-10 overflow-hidden">
           {/* High-fidelity Glossy top highlight */}
           <div className="absolute top-0 left-0 right-0 h-[55%] bg-gradient-to-b from-white to-transparent rounded-t-full pointer-events-none mix-blend-overlay" />
           <div className="absolute top-0 left-0 right-0 h-[40%] bg-gradient-to-b from-white/90 to-transparent rounded-t-full pointer-events-none" />
        </div>

        {/* Inner Subtle Depth Core */}
        <div className="absolute inset-2 rounded-full bg-gradient-to-br from-white via-white/80 to-pink-100/50 z-20 shadow-[inset_0_0_15px_rgba(255,255,255,1)] blur-[1px]" />

        <div className="relative flex items-center justify-center w-full h-full z-30">
          <AnimatePresence mode="wait">
            {isOpen ? (
              <motion.div
                key="close"
                initial={{ rotate: -90, opacity: 0 }}
                animate={{ rotate: 0, opacity: 1 }}
                exit={{ rotate: 90, opacity: 0 }}
                transition={{ duration: 0.3 }}
              >
                <X className="w-7 h-7 text-gray-600 drop-shadow-sm" />
              </motion.div>
            ) : (
              <motion.div
                key="chat"
                initial={{ rotate: 90, opacity: 0 }}
                animate={{ rotate: 0, opacity: 1 }}
                exit={{ rotate: -90, opacity: 0 }}
                transition={{ duration: 0.3 }}
              >
                <Sparkles className="w-7 h-7 text-gray-700 drop-shadow-sm" />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </motion.button>
    </div>
  );
}
