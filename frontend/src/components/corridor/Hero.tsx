"use client";

/* ============================================================
   FiltreLAB — Hero · Karanlık Oda
   The entrance before the corridor. Wired to the real app:
   the paste rig routes to /dashboard, the topbar opens a real
   auth modal (loginUser / registerUser / forgotPassword).
   ============================================================ */

import { useEffect, useMemo, useRef, useState, type CSSProperties } from "react";
import { useRouter } from "next/navigation";
import { loginUser, registerUser, forgotPassword } from "@/lib/apiClient";
import { rand } from "./rng";

type AuthMode = "login" | "register" | "forgot" | null;

const ALCOVE_NAMES: [string, string, string][] = [
  ["01", "Linki Tarıyoruz", "ürün bilgisi"],
  ["02", "Yorumları Süzüyoruz", "duygu analizi"],
  ["03", "Sahteleri Yakalıyoruz", "bot tespiti"],
  ["04", "İade Riskini Ölçüyoruz", "kullanıcı şikayetleri"],
  ["05", "Fiyatı Karşılaştırıyoruz", "pazar verisi"],
  ["06", "Kararı Açıklıyoruz", "tek net sonuç"],
];

const PLACEHOLDERS = [
  "Trendyol ürün linkini yapıştır...",
  "Hepsiburada ürün linkini yapıştır...",
  "Amazon ürün linkini yapıştır...",
];

