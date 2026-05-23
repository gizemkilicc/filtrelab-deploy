"use client";

/* ============================================================
   FiltreLAB — Alcove components
   Each alcove is a cinematic mise-en-scène explaining one step
   of the analysis, using a single sample product.
   ============================================================ */

import { useMemo, useRef, useState, type CSSProperties, type ReactNode } from "react";
import { rand } from "./rng";

// --- shared sample dataset (single product, the corridor IS the analysis) ---
export const PRODUCT = {
  brand: "STELLAR",
  name: "Stellar X2 — Aktif Gürültü Önleyici Kulaklık",
  shortName: "Stellar X2",
  url: "trendyol.com/stellar/x2-anc-kulaklik-p-9484017",
  price: "2.847 ₺",
  rrp: "3.249 ₺",
  reviews: 4127,
  verifiedShare: 0.62,
  fakeRisk: 0.34,
  returnRate: 0.21,
  trust: 0.58,
  dataSource: "Trendyol Open API · 19 May 2026 · 03:14 GMT+3",
  dataQuality: "Yorum örneklemi 4127/4127 · Eksik veri yok · Çapraz kaynak 2/3",
};

export type Verdict = "BUY" | "CAUTION" | "WAIT";
export type Confidence = "HIGH" | "MEDIUM" | "LOW";

// ============================================================
// SHARED CHROME
// ============================================================
function Ribbon({ index, name, step }: { index: number; name: string; step?: string }) {
  const n = String(index).padStart(2, "0");
  return (
    <div className="alcove__ribbon">
      <b>EVRE {n}</b>
      <span className="rule"></span>
      <span>{name}</span>
      {step && (
        <>
          <span className="rule rule--soft"></span>
          <span className="alcove__ribbon-step">{step}</span>
        </>
      )}
    </div>
  );
}

function Caption({ children }: { children: ReactNode }) {
  return <div className="alcove__caption">{children}</div>;
}

// ============================================================
// 1 · ŞÜPHENİN ODASI — vitrine + URL ticket + drifting particles
// ============================================================
export function AlcoveWelcome({ submittedUrl }: { submittedUrl?: string }) {
  const particles = useMemo(() => {
    const arr = [];
    for (let i = 0; i < 38; i++) {
      let k = i * 11 + 1;
      const rnd = () => rand(k++);
      const suspicious = rnd() < 0.28;
      arr.push({
        left: rnd() * 100,
        top: rnd() * 100,
        s: 2 + rnd() * 5,
        d: 10 + rnd() * 16,
        delay: -rnd() * 12,
        dx: (rnd() - 0.5) * 80,
        dy: (rnd() - 0.5) * 100,
        c: suspicious ? "#6a5fa8" : "#fbf8ef",
        o: suspicious ? 0.55 : 0.85,
      });
    }
    return arr;
  }, []);

  return (
    <section
      className="alcove alcove--welcome"
      data-screen-label="01 Şüphenin Odası"
      style={{ "--echo-color": "transparent" } as CSSProperties}
    >
      <Ribbon index={1} name="Linki Tanıma" step="ürün algılandı" />
      <div className="alcove__inner">
        <div className="alcove__stage">
          <div className="particles">
            {particles.map((p, i) => (
              <span
                key={i}
                style={
                  {
                    left: `${p.left}%`,
                    top: `${p.top}%`,
                    "--s": `${p.s}px`,
                    "--d": `${p.d}s`,
                    "--delay": `${p.delay}s`,
                    "--dx": `${p.dx}px`,
                    "--dy": `${p.dy}px`,
                    "--c": p.c,
                    "--o": p.o,
                  } as CSSProperties
                }
              />
            ))}
          </div>

          <div className="vitrine">
            <div className="vitrine__column">
              <div className="vitrine__case">
                <div className="vitrine__product">
                  <svg viewBox="0 0 200 280" preserveAspectRatio="xMidYMid meet">
                    <defs>
                      <linearGradient id="cup" x1="0" y1="0" x2="1" y2="1">
                        <stop offset="0%" stopColor="#3a3631" />
                        <stop offset="100%" stopColor="#0e0d0b" />
                      </linearGradient>
                    </defs>
                    {/* stylized headphone silhouette */}
                    <path
                      d="M40 130 Q40 50 100 50 Q160 50 160 130"
                      stroke="#2a2823"
                      strokeWidth="6"
                      fill="none"
                      strokeLinecap="round"
                    />
                    <ellipse cx="40" cy="160" rx="34" ry="44" fill="url(#cup)" />
                    <ellipse cx="160" cy="160" rx="34" ry="44" fill="url(#cup)" />
                    <ellipse cx="40" cy="160" rx="20" ry="28" fill="#1a1916" />
                    <ellipse cx="160" cy="160" rx="20" ry="28" fill="#1a1916" />
                  </svg>
                  <span className="label">PLACEHOLDER · ürün modeli</span>
                </div>
              </div>
            </div>
          </div>

          <div className="ticket">
            <span className="stamp">URL · BİLET</span>
            <div className="url">{submittedUrl || PRODUCT.url}</div>
            <div className="meta">
              <span>tarayıcıdan alındı</span>
              <span>03:14:22</span>
            </div>
          </div>
        </div>

        <Caption>
          <div className="data-row">
            <span>analiz edilen ürün</span>
            <span>· 19.05.2026</span>
          </div>
          <h2 className="title">
            <em>1. adım:</em>
            <br />
            Link&apos;i tanıyoruz.
          </h2>
          <p className="lede">
            Yapıştırdığınız linki anında okuyor, ürünü cam vitrine yerleştiriyoruz. Şu andan
            itibaren reklamla, tıklama tuzağıyla uğraşmayacaksınız — sadece gerçek verilerle.
          </p>
          <div className="data-row" style={{ marginTop: 24 }}>
            <strong>{PRODUCT.shortName}</strong>
          </div>
          <div className="data-row">
            <span>· marka</span>
            <span>{PRODUCT.brand}</span>
            <span>· liste fiyatı</span>
            <span>{PRODUCT.rrp}</span>
          </div>
        </Caption>
      </div>

      <div className="scroll-hint">
        <span className="line"></span>
        <span>laboratuvara in</span>
        <span className="line"></span>
      </div>
    </section>
  );
}

