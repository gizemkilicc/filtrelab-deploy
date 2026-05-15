"use client";

import { motion } from "framer-motion";
import { Search, ShoppingCart, User, Menu } from "lucide-react";
import Link from "next/link";
import Image from "next/image";
import { useState } from "react";
import { AuthModal } from "./AuthModal";

export function Navbar() {
  const [isAuthOpen, setIsAuthOpen] = useState(false);

  return (
    <>
      <motion.nav 
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
        className="fixed top-0 left-0 right-0 z-50 p-4 md:p-6 pointer-events-none"
      >
        <div className="max-w-7xl mx-auto liquid-glass gloss-overlay rounded-full px-7 py-3.5 flex items-center justify-between pointer-events-auto shadow-[0_12px_40px_rgba(0,0,0,0.05)] border border-white">
          
          {/* Logo */}
          <Link href="/" className="flex items-center space-x-3 group">
            {/* AI Generated Frosted Glass Logo */}
            <div className="relative w-12 h-12 rounded-[14px] overflow-hidden group-hover:scale-105 transition-transform duration-700 will-change-transform shadow-[0_4px_15px_rgba(0,0,0,0.06)] border border-white/60 bg-white">
              <Image src="/images/logo.png" alt="FiltreLAB Logo" fill className="object-cover scale-110" />
            </div>
            
            <span className="text-[22px] font-medium tracking-tight hidden sm:block text-gray-700 drop-shadow-sm">
              Filtre<span className="font-bold text-gray-900">LAB</span>
            </span>
          </Link>

          {/* Links */}
          <div className="hidden md:flex items-center space-x-9">
            <Link href="#" className="text-[14px] font-medium text-gray-500 hover:text-gray-900 transition-colors">
              Kadın
            </Link>
            <Link href="#" className="text-[14px] font-medium text-gray-500 hover:text-gray-900 transition-colors">
              Erkek
            </Link>
            <Link href="#" className="text-[14px] font-medium text-gray-500 hover:text-gray-900 transition-colors">
              Aksesuar
            </Link>
            <Link href="#" className="text-[14px] font-bold text-gray-900 hover:opacity-70 transition-opacity drop-shadow-sm">
              AI Tavsiyeleri
            </Link>
          </div>

          {/* Icons */}
          <div className="flex items-center space-x-3 sm:space-x-4">
            <button className="text-gray-500 hover:text-gray-900 transition-transform hover:scale-105 hidden sm:block will-change-transform p-2 bg-white/60 hover:bg-white rounded-full shadow-[inset_0_1px_2px_rgba(255,255,255,1)]">
              <Search className="w-[18px] h-[18px]" />
            </button>
            <button className="text-gray-500 hover:text-gray-900 transition-transform hover:scale-105 relative will-change-transform p-2 bg-white/60 hover:bg-white rounded-full shadow-[inset_0_1px_2px_rgba(255,255,255,1)]">
              <ShoppingCart className="w-[18px] h-[18px]" />
            </button>
            <button 
              onClick={() => setIsAuthOpen(true)}
              className="text-gray-700 transition-all duration-500 hover:scale-105 bg-white hover:bg-gray-50 border border-white p-2.5 rounded-full shadow-[inset_0_2px_4px_rgba(255,255,255,1),0_4px_12px_rgba(0,0,0,0.05)] will-change-transform flex items-center justify-center"
            >
              <User className="w-[18px] h-[18px]" />
            </button>
            <button className="md:hidden text-gray-500 hover:text-gray-900 transition-colors p-2 bg-white/60 rounded-full shadow-[inset_0_1px_2px_rgba(255,255,255,1)]">
              <Menu className="w-5 h-5" />
            </button>
          </div>

        </div>
      </motion.nav>

      {/* Auth Modal */}
      <AuthModal isOpen={isAuthOpen} onClose={() => setIsAuthOpen(false)} />
    </>
  );
}
