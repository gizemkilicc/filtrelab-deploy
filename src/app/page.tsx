import { Navbar } from "@/components/ui/Navbar";
import { FeaturedProducts } from "@/components/ui/FeaturedProducts";
import { Chatbot } from "@/components/ui/Chatbot";
import { HeroWave } from "@/components/ui/HeroWave";
import { SupportFeedback } from "@/components/ui/SupportFeedback";

export default function Home() {
  return (
    <main className="min-h-screen flex flex-col relative overflow-x-hidden selection:bg-purple-200 selection:text-purple-900">
      <Navbar />

      {/* Futuristic Fullscreen Hero Section */}
      <HeroWave />

      {/* Spacing before Products */}
      <div className="h-20" />

      {/* Featured Products */}
      <FeaturedProducts />

      {/* Support and Feedback */}
      <SupportFeedback />

      {/* Floating Chatbot */}
      <Chatbot />
    </main>
  );
}