export function Hero() {
  const router = useRouter();
  const [url, setUrl] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  const [authMode, setAuthMode] = useState<AuthMode>(null);

  // Pre-fill from ?url= query param on mount
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const urlParam = params.get("url");
    if (urlParam) setUrl(decodeURIComponent(urlParam));
  }, []);

  // drifting motes
  const motes = useMemo(() => {
    const arr = [];
    for (let i = 0; i < 28; i++) {
      let k = i * 9 + 1;
      const rnd = () => rand(k++);
      arr.push({
        left: rnd() * 100,
        top: 10 + rnd() * 80,
        s: 1.5 + rnd() * 3,
        d: 14 + rnd() * 24,
        delay: -rnd() * 18,
        dx: (rnd() - 0.5) * 60,
        dy: (rnd() - 0.5) * 80,
        o: 0.25 + rnd() * 0.55,
      });
    }
    return arr;
  }, []);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = url.trim();
    if (!trimmed) {
      inputRef.current?.focus();
      return;
    }
    router.push(`/dashboard?url=${encodeURIComponent(trimmed)}`);
  };

  // example URL placeholder cycles through marketplaces
  const [phIdx, setPhIdx] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setPhIdx((p) => (p + 1) % PLACEHOLDERS.length), 3200);
    return () => clearInterval(id);
  }, []);

  return (
    <section className="hero" data-screen-label="00 Karanlık Oda">
      {/* warm ceiling spotlight cone */}
      <div className="hero__cone"></div>
      <div className="hero__vignette"></div>

      {/* drifting motes in the light */}
      <div className="hero__motes" aria-hidden="true">
        {motes.map((m, i) => (
          <span
            key={i}
            style={
              {
                left: `${m.left}%`,
                top: `${m.top}%`,
                "--s": `${m.s}px`,
                "--d": `${m.d}s`,
                "--delay": `${m.delay}s`,
                "--dx": `${m.dx}px`,
                "--dy": `${m.dy}px`,
                "--o": m.o,
              } as CSSProperties
            }
          />
        ))}
      </div>

      {/* top bar */}
      <header className="hero__topbar">
        <div className="hero__mark">
          <em>FiltreLAB</em>
          <span className="rule"></span>
          <span>akıllı alışveriş asistanı</span>
        </div>

        <div className="hero__auth">
          <button
            type="button"
            className="auth-btn auth-btn--ghost"
            onClick={() => setAuthMode("login")}
          >
            Giriş Yap
          </button>
          <button
            type="button"
            className="auth-btn auth-btn--solid"
            onClick={() => setAuthMode("register")}
          >
            Kayıt Ol
          </button>
        </div>
      </header>

      {/* key remounts on mode change so feedback/fields reset without a setState effect */}
      <AuthModal
        key={authMode ?? "closed"}
        mode={authMode}
        onClose={() => setAuthMode(null)}
        onSwitch={setAuthMode}
      />

      {/* main stage */}
      <div className="hero__stage">
        <div className="hero__lead">
          <div className="hero__kicker">
            <span>NASIL ÇALIŞIR</span>
            <span className="bar"></span>
            <span>6 ADIMDA KARAR</span>
          </div>

          <h1 className="hero__title">
            <span>Bir link yapıştırın.</span>
            <span>6 adımda</span>
            <span className="hero__title-em">
              <em>net cevap alın.</em>
            </span>
          </h1>

          <p className="hero__deck">
            FiltreLAB, Trendyol, Hepsiburada ve Amazon&apos;dan aldığınız ürün linkini
            analiz eder. Yorumları, iade oranlarını ve fiyatı inceler; size yalnızca tek
            bir karar verir: <em>alın, dikkatli inceleyin ya da bekleyin.</em>
          </p>

          <form className="paste-rig" onSubmit={submit}>
            <div className="paste-rig__field">
              <label htmlFor="hero-url">ÜRÜN LİNKİ</label>
              <input
                id="hero-url"
                ref={inputRef}
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder={PLACEHOLDERS[phIdx]}
                autoComplete="off"
                spellCheck="false"
              />
            </div>
            <button type="submit" className="paste-rig__submit">
              <span>Analiz Et</span>
              <span className="arrow">→</span>
            </button>
          </form>

          <div className="hero__support">
            Trendyol · Hepsiburada · Amazon linklerini destekler
          </div>

          <div className="hero__trust">
            <span>· 12.400+ ürün analiz edildi</span>
            <span>· %94 doğruluk</span>
            <span>· Ücretsiz · reklamsız</span>
          </div>
        </div>

        {/* right diorama: vertical brass distillation column */}
        <aside className="hero__column" aria-hidden="true">
          <div className="column__cap"></div>
          <div className="column__shaft">
            <div className="column__liquid"></div>
            <div className="column__beam"></div>
          </div>
          <div className="column__base"></div>
          <div className="column__plate">
            <span>STELLAR X2 · TY-9484017</span>
            <span>damıtma odaklı · 4127 sinyal</span>
          </div>

          {/* labels float to the LEFT of the column, each connected by a tick */}
          <div className="column__labels">
            {ALCOVE_NAMES.map(([n, name, palette], i) => (
              <div key={n} className="grad" style={{ top: `${10 + i * 13.5}%` }}>
                <span className="grad__palette">{palette}</span>
                <span className="grad__name">{name}</span>
                <span className="grad__num">{n}</span>
                <span className="grad__tick"></span>
              </div>
            ))}
          </div>
        </aside>
      </div>

      <div className="hero__floor">
        <div className="hero__floor-rule"></div>
        <div className="hero__scroll">
          <span className="line"></span>
          <span>kaydırarak 6 adımı görün</span>
          <span className="line"></span>
        </div>
      </div>
    </section>
  );
}

/* ============================================================
   Auth Modal — Giriş / Kayıt / Şifre sıfırlama (gerçek API)
   ============================================================ */