// ============================================================
// 2 · YORUM TARLASI — astrolabe of comment cards
// ============================================================
const SAMPLE_REVIEWS: [string, string, string][] = [
  ["★★★★★", "Ses kalitesi bu fiyata harika.", "pos"],
  ["★★★☆☆", "Kulaklarımı sıkıyor ama 2-3 günde geçti.", "mid"],
  ["★☆☆☆☆", "ANC çalışmıyor, mağazaya iade ettim.", "neg"],
  ["★★★★☆", "Trendyol'dan aldım, kutusu hasarlıydı.", "pos"],
  ["★★★☆☆", "Pil ömrü reklamdaki gibi değil.", "mid"],
  ["★★★★★", "Mükemmel ürün, herkese tavsiye ederim.", "pos"],
  ["★☆☆☆☆", "İkinci günde sol kulaklık öldü.", "neg"],
  ["★★★☆☆", "Fiyatına göre iyi ama premium değil.", "mid"],
  ["★★★★★", "Telefonla eşleştirme çok kolay.", "pos"],
  ["★★★★★", "Mükemmel ürün, herkese tavsiye ederim.", "pos"],
  ["★★★☆☆", "Mikrofon kalitesi yeterli, fazlası değil.", "mid"],
  ["★★★★★", "5 yıldız hak ediyor cidden.", "pos"],
  ["★☆☆☆☆", "Boya birkaç haftada soyuldu.", "neg"],
  ["★★★★☆", "Uzun yolculukta kurtardı.", "pos"],
  ["★★★★★", "Tam aradığım ürün, çok teşekkürler.", "pos"],
];

