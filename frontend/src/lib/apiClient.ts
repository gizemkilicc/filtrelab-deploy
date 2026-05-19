export type AIAnalysisResult = {
  extractedFromUrl?: boolean;
  sourceUrl: string;
  sourcePlatform: string;
  dataSource: Record<string, string>;
  dataQuality?: {
    reviewsLoaded?: number;
    hasRatingDistribution?: boolean;
    alternativePricesFound?: number;
    hasRating?: boolean;
    hasReviewCount?: boolean;
    hasSellerScore?: boolean;
    sentimentEligible?: boolean;
    fakeRiskEligible?: boolean;
    pricePerformanceEligible?: boolean;
    price?: "high" | "medium" | "low" | "missing";
    reviewCount?: "high" | "medium" | "low" | "missing";
    questionCount?: "high" | "medium" | "low" | "missing";
  };
  scoringInputs?: Record<string, unknown>;
  scoringVersion?: string;
  confidence?: number;
  extractedFields?: Record<string, boolean>;
  productName: string;
  brand: string;
  category: string;
  categoryConfidence?: number;
  price: string | null;
  image?: string | null;
  rating: number;
  reviewCount: number | null;
  questionCount?: number | null;
  sellerScore?: number | null;
  fakeReviewRisk: number;
  trustScore: number;
  returnRisk: "Düşük" | "Orta" | "Yüksek";
  sentimentScore: number;
  reviewIntelligence?: {
    sentiment_score: number;
    positive: number;
    negative: number;
    neutral: number;
    mixed: number;
    suspicious_review_count: number;
    review_risk_score: number;
    detected_key_phrases: string[];
    source: "aws_comprehend" | "deepseek_fallback";
  } | null;
  pricePerformance: number | null;
  confidenceLevel: "HIGH_CONFIDENCE" | "MEDIUM_CONFIDENCE" | "LOW_CONFIDENCE" | "NO_REVIEW_TEXT";
  dataWarning: string | null;
  analysis: string;
  shoppingBehavior: string;
  finalDecision: "ALINABİLİR" | "DİKKATLİ İNCELE" | "BEKLE";
  betterAlternatives: {
    name: string;
    price: string;
    image?: string | null;
    reason: string;
    url?: string;
    platform?: string;
    isDirectProductUrl?: boolean;
  }[];
  alternativeProducts?: {
    name: string;
    price: string;
    image?: string | null;
    reason?: string;
    url?: string;
    platform?: string;
  }[];
};

export type APIResponse =
  | { success: true; data: AIAnalysisResult }
  | { success: false; error: string };

// ── Auth types ────────────────────────────────────────────────────────────────

export type AuthUser = {
  id: number;
  firstName: string;
  lastName: string;
  name: string;
  email: string;
  createdAt?: string;
  analysisCount?: number;
};

export type AuthResponse =
  | { success: true; accessToken: string; user: AuthUser; message: string | null }
  | { success: false; error: string };

export type SimpleAuthResponse =
  | { success: true; message: string; userId?: number }
  | { success: false; error: string };

// ── Config ────────────────────────────────────────────────────────────────────

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export type SavedProduct = {
  id: number;
  productName: string;
  productUrl: string;
  image?: string | null;
  price?: string | null;
  currentPrice?: string | null;
  targetPrice?: string | null;
  finalDecision?: string | null;
  trustScore?: number | null;
  platform?: string | null;
  createdAt?: string | null;
};

export type Recommendation = {
  title: string;
  description: string;
  source?: SavedProduct | null;
};

// ── Analyze ───────────────────────────────────────────────────────────────────

