import { Navbar } from "@/components/ui/Navbar";
import { FeaturedProducts } from "@/components/ui/FeaturedProducts";
import { HeroWave } from "@/components/ui/HeroWave";
import { HowItWorks } from "@/components/ui/HowItWorks";
import { StatsBar } from "@/components/ui/StatsBar";
import { CategoryCards } from "@/components/ui/CategoryCards";
import { PremiumCTA } from "@/components/ui/PremiumCTA";
import { SupportFeedback } from "@/components/ui/SupportFeedback";

export default function Home() {
  return (
    <main className="min-h-screen flex flex-col relative overflow-x-hidden selection:bg-purple-200 selection:text-purple-900">
      <Navbar />

      {/* Hero */}
      <HeroWave />

      {/* Nasıl Çalışır? */}
      <HowItWorks />

      {/* İstatistik Bandı */}
      <StatsBar />

      {/* Kategori Kartları */}
      <CategoryCards />

      {/* AI Koleksiyonu */}
      <FeaturedProducts />

      {/* Hesap / Premium CTA */}
      <PremiumCTA />

      {/* Support and Feedback */}
      <SupportFeedback />

    </main>
  );
}
