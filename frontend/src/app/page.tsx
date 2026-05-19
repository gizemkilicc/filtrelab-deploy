import { Navbar } from "@/components/ui/Navbar";
import { HeroWave } from "@/components/ui/HeroWave";
import { ProcessJourney } from "@/components/ui/ProcessJourney";
import { StatsBar } from "@/components/ui/StatsBar";
import { PremiumCTA } from "@/components/ui/PremiumCTA";
import { SupportFeedback } from "@/components/ui/SupportFeedback";
import { PersonalizedHome } from "@/components/ui/PersonalizedHome";

export default function Home() {
  return (
    <main className="fl-page relative flex min-h-screen flex-col overflow-x-hidden">
      <Navbar />

      <PersonalizedHome>
        <HeroWave />
        <ProcessJourney />
        <StatsBar />
        <PremiumCTA />
        <SupportFeedback />
      </PersonalizedHome>
    </main>
  );
}
