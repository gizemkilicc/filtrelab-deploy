export type AIAnalysisResult = {
  extractedFromUrl: boolean;
  sourceUrl: string;
  sourcePlatform: string;
  dataSource: Record<string, string>;
  confidence: number;
  extractedFields: Record<string, boolean>;
  productName: string;
  brand: string;
  category: string;
  categoryConfidence?: number;
  price: string;
  image?: string | null;
  rating: number;
  reviewCount: number;
  questionCount?: number | null;
  sellerScore?: number | null;
  fakeReviewRisk: number;
  trustScore: number;
  returnRisk: "Düşük" | "Orta" | "Yüksek";
  sentimentScore: number;
  pricePerformance: number;
  analysis: string;
  shoppingBehavior: string;
  finalDecision: "ALINABİLİR" | "BEKLE" | "ÖNERİLMEZ";
  betterAlternatives: {
    name: string;
    price: string;
    image?: string | null;
    reason: string;
    url?: string;
    isDirectProductUrl?: boolean;
  }[];
};

export type APIResponse = {
  success: true;
  data: AIAnalysisResult;
} | {
  success: false;
  error: string;
};

export const runAIAnalysis = async (url: string, onProgress: (step: number, message: string) => void): Promise<APIResponse> => {
  const steps = [
    { message: "Ürün linki inceleniyor...", time: 600 },
    { message: "Yorumlar analiz ediliyor...", time: 800 },
    { message: "Sahte yorum kalıpları aranıyor...", time: 700 },
    { message: "İade riski hesaplanıyor...", time: 800 },
    { message: "Alternatif ürünler karşılaştırılıyor...", time: 600 },
    { message: "Nihai karar oluşturuluyor...", time: 500 }
  ];

  const API_URL = "http://127.0.0.1:8000";

  // Start UI animations in background
  const animationPromise = (async () => {
    for (let i = 0; i < steps.length; i++) {
      onProgress(i, steps[i].message);
      await new Promise(resolve => setTimeout(resolve, steps[i].time));
    }
    onProgress(steps.length, "Analiz Tamamlandı");
  })();

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 8000);

    const response = await fetch(`${API_URL}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
      mode: "cors",
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return { success: false, error: errorData.error || "API hatası" };
    }

    const data = await response.json();
    
    // If the backend returns a custom JSON object indicating an error even on 200 OK
    if (data.success === false) {
      return { success: false, error: data.error || "API hatası" };
    }

    await animationPromise;
    return { success: true, data };
  } catch (err) {
    return { success: false, error: "Backend bağlantısı kurulamadı." };
  }
};