export function AlcoveField() {
  // distribute the reviews on three rings
  const cards = useMemo(() => {
    return SAMPLE_REVIEWS.map((r, i) => {
      const ring = i % 3; // 0 outer, 1 mid, 2 inner
      const radius = [42, 30, 19][ring];
      const angle = ((i / SAMPLE_REVIEWS.length) * 360 + ring * 22) % 360;
      const rad = (angle * Math.PI) / 180;
      const x = 50 + Math.cos(rad) * radius;
      const y = 50 + Math.sin(rad) * radius;
      const rot = (rand(i * 3 + 1) - 0.5) * 14;
      return { stars: r[0], body: r[1], cls: r[2], x, y, rot };
    });
  }, []);

  return (
    <section
      className="alcove alcove--field"
      data-screen-label="02 Yorum Tarlası"
      style={{ "--echo-color": "rgba(247,244,236,0.18)" } as CSSProperties}
    >
      <Ribbon index={2} name="Yorum Analizi" step="Duygu dağılımı çıkarılıyor" />
      <div className="alcove__inner">
        <div className="alcove__stage">
          <div className="astrolabe">
            <div className="astrolabe__ring">
              <div className="astrolabe__ring astrolabe__ring--inner"></div>
              <div className="astrolabe__ring astrolabe__ring--core"></div>
              <div className="astrolabe__core">
                <div className="count">{PRODUCT.reviews.toLocaleString("tr-TR")}</div>
                <div className="label">ses süzüldü</div>
              </div>
            </div>

            {cards.map((c, i) => (
              <div
                key={i}
                className={`review review--${c.cls}`}
                style={
                  {
                    left: `${c.x}%`,
                    top: `${c.y}%`,
                    "--rot": `${c.rot}deg`,
                  } as CSSProperties
                }
              >
                <div className="stars">{c.stars}</div>
                <div className="body">{c.body}</div>
              </div>
            ))}
          </div>
        </div>

        <Caption>
          <div className="data-row">
            <span>{PRODUCT.reviews.toLocaleString("tr-TR")} yorum taranıyor</span>
          </div>
          <h2 className="title">
            <em>2. adım:</em>
            <br />
            Yorumları süzüyoruz.
          </h2>
          <p className="lede">
            Binlerce yorumu okuyup olumlu, nötr ve olumsuz olarak ayırıyoruz. Renk değişimi
            duygu değişimini gösterir: yeşil olumlu, kehribar nötr, kızıl olumsuz.
          </p>
          <div className="data-row" style={{ marginTop: 24 }}>
            <strong>%62</strong>
          </div>
          <div className="data-row">
            <span>· olumlu yorum oranı</span>
            <span>· doğrulanmış satın alma {Math.round(PRODUCT.verifiedShare * 100)}%</span>
          </div>
        </Caption>
      </div>
    </section>
  );
}

// ============================================================
// 3 · AYNALAR SALONU — bot reviews, mirrors crack, gold leaks
// ============================================================
const BOT_NEAR = [
  "Mükemmel ürün, herkese tavsiye ederim.",
  "Mükemmel ürün herkese tavsiye ederim!!",
  "Mükemmel bir ürün, herkese tavsiye ederim.",
  "Mükemmel ürün, herkese tavsiye ediyorum.",
  "Çok mükemmel ürün, herkese tavsiye ederim.",
  "Mükemmel ürün! Herkese tavsiye ederim.",
  "Mükemmel ürün, gerçekten herkese tavsiye ederim.",
  "Mükemmel ürün, herkese tavsiye ederim 🙂",
  "Mükemmel ürün! herkese tavsiye ederim.",
  "Mükemmel ürün, bu ürünü herkese tavsiye ederim.",
  "Mükemmel ürün, herkese tavsiye!",
];

