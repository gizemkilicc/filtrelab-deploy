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
    platform?: string;
    isDirectProductUrl?: boolean;
  }[];
};

export type APIResponse =
  | { success: true; data: AIAnalysisResult }
  | { success: false; error: string };

// ── Auth types ────────────────────────────────────────────────────────────────

export type AuthUser = {
  id: number;
  name: string;
  email: string;
  isVerified: boolean;
  createdAt?: string;
};

export type AuthResponse =
  | { success: true; accessToken: string; user: AuthUser; emailVerified: boolean; message: string | null }
  | { success: false; error: string };

export type SimpleAuthResponse =
  | { success: true; message: string; userId?: number }
  | { success: false; error: string };

// ── Config ────────────────────────────────────────────────────────────────────

const API_URL = "http://127.0.0.1:8000";

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

// ── Auth functions ────────────────────────────────────────────────────────────

export async function registerUser(
  name: string,
  email: string,
  password: string
): Promise<SimpleAuthResponse> {
  try {
    const data = await authPost<{ success: boolean; message: string; userId?: number }>(
      "/auth/register",
      { name, email, password }
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
      emailVerified: boolean;
      message: string | null;
    }>("/auth/login", { email, password });

    if (typeof window !== "undefined") {
      localStorage.setItem("filtre_token", data.accessToken);
      localStorage.setItem("filtre_user", JSON.stringify(data.user));
    }

    return {
      success: true,
      accessToken: data.accessToken,
      user: data.user,
      emailVerified: data.emailVerified,
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

export async function getMe(): Promise<AuthUser | null> {
  try {
    const token =
      typeof window !== "undefined" ? localStorage.getItem("filtre_token") : null;
    if (!token) return null;

    const res = await fetch(`${API_URL}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) return null;
    return (await res.json()) as AuthUser;
  } catch {
    return null;
  }
}

export function logoutUser(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem("filtre_token");
    localStorage.removeItem("filtre_user");
  }
}