function AuthModal({
  mode,
  onClose,
  onSwitch,
}: {
  mode: AuthMode;
  onClose: () => void;
  onSwitch: (m: AuthMode) => void;
}) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [pwd, setPwd] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // close on ESC
  useEffect(() => {
    if (!mode) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [mode, onClose]);

  if (!mode) return null;

  const isLogin = mode === "login";
  const isForgot = mode === "forgot";
  const title = isForgot ? "Şifre sıfırla" : isLogin ? "Hoş geldiniz" : "Hesap oluşturun";
  const cta = isForgot ? "Bağlantı gönder" : isLogin ? "Giriş Yap" : "Hesap Oluştur";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (loading) return;
    setError(null);
    setSuccess(null);

    if (!email.trim()) return;
    if (!isForgot && !pwd.trim()) return;
    if (mode === "register" && !name.trim()) return;

    setLoading(true);
    try {
      if (mode === "register") {
        const parts = name.trim().split(/\s+/);
        const firstName = parts[0];
        const lastName = parts.slice(1).join(" ") || parts[0];
        const res = await registerUser(firstName, lastName, email.trim(), pwd);
        if (res.success) setSuccess(res.message);
        else setError(res.error);
      } else if (mode === "login") {
        const res = await loginUser(email.trim(), pwd);
        if (res.success) {
          setSuccess(res.message ? `Giriş başarılı! ${res.message}` : "Giriş başarılı!");
          setTimeout(() => onClose(), res.message ? 1600 : 700);
        } else {
          setError(res.error);
        }
      } else {
        const res = await forgotPassword(email.trim());
        if (res.success) setSuccess(res.message);
        else setError(res.error);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-backdrop" onClick={onClose}>
      <div className="auth-card" onClick={(e) => e.stopPropagation()}>
        <button type="button" className="auth-close" onClick={onClose} aria-label="Kapat">
          <span>×</span>
        </button>

        <div className="auth-card__head">
          <span className="auth-kicker">
            {isForgot ? "ŞİFRE SIFIRLAMA" : isLogin ? "GİRİŞ" : "YENİ HESAP"}
          </span>
          <h3 className="auth-title">
            {title.split(" ").map((w, i, arr) =>
              i === arr.length - 1 ? <em key={i}>{w}</em> : <span key={i}>{w} </span>
            )}
          </h3>
          <p className="auth-sub">
            {isForgot
              ? "E-postanıza bir sıfırlama bağlantısı gönderelim."
              : isLogin
              ? "Geçmiş analizleriniz ve favori ürünleriniz için."
              : "Analiz geçmişinizi kaydedin, fiyat takibi kurun."}
          </p>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          {mode === "register" && (
            <label className="auth-field">
              <span>Ad Soyad</span>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Adınız Soyadınız"
                autoComplete="name"
              />
            </label>
          )}

          <label className="auth-field">
            <span>E-posta</span>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="ornek@eposta.com"
              autoComplete="email"
              required
            />
          </label>

          {!isForgot && (
            <label className="auth-field">
              <span>Şifre</span>
              <input
                type="password"
                value={pwd}
                onChange={(e) => setPwd(e.target.value)}
                placeholder="••••••••"
                autoComplete={isLogin ? "current-password" : "new-password"}
                minLength={6}
                required
              />
            </label>
          )}

          {isLogin && (
            <div className="auth-meta">
              <a onClick={() => onSwitch("forgot")}>Şifremi unuttum</a>
            </div>
          )}

          {error && <p className="auth-feedback auth-feedback--error">{error}</p>}
          {success && <p className="auth-feedback auth-feedback--success">{success}</p>}

          <button type="submit" className="auth-submit" disabled={loading}>
            {loading ? (
              <span>Bekleyin…</span>
            ) : (
              <>
                <span>{cta}</span>
                <span className="arrow">→</span>
              </>
            )}
          </button>
        </form>

        <div className="auth-switch">
          {isForgot ? (
            <>
              <span>Şifrenizi hatırladınız mı?</span>
              <button type="button" onClick={() => onSwitch("login")}>
                Giriş Yap
              </button>
            </>
          ) : (
            <>
              <span>{isLogin ? "Hesabınız yok mu?" : "Zaten üye misiniz?"}</span>
              <button type="button" onClick={() => onSwitch(isLogin ? "register" : "login")}>
                {isLogin ? "Kayıt Ol" : "Giriş Yap"}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