export function AlcoveMirrors() {
  const [longPressed, setLongPressed] = useState(false);
  const pressTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const cells: { isCracked: boolean; phrase: string; signer: string }[] = [];
  for (let i = 0; i < 12; i++) {
    const isCracked = i === 6;
    const phrase = isCracked ? "verified · gerçek satın alma" : BOT_NEAR[i % BOT_NEAR.length];
    const signer = isCracked ? "K. D. — Eylül 2025" : `bot_${(2030 + i * 41).toString(36)}`;
    cells.push({ isCracked, phrase, signer });
  }

  const onPressStart = (i: number) => {
    if (i !== 6) return;
    pressTimer.current = setTimeout(() => setLongPressed(true), 600);
  };
  const onPressEnd = () => {
    if (pressTimer.current) clearTimeout(pressTimer.current);
  };

  return (
    <section
      className="alcove alcove--mirrors"
      data-screen-label="03 Aynalar Salonu"
      style={{ "--echo-color": "rgba(212,185,107,0.12)" } as CSSProperties}
    >
      <Ribbon index={3} name="Sahte Yorum Kontrolü" step="Bot kalıpları taranıyor" />
      <div className="alcove__inner">
        <div className="alcove__stage">
          <div className="mirrors">
            <div className="mirrors__rack">
              {cells.map((c, i) => (
                <div
                  key={i}
                  className={`mirror ${c.isCracked ? "mirror--cracked" : "mirror--bot"}`}
                  onMouseDown={() => onPressStart(i)}
                  onMouseUp={onPressEnd}
                  onMouseLeave={onPressEnd}
                  onTouchStart={() => onPressStart(i)}
                  onTouchEnd={onPressEnd}
                >
                  {!c.isCracked && (
                    <>
                      <span>“{c.phrase}”</span>
                      <div className="signature">{c.signer}</div>
                    </>
                  )}
                  {c.isCracked && (
                    <span
                      style={{
                        color: "#d9b65c",
                        fontStyle: "normal",
                        fontFamily: "var(--mono)",
                        fontSize: 9,
                        letterSpacing: "0.3em",
                        textTransform: "uppercase",
                        position: "relative",
                        zIndex: 2,
                      }}
                    >
                      {longPressed ? "verified pattern" : "gerçek"}
                    </span>
                  )}
                </div>
              ))}
            </div>
            <div className="bot-flag">
              <span className="dot"></span>
              <span>%34 bot kalıbı tespit</span>
            </div>
          </div>
        </div>

        <Caption>
          <div className="data-row">
            <span>bot kalıbı tespit edildi</span>
          </div>
          <h2 className="title">
            <em>3. adım:</em>
            <br />
            Sahteleri yakalıyoruz.
          </h2>
          <p className="lede">
            Bot hesaplar genellikle aynı cümleyi farklı şekillerde yazar. Bu kalıpları tespit
            ediyor, gerçek yorumları sahtelerinden ayırıyoruz. Bir aynaya basılı tutun, gerçek
            satın alma kalıbını görün.
          </p>
          <div className="data-row" style={{ marginTop: 24 }}>
            <strong>%34</strong>
          </div>
          <div className="data-row">
            <span>· sahte yorum oranı</span>
            <span>· {Math.round((1 - PRODUCT.fakeRisk) * PRODUCT.reviews)} gerçek yorum</span>
          </div>
          {longPressed && (
            <div className="data-row" style={{ color: "#d9b65c" }}>
              <span>doğrulanmış satın alma %62 · 14 ay yayılım</span>
            </div>
          )}
        </Caption>
      </div>
      <div className="gesture-hint">bir aynaya basılı tutun</div>
    </section>
  );
}