export const runAIAnalysis = async (
  url: string,
  onProgress: (step: number, message: string) => void
): Promise<APIResponse> => {
  const steps = [
    { message: "Ürün linki inceleniyor...", time: 600 },
    { message: "Yorumlar analiz ediliyor...", time: 800 },
    { message: "Sahte yorum kalıpları aranıyor...", time: 700 },
    { message: "İade riski hesaplanıyor...", time: 800 },
    { message: "Alternatif ürünler karşılaştırılıyor...", time: 600 },
    { message: "Nihai karar oluşturuluyor...", time: 500 },
  ];

  const animationPromise = (async () => {
    for (let i = 0; i < steps.length; i++) {
      onProgress(i, steps[i].message);
      await new Promise((resolve) => setTimeout(resolve, steps[i].time));
    }
    onProgress(steps.length, "Analiz Tamamlandı");
  })();

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 120000);

    const response = await fetch(`${API_URL}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
      mode: "cors",
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return { success: false, error: errorData.error || "API hatası" };
    }

    const data = await response.json();
    if (data.success === false) {
      return { success: false, error: data.error || "API hatası" };
    }

    await animationPromise;
    return { success: true, data };
  } catch {
    return { success: false, error: "Backend bağlantısı kurulamadı." };
  }
};

// ── Auth helpers ──────────────────────────────────────────────────────────────

async function authPost<T>(path: string, body: Record<string, string>): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const json = await res.json();
  if (!res.ok) {
    throw new Error(json.detail || json.error || "Bir hata oluştu.");
  }
  return json as T;
}

function getToken(): string | null {
  return typeof window !== "undefined" ? localStorage.getItem("filtre_token") : null;
}

function getAuthHeaders(): HeadersInit {
  const token = getToken();
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

async function featureRequest<T>(
  path: string,
  options: RequestInit = {}
): Promise<{ success: true; data: T } | { success: false; error: string }> {
  try {
    const res = await fetch(`${API_URL}${path}`, {
      ...options,
      headers: {
        ...getAuthHeaders(),
        ...(options.headers || {}),
      },
    });
    const json = await res.json().catch(() => ({}));
    if (!res.ok) {
      return {
        success: false,
        error: json.detail || json.error || "İşlem başarısız.",
      };
    }
    return { success: true, data: json as T };
  } catch {
    return { success: false, error: "Backend bağlantısı kurulamadı." };
  }
}

// ── Auth functions ────────────────────────────────────────────────────────────

export async function registerUser(
  firstName: string,
  lastName: string,
  email: string,
  password: string
): Promise<SimpleAuthResponse> {
  try {
    const data = await authPost<{ success: boolean; message: string; userId?: number }>(
      "/auth/register",
      { firstName, lastName, email, password }
    );
    return { success: true, message: data.message, userId: data.userId };
  } catch (err) {
    return { success: false, error: err instanceof Error ? err.message : "Kayıt başarısız." };
  }
}

export async function loginUser(
  email: string,
  password: string
): Promise<AuthResponse> {
  try {
    const data = await authPost<{
      success: boolean;
      accessToken: string;
      user: AuthUser;
      message: string | null;
    }>("/auth/login", { email, password });

    if (typeof window !== "undefined") {
      localStorage.setItem("filtre_token", data.accessToken);
      localStorage.setItem("filtre_user", JSON.stringify(data.user));
      window.dispatchEvent(new CustomEvent("filtre-auth-changed"));
    }

    return {
      success: true,
      accessToken: data.accessToken,
      user: data.user,
      message: data.message,
    };
  } catch (err) {
    return { success: false, error: err instanceof Error ? err.message : "Giriş başarısız." };
  }
}

export async function forgotPassword(email: string): Promise<SimpleAuthResponse> {
  try {
    const data = await authPost<{ success: boolean; message: string }>(
      "/auth/forgot-password",
      { email }
    );
    return { success: true, message: data.message };
  } catch (err) {
    return { success: false, error: err instanceof Error ? err.message : "İşlem başarısız." };
  }
}

export async function resetPassword(
  token: string,
  newPassword: string
): Promise<SimpleAuthResponse> {
  try {
    const res = await fetch(`${API_URL}/auth/reset-password`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token, newPassword }),
    });
    const json = await res.json();
    if (!res.ok) throw new Error(json.detail || json.error || "İşlem başarısız.");
    return { success: true, message: json.message };
  } catch (err) {
    return { success: false, error: err instanceof Error ? err.message : "Şifre sıfırlanamadı." };
  }
}

export async function verifyEmailToken(
  token: string
): Promise<SimpleAuthResponse> {
  try {
    const res = await fetch(`${API_URL}/auth/verify-email?token=${encodeURIComponent(token)}`);
    const json = await res.json();
    if (!res.ok) throw new Error(json.detail || json.error || "Doğrulama başarısız.");
    return { success: true, message: json.message };
  } catch (err) {
    return { success: false, error: err instanceof Error ? err.message : "Doğrulama başarısız." };
  }
}

export async function resendVerificationEmail(
  email: string
): Promise<SimpleAuthResponse> {
  try {
    const data = await authPost<{ success: boolean; message: string }>(
      "/auth/send-verification-email",
      { email }
    );
    return { success: true, message: data.message };
  } catch (err) {
    return { success: false, error: err instanceof Error ? err.message : "İşlem başarısız." };
  }
}

export async function getMe(): Promise<AuthUser | null> {
  try {
    const token =
      typeof window !== "undefined" ? localStorage.getItem("filtre_token") : null;
    if (!token) return null;

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);

    const res = await fetch(`${API_URL}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (!res.ok) {
      if (res.status === 401) {
        localStorage.removeItem("filtre_token");
        localStorage.removeItem("filtre_user");
      }
      return null;
    }
    return (await res.json()) as AuthUser;
  } catch {
    return null;
  }
}