// ============================================================
// 4 · İADE TÜNELİ — conveyor belt of stylized parcels
// ============================================================
export function AlcoveReturns() {
  const parcels = useMemo(() => {
    const arr = [];
    for (let i = 0; i < 9; i++) {
      const torn = i % 5 === 2; // ~%20 return rate visually
      arr.push({
        left: (i / 9) * 110 - 10,
        bottom: 60 + (i % 2) * 8,
        torn,
        delay: -i * 1.6,
      });
    }
    return arr;
  }, []);

  return (
    <section
      className="alcove alcove--returns"
      data-screen-label="04 İade Tüneli"
      style={{ "--echo-color": "rgba(20,20,15,0.6)" } as CSSProperties}
    >
      <Ribbon index={4} name="İade Riski" step="İade verileri hesaplanıyor" />
      <div className="alcove__inner">
        <div className="alcove__stage">
          <div className="tunnel">
            <div className="tunnel__walls"></div>
            <div className="belt">
              <div className="belt__surface"></div>
              {parcels.map((p, i) => (
                <div
                  key={i}
                  className={`parcel ${p.torn ? "parcel--torn" : ""}`}
                  style={{
                    left: `${p.left}%`,
                    bottom: `${p.bottom}px`,
                    animation: `parcel-${p.torn ? "u" : "fwd"} 9s linear infinite`,
                    animationDelay: `${p.delay}s`,
                  }}
                >
                  {p.torn && <div className="label-strip"></div>}
                  <span>{p.torn ? "İADE" : "ALINDI"}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <Caption>
          <div className="data-row">
            <span>iade tahmini</span>
          </div>
          <h2 className="title">
            <em>4. adım:</em>
            <br />
            İade riskini ölçüyoruz.
          </h2>
          <p className="lede">
            Bu ürünün kaç müşteri tarafından iade edildiğini ve neden iade edildiğini
            hesaplıyoruz. Düşük risk: paket müşteriye ulaşır. Yüksek risk: U dönüşü yapar,
            kategori ortalamasının üzerindedir.
          </p>
          <div className="data-row" style={{ marginTop: 24 }}>
            <strong>%21</strong>
          </div>
          <div className="data-row">
            <span>· iade oranı</span>
            <span>· kategori ortalaması %14</span>
          </div>
        </Caption>
      </div>
      <style>{`
        @keyframes parcel-fwd {
          0%   { transform: translateX(0); }
          100% { transform: translateX(140%); }
        }
        @keyframes parcel-u {
          0%   { transform: translateX(0) translateY(0); }
          45%  { transform: translateX(70%) translateY(0); }
          55%  { transform: translateX(70%) translateY(-30px) rotate(180deg); }
          100% { transform: translateX(-30%) translateY(-30px) rotate(180deg); }
        }
      `}</style>
    </section>
  );
}

// ============================================================
// 5 · FİYAT TERAZİSİ — antique brass scale + alt cards
// ============================================================
const ALTERNATIVES = [
  { name: "Auralia M3", price: "2.299 ₺", link: "hepsiburada.com/auralia-m3" },
  { name: "Boreal Note 2", price: "2.499 ₺", link: "trendyol.com/boreal-note-2" },
  { name: "Kervan ANC", price: "2.749 ₺", link: "amazon.com.tr/kervan-anc" },
  { name: "Northwind P1", price: "3.099 ₺", link: "trendyol.com/northwind-p1" },
];

export function AlcoveScale() {
  const [active, setActive] = useState<number | null>(null);

  // analyzed product is overpriced — left pan goes down. tilt: negative = left side down
  const tilt = -6;

  return (
    <section
      className="alcove alcove--scale"
      data-screen-label="05 Fiyat Terazisi"
      style={{ "--echo-color": "rgba(45,40,30,0.5)" } as CSSProperties}
    >
      <Ribbon index={5} name="Fiyat Karşılaştırması" step="Pazardaki alternatifler taranıyor" />
      <div className="alcove__inner">
        <div className="alcove__stage">
          <div className="scale">
            <div className="scale__rig">
              <div className="scale__column"></div>
              <div className="scale__cap"></div>
              <div className="scale__beam" style={{ "--tilt": `${tilt}deg` } as CSSProperties}></div>

              <div className="pan pan--left" style={{ "--lift-l": "44px" } as CSSProperties}>
                <div className="pan__load">
                  <div className="product-mark"></div>
                  <div>{PRODUCT.shortName}</div>
                  <div className="price">{PRODUCT.price}</div>
                </div>
              </div>

              <div className="pan pan--right" style={{ "--lift-r": "-44px" } as CSSProperties}>
                <div className="pan__load">
                  <div className="alt-stack">
                    {ALTERNATIVES.map((a, i) => (
                      <div
                        key={i}
                        className="alt"
                        onMouseEnter={() => setActive(i)}
                        onMouseLeave={() => setActive(null)}
                      ></div>
                    ))}
                  </div>
                  <div>alternatifler</div>
                  <div className="price" style={{ fontSize: 18 }}>
                    2.299 — 3.099 ₺
                  </div>
                </div>
              </div>
            </div>

            {active !== null && (
              <div className="alt-card" style={{ left: "62%", top: "26%" }}>
                <div className="name">{ALTERNATIVES[active].name}</div>
                <div className="price">{ALTERNATIVES[active].price}</div>
                <div className="link">{ALTERNATIVES[active].link} →</div>
              </div>
            )}
          </div>
        </div>

        <Caption>
          <div className="data-row">
            <span>pazar karşılaştırması</span>
          </div>
          <h2 className="title">
            <em>5. adım:</em>
            <br />
            Fiyatı karşılaştırıyoruz.
          </h2>
          <p className="lede">
            Sol kefede sizin seçtiğiniz ürün, sağ kefede pazardaki dört alternatif. Eğim, fiyat
            farkını gösterir. Bir alternatifin üzerine gelin: adı, fiyatı ve linki anında
            karşınıza çıkar.
          </p>
          <div className="data-row" style={{ marginTop: 24 }}>
            <strong>+%14</strong>
          </div>
          <div className="data-row">
            <span>· pazar ortalamasının %14 üzerinde</span>
          </div>
        </Caption>
      </div>
      <div className="gesture-hint">alternatifin üzerine gelin</div>
    </section>
  );
}

// ============================================================
// 6 · KARAR MAHKEMESİ — three doors, one opens itself
// ============================================================
const VERDICTS: Record<Verdict, { key: string; label: string; cls: string; future: string }> = {
  BUY: {
    key: "ALINABİLİR",
    label: "Alınabilir",
    cls: "buy",
    future:
      "Paket dördüncü gün elinde. Kulaklığı taktığında ilk dakikada doğru kararı verdiğini anlıyorsun.",
  },
  CAUTION: {
    key: "DİKKATLİ İNCELE",
    label: "Dikkatli incele",
    cls: "caution",
    future:
      "Almadan önce iki yorum daha okuyorsun. Boya soyulması ihtimali için renk seçimini yeniden düşünüyorsun.",
  },
  WAIT: {
    key: "BEKLE",
    label: "Bekle",
    cls: "wait",
    future: "Bir hafta sabredersen kategori daha berrak. Vitrini kapatıyorsun, kahveni alıyorsun.",
  },
};

const DECLINE_REASONS: Record<Verdict, string> = {
  BUY: "Sahte yorum riski %34 — kategori ortalamasının iki katı. Şu an kararı satın alma yönüne yatırmıyoruz.",
  CAUTION:
    "Fiyat pazar medyanının üzerinde değil; ANC çalışmıyor temalı yorumlar tek bir partide kümeleniyor. “Dikkatli incele” bu sinyalin tek başına ana karar olmasını engelliyor.",
  WAIT: "İade oranı yüksek ama iadelerin %71’i renk uyumsuzluğu. Bu, ürünün niteliği değil seçim aşaması sinyali — beklemek çözüm değil.",
};

export function AlcoveCourt({
  verdict,
  confidence,
}: {
  verdict: Verdict;
  confidence: Confidence;
}) {
  const [declined, setDeclined] = useState<Verdict | null>(null);

  const order: Verdict[] = ["BUY", "CAUTION", "WAIT"];
  const confidenceLabel =
    { HIGH: "Yüksek Güven", MEDIUM: "Orta Güven", LOW: "Düşük Güven" }[confidence] ||
    "Orta Güven";
  const lowConfidence = confidence === "LOW";

  return (
    <section
      className="alcove alcove--court"
      data-screen-label="06 Karar Mahkemesi"
      style={{ "--echo-color": "rgba(180,150,80,0.18)" } as CSSProperties}
    >
      <Ribbon index={6} name="Nihai Karar" step="Tüm veriler birleştiriliyor" />
      <div className="alcove__inner">
        <div className="alcove__stage">
          <div className="court">
            <div className="court__floor"></div>
            <div className="doors">
              {order.map((k) => {
                const v = VERDICTS[k];
                const isActive = verdict === k;
                return (
                  <div
                    key={k}
                    className={`door door--${v.cls} ${
                      isActive ? "door--open door--active" : "door--breathing"
                    }`}
                    onClick={() => !isActive && setDeclined(k)}
                  >
                    <div className="door__frame"></div>
                    <div className="door__crack">
                      <div className="door__crack-inner">
                        <div className="door__future">
                          <div className="scene">mikro-gelecek</div>
                          <span>{v.future}</span>
                        </div>
                      </div>
                    </div>
                    <div className="door__verdict">
                      <span>{v.label}</span>
                      <span className="door__verdict-key">{v.key}</span>
                    </div>
                  </div>
                );
              })}
            </div>

            <div
              className={`declined-note ${declined ? "visible" : ""}`}
              onClick={() => setDeclined(null)}
            >
              <h4>{declined ? VERDICTS[declined].key + " · neden değil" : ""}</h4>
              <div>{declined ? DECLINE_REASONS[declined] : ""}</div>
              {declined && lowConfidence && (
                <div
                  style={{
                    marginTop: 14,
                    fontFamily: "var(--mono)",
                    fontSize: 10,
                    letterSpacing: "0.22em",
                    textTransform: "uppercase",
                    color: "#c79366",
                  }}
                >
                  · low_confidence · veri örneklemi zayıf
                </div>
              )}
            </div>
          </div>
        </div>

        <Caption>
          <div className="data-row">
            <span>sizin için seçtiğimiz tek seçenek</span>
          </div>
          <h2 className="title">
            <em>6. adım:</em>
            <br />
            Kararla biten yol.
          </h2>
          <p className="lede">
            Tüm verileri birleştirip size <strong>tek</strong> bir cevap veriyoruz:{" "}
            <strong>alınabilir</strong>, <strong>dikkatli inceleyin</strong> ya da{" "}
            <strong>bekleyin</strong>. Kapalı bir kapıya dokunun, neden o seçeneği
            önermediğimizi görün.
          </p>
          <div className="data-row" style={{ marginTop: 24 }}>
            <strong>{VERDICTS[verdict].key}</strong>
          </div>
          <div className="verdict-strip">
            <span className="verdict-pill">{confidenceLabel}</span>
            <span>güven {Math.round(PRODUCT.trust * 100)}%</span>
            {lowConfidence && <span className="low-conf">· LOW_CONFIDENCE</span>}
          </div>
        </Caption>
      </div>
      <div className="gesture-hint">kapalı bir kapıya dokunun</div>
    </section>
  );
}