export async function updateMe(profile: {
  firstName: string;
  lastName: string;
  email: string;
}): Promise<{ success: true; user: AuthUser } | { success: false; error: string }> {
  try {
    const res = await fetch(`${API_URL}/auth/me`, {
      method: "PUT",
      headers: getAuthHeaders(),
      body: JSON.stringify(profile),
    });
    const json = await res.json().catch(() => ({}));
    if (!res.ok) {
      return { success: false, error: json.detail || json.error || "Profil güncellenemedi." };
    }
    if (typeof window !== "undefined") {
      localStorage.setItem("filtre_user", JSON.stringify(json));
      window.dispatchEvent(new CustomEvent("filtre-auth-changed"));
    }
    return { success: true, user: json as AuthUser };
  } catch {
    return { success: false, error: "Backend bağlantısı kurulamadı." };
  }
}

export function logoutUser(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem("filtre_token");
    localStorage.removeItem("filtre_user");
    window.dispatchEvent(new CustomEvent("filtre-auth-changed"));
  }
}

// ── User features ────────────────────────────────────────────────────────────

export async function addAnalysisHistory(item: {
  productName: string;
  productUrl: string;
  image?: string | null;
  price?: string | null;
  finalDecision?: string | null;
  trustScore?: number | null;
}) {
  return featureRequest<{ success: boolean; item: SavedProduct }>("/analysis-history", {
    method: "POST",
    body: JSON.stringify(item),
  });
}

export async function getAnalysisHistory() {
  return featureRequest<{ success: boolean; items: SavedProduct[] }>("/analysis-history");
}

export async function deleteAnalysisHistory(id: number) {
  return featureRequest<{ success: boolean }>(`/analysis-history/${id}`, { method: "DELETE" });
}

export async function addFavorite(item: {
  productName: string;
  productUrl: string;
  image?: string | null;
  price?: string | null;
  platform?: string | null;
}) {
  return featureRequest<{ success: boolean; item: SavedProduct }>("/favorites", {
    method: "POST",
    body: JSON.stringify(item),
  });
}

export async function getFavorites() {
  return featureRequest<{ success: boolean; items: SavedProduct[] }>("/favorites");
}

export async function deleteFavorite(id: number) {
  return featureRequest<{ success: boolean }>(`/favorites/${id}`, { method: "DELETE" });
}

export async function getRecommendations() {
  return featureRequest<{ success: boolean; message: string | null; recommendations: Recommendation[] }>("/recommendations");
}

// ── SYSTEM 2 — Shopping Psychology ─────────────────────────────────────────

export type ShoppingPsychology = {
  shopping_personality: string;
  trust_sensitivity: number;
  impulsive_vs_analytical: number;
  budget_behavior: string;
  recommendation_strategy: string;
  confidence_score: number;
};

/**
 * Gezinme geçmişini /shopping-psychology endpoint'ine gönderir.
 * Herhangi bir hatada null döndürür — çağıran taraf bölümü gizler, çökmez.
 */
export async function getShoppingPsychology(
  history: unknown[]
): Promise<ShoppingPsychology | null> {
  try {
    const res = await fetch(`${API_URL}/shopping-psychology`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ history }),
    });
    if (!res.ok) return null;
    return (await res.json()) as ShoppingPsychology;
  } catch {
    return null;
  }
}
