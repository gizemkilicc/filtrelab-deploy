"use client";

/**
 * Landing page'in scrollytelling devamı — 6 tam ekran "adım" bölümü.
 * Her bölüm: sol ray (01-06), ortada illüstrasyon, sağda metin.
 * Tamamen dekoratif; işlevsel state/API yok.
 */

import { motion } from "framer-motion";

const RAIL = [
  "Linki Tanıma",
  "Yorum Analizi",
  "Sahte Yorum Kontrolü",
  "İade Riski",
  "Fiyat Karşılaştırması",
  "Nihai Karar",
];

type Tone = {
  bg: string;
  text: string;
  dim: string;
  faint: string;
  line: string;
  cardBg: string;
  cardBorder: string;
};

const DARK: Tone = {
  bg: "radial-gradient(ellipse 130% 90% at 50% 0%, #1a1813 0%, #0a0908 70%)",
  text: "var(--paper)",
  dim: "var(--ink-30)",
  faint: "var(--ink-50)",
  line: "var(--ink-70)",
  cardBg: "rgba(20,18,14,0.85)",
  cardBorder: "#2a2823",
};

const LIGHT: Tone = {
  bg: "radial-gradient(ellipse 130% 90% at 50% 0%, #f6f3ec 0%, #e6e0d2 75%)",
  text: "#26241f",
  dim: "#8a8273",
  faint: "#a89f8c",
  line: "#d2cab8",
  cardBg: "#fbf9f3",
  cardBorder: "#d6cdbb",
};

const TAN: Tone = {
  bg: "radial-gradient(ellipse 130% 90% at 50% 0%, #e9dcc0 0%, #d3c19b 80%)",
  text: "#3a3120",
  dim: "#8a7a57",
  faint: "#a8966e",
  line: "#c4ad81",
  cardBg: "#f0e7d2",
  cardBorder: "#c2ad82",
};

/* ── Sol ray ──────────────────────────────────────────────── */
function Rail({ active, tone }: { active: number; tone: Tone }) {
  return (
    <div className="hidden shrink-0 flex-col gap-3 lg:flex">
      {RAIL.map((label, i) => {
        const n = i + 1;
        const isActive = n === active;
        return (
          <div key={label} className="flex items-center gap-2">
            <span
              className="fl-mono text-[10px]"
              style={{ color: isActive ? "var(--brass)" : tone.faint }}
            >
              {String(n).padStart(2, "0")}
            </span>
            <span
              className="block h-px transition-all"
              style={{
                width: isActive ? 26 : 12,
                background: isActive ? "var(--brass)" : tone.line,
              }}
            />
            <span
              className="fl-mono text-[9px] uppercase tracking-[0.13em]"
              style={{ color: isActive ? "var(--brass)" : tone.faint }}
            >
              {label}
            </span>
          </div>
        );
      })}
    </div>
  );
}

/* ── Bölüm başlığı ────────────────────────────────────────── */
function SectionHead({
  index,
  evre,
  sub,
  tone,
}: {
  index: number;
  evre: string;
  sub: string;
  tone: Tone;
}) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-3">
        <span className="fl-mono text-[10px] uppercase tracking-[0.16em]" style={{ color: tone.dim }}>
          Evre {String(index).padStart(2, "0")}
        </span>
        <span className="h-px w-8" style={{ background: tone.line }} />
        <span className="fl-mono text-[10px] uppercase tracking-[0.16em]" style={{ color: tone.text }}>
          {evre}
        </span>
        <span className="hidden fl-serif italic text-[13px] sm:inline" style={{ color: tone.faint }}>
          {sub}
        </span>
      </div>
      <div className="flex items-baseline gap-2">
        <span className="fl-serif italic text-[15px]" style={{ color: tone.text }}>
          FiltreLAB
        </span>
        <span className="hidden fl-mono text-[8px] uppercase tracking-[0.2em] sm:inline" style={{ color: tone.dim }}>
          Akıllı Alışveriş Asistanı
        </span>
      </div>
    </div>
  );
}

/* ── Sağ metin bloğu ──────────────────────────────────────── */
function TextBlock({
  kicker,
  adim,
  title,
  body,
  stat,
  statSub,
  tone,
}: {
  kicker: string;
  adim: string;
  title: string;
  body: string;
  stat: string;
  statSub: string;
  tone: Tone;
}) {
  return (
    <div className="w-full max-w-[340px] shrink-0">
      <p className="fl-mono text-[9px] uppercase tracking-[0.16em]" style={{ color: tone.dim }}>
        {kicker}
      </p>
      <p className="fl-serif italic mt-5 text-[26px]" style={{ color: "var(--brass)" }}>
        {adim}
      </p>
      <h2 className="fl-serif text-[44px] leading-[1.04]" style={{ color: tone.text }}>
        {title}
      </h2>
      <p className="fl-sans mt-5 text-[13px] leading-relaxed" style={{ color: tone.dim }}>
        {body}
      </p>
      <p className="fl-serif mt-8 text-[40px] leading-none" style={{ color: "var(--brass)" }}>
        {stat}
      </p>
      <p className="fl-mono mt-3 text-[9px] uppercase tracking-[0.14em]" style={{ color: tone.dim }}>
        {statSub}
      </p>
    </div>
  );
}

/* ── Bölüm kabuğu ─────────────────────────────────────────── */
function Section({
  index,
  evre,
  sub,
  tone,
  footer,
  illustration,
  text,
}: {
  index: number;
  evre: string;
  sub: string;
  tone: Tone;
  footer: string;
  illustration: React.ReactNode;
  text: React.ReactNode;
}) {
  return (
    <section
      className="relative flex min-h-screen flex-col overflow-hidden px-6 py-8 md:px-12"
      style={{ background: tone.bg }}
    >
      <SectionHead index={index} evre={evre} sub={sub} tone={tone} />

      <motion.div
        initial={{ opacity: 0, y: 24 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-120px" }}
        transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
        className="flex flex-1 flex-col items-center gap-10 py-10 lg:flex-row lg:gap-12"
      >
        <Rail active={index} tone={tone} />
        <div className="relative flex flex-1 items-center justify-center">{illustration}</div>
        {text}
      </motion.div>

      <p
        className="text-center fl-mono text-[9px] uppercase tracking-[0.2em]"
        style={{ color: tone.faint }}
      >
        {footer}
      </p>
    </section>
  );
}

/* ════════════════════════════════════════════════════════════
   01 — LİNKİ TANIMA
   ════════════════════════════════════════════════════════════ */
function StepOne() {
  return (
    <Section
      index={1}
      evre="Linki Tanıma"
      sub="Ürün doğrulanıyor"
      tone={LIGHT}
      footer="— Laboratuvara in —"
      illustration={
        <div className="relative">
          {/* Ürün kartı */}
          <div
            className="flex h-[420px] w-[300px] flex-col items-center justify-center border"
            style={{ background: "#ffffff", borderColor: "#e3ddce" }}
          >
            <svg viewBox="0 0 220 200" className="h-44 w-44" aria-hidden="true">
              <path
                d="M44 122 a66 66 0 0 1 132 0"
                fill="none"
                stroke="#1c1c1c"
                strokeWidth="11"
                strokeLinecap="round"
              />
              <rect x="26" y="108" width="40" height="74" rx="19" fill="#1c1c1c" />
              <rect x="154" y="108" width="40" height="74" rx="19" fill="#1c1c1c" />
              <circle cx="46" cy="145" r="13" fill="#3a3a3a" />
              <circle cx="174" cy="145" r="13" fill="#3a3a3a" />
            </svg>
            <p className="fl-mono mt-10 text-[9px] uppercase tracking-[0.18em]" style={{ color: "#a89f8c" }}>
              Placeholder · Ürün Modeli
            </p>
          </div>

          {/* URL bileti */}
          <div
            className="absolute -bottom-6 -left-16 w-[244px] -rotate-3 border px-4 py-3 shadow-[0_18px_40px_rgba(0,0,0,0.12)]"
            style={{ background: "#fbf9f3", borderColor: "#ddd5c4" }}
          >
            <div className="flex items-center justify-between">
              <span
                className="fl-mono text-[8px] uppercase tracking-[0.16em]"
                style={{ color: "var(--brass-deep)" }}
              >
                URL · Bilet
              </span>
            </div>
            <p className="fl-mono mt-2 break-all text-[10px] leading-snug" style={{ color: "#3a3528" }}>
              trendyol.com/stellar/x2-anc-kulaklik-p-9484017
            </p>
            <div className="mt-2 flex items-center justify-between">
              <span className="fl-mono text-[8px] uppercase tracking-[0.14em]" style={{ color: "#a89f8c" }}>
                Taranıyor
              </span>
              <span className="fl-mono text-[8px]" style={{ color: "#a89f8c" }}>
                00:14:22
              </span>
            </div>
          </div>
        </div>
      }
      text={
        <TextBlock
          tone={LIGHT}
          kicker="Analiz Edilen Ürün · 19.05.2026"
          adim="1. adım:"
          title="Link'i tanıyoruz."
          body="Yapıştırdığınız linki anında okuyor, ürünü cam vitrine yerleştiriyoruz. Şu andan itibaren reklamlarla, reklam tuzağıyla uğraşmayacaksınız — sadece gerçek verilerle."
          stat="Stellar X2"
          statSub="Marka Stellar · Liste Fiyatı 3.249 ₺"
        />
      }
    />
  );
}

/* ════════════════════════════════════════════════════════════
   02 — YORUM ANALİZİ
   ════════════════════════════════════════════════════════════ */
const ORBIT_REVIEWS: { x: number; y: number; r: number; neg: boolean; stars: number; text: string }[] = [
  { x: 50, y: 4, r: -3, neg: false, stars: 4, text: "Boya birkaç hafta sonra soyuldu." },
  { x: 26, y: 14, r: 4, neg: false, stars: 3, text: "Mikrofon kalitesi yeterli, fazlası değil." },
  { x: 9, y: 30, r: -5, neg: false, stars: 5, text: "Mükemmel ürün, herkese tavsiye ederim." },
  { x: 13, y: 52, r: 3, neg: true, stars: 2, text: "Fiyatına göre iyi ama premium değil." },
  { x: 10, y: 72, r: -4, neg: false, stars: 5, text: "Mükemmel ürün, herkese tavsiye ederim." },
  { x: 26, y: 84, r: 5, neg: false, stars: 5, text: "Pil ömrü reklamdaki gibi değil." },
  { x: 33, y: 36, r: -2, neg: false, stars: 5, text: "Şıklıkla rahatlığı çok hoşuş." },
  { x: 50, y: 50, r: 0, neg: false, stars: 5, text: "Tam aradığım ürün, çok teşekkürler." },
  { x: 49, y: 92, r: 3, neg: false, stars: 5, text: "Trendyol'dan aldım, kutusu hasarlıydı." },
  { x: 67, y: 84, r: -4, neg: false, stars: 4, text: "Kulaklığın okuya sırası 3 günde geçti." },
  { x: 71, y: 62, r: 4, neg: true, stars: 1, text: "ANC çalışmıyor, mağazaya iade ettim." },
  { x: 64, y: 22, r: -3, neg: false, stars: 5, text: "3 yıldır ilk olarak çıktım." },
  { x: 80, y: 36, r: 2, neg: false, stars: 5, text: "Uzun yolculuğu kurtardı." },
  { x: 84, y: 56, r: -3, neg: false, stars: 5, text: "Ses kalitesi bu fiyata harika." },
];

function OrbitReview({
  x,
  y,
  r,
  neg,
  stars,
  text,
}: (typeof ORBIT_REVIEWS)[number]) {
  return (
    <div
      className="absolute w-[128px] -translate-x-1/2 -translate-y-1/2 border px-2.5 py-2"
      style={{
        left: `${x}%`,
        top: `${y}%`,
        rotate: `${r}deg`,
        background: "rgba(20,18,14,0.9)",
        borderColor: neg ? "#7a4a3f" : "#2a2823",
      }}
    >
      <div className="fl-mono text-[8px]" style={{ color: neg ? "#c08a6f" : "var(--brass)" }}>
        {"★".repeat(stars)}
        <span style={{ color: "#3a352c" }}>{"★".repeat(5 - stars)}</span>
      </div>
      <p className="fl-sans mt-1 text-[8.5px] leading-snug" style={{ color: "var(--ink-10)" }}>
        {text}
      </p>
      <p className="fl-mono mt-1 text-[7px]" style={{ color: "var(--ink-50)" }}>
        RVW_{String(Math.round(x * y)).padStart(4, "0")}
      </p>
    </div>
  );
}

function StepTwo() {
  return (
    <Section
      index={2}
      evre="Yorum Analizi"
      sub="Duygu dağılımı çıkarılıyor"
      tone={DARK}
      footer="— Sinyali gürültüden ayırıyoruz —"
      illustration={
        <div className="relative h-[500px] w-full max-w-[620px]">
          {/* Yörünge halkaları */}
          <div
            className="absolute left-1/2 top-1/2 h-[340px] w-[340px] -translate-x-1/2 -translate-y-1/2 rounded-full border"
            style={{ borderColor: "#2a2823" }}
          />
          <div
            className="absolute left-1/2 top-1/2 h-[210px] w-[210px] -translate-x-1/2 -translate-y-1/2 rounded-full border"
            style={{ borderColor: "#211f1a" }}
          />
          {/* Merkez sayaç */}
          <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 -rotate-6 text-center">
            <p className="fl-serif text-[44px] leading-none" style={{ color: "var(--brass)" }}>
              4.127
            </p>
            <p className="fl-mono mt-1 text-[9px] uppercase tracking-[0.2em]" style={{ color: "var(--ink-30)" }}>
              Ses Süzüldü
            </p>
          </div>
          {ORBIT_REVIEWS.map((rev, i) => (
            <OrbitReview key={i} {...rev} />
          ))}
        </div>
      }
      text={
        <TextBlock
          tone={DARK}
          kicker="4.127 Yorum Tarandı"
          adim="2. adım:"
          title="Yorumları süzüyoruz."
          body="Binlerce yorumu okuyup olumlu, nötr ve olumsuz olarak ayırıyoruz. Renk değişimi duygu değişimini gösterir: yeşil olumlu, kehribar nötr, kızıl olumsuz. Hangisinin gürültü olduğunu burada öğreniyoruz."
          stat="%62"
          statSub="Olumlu Yorum Oranı · Doğrulanmış Satın Alma %62"
        />
      }
    />
  );
}

/* ════════════════════════════════════════════════════════════
   03 — SAHTE YORUM KONTROLÜ
   ════════════════════════════════════════════════════════════ */
function StepThree() {
  const cards = Array.from({ length: 12 });
  const realIndex = 6;
  return (
    <Section
      index={3}
      evre="Sahte Yorum Kontrolü"
      sub="Bot kalıpları taranıyor"
      tone={DARK}
      footer="◇ Bir aynaya basılı tutun ◇"
      illustration={
        <div className="grid w-full max-w-[560px] grid-cols-4 gap-2.5">
          {cards.map((_, i) => {
            if (i === realIndex) {
              return (
                <div
                  key={i}
                  className="relative flex aspect-[3/4] flex-col items-center justify-center overflow-hidden border"
                  style={{ borderColor: "var(--brass)", background: "#15120b" }}
                >
                  <svg viewBox="0 0 60 60" className="h-12 w-12" aria-hidden="true">
                    <path
                      d="M16 50 L30 12 L44 50"
                      fill="none"
                      stroke="var(--brass-hot)"
                      strokeWidth="5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                  <p
                    className="fl-mono mt-2 text-[8px] uppercase tracking-[0.2em]"
                    style={{ color: "var(--brass-hot)" }}
                  >
                    Gerçek
                  </p>
                  <div
                    className="absolute inset-0 -z-0"
                    style={{ background: "radial-gradient(circle at 50% 60%, rgba(217,182,92,0.18), transparent 70%)" }}
                  />
                </div>
              );
            }
            return (
              <div
                key={i}
                className="flex aspect-[3/4] flex-col justify-between border p-2.5"
                style={{ borderColor: "#211f1a", background: "rgba(18,16,12,0.7)" }}
              >
                <p className="fl-sans text-[8px] italic leading-snug" style={{ color: "var(--ink-50)" }}>
                  &quot;Mükemmel ürün, herkese tavsiye ederim.&quot;
                </p>
                <p className="fl-mono text-[7px]" style={{ color: "#332f28" }}>
                  RVW_{String(1200 + i * 37).slice(-4)}
                </p>
              </div>
            );
          })}
        </div>
      }
      text={
        <TextBlock
          tone={DARK}
          kicker="Bot Kalıbı Tespit Edildi"
          adim="3. adım:"
          title="Sahteleri yakalıyoruz."
          body="Bot hesaplar genellikle aynı cümleyi farklı şekillerde yazar. Bu kalıpları tespit ediyor, gerçek yorumları sahtelerinden ayırıyoruz. Gerçek satın alma kalıbı böyle görünür."
          stat="%34"
          statSub="Sahte Yorum Uyarısı · 2.726 Gerçek Yorum"
        />
      }
    />
  );
}

/* ════════════════════════════════════════════════════════════
   04 — İADE RİSKİ
   ════════════════════════════════════════════════════════════ */
function StepFour() {
  return (
    <Section
      index={4}
      evre="İade Riski"
      sub="İade sinyalleri taranıyor"
      tone={DARK}
      footer="— Paketler müşteriye doğru ilerliyor —"
      illustration={
        <div
          className="relative h-[360px] w-full max-w-[560px]"
          style={{ perspective: "900px" }}
        >
          <div
            className="absolute inset-x-0 top-1/2 grid grid-cols-4 gap-6"
            style={{ transform: "rotateX(56deg)", transformOrigin: "center" }}
          >
            {Array.from({ length: 8 }).map((_, i) => (
              <div
                key={i}
                className="relative aspect-square"
                style={{
                  background: "linear-gradient(135deg,#c79a52,#8a6533)",
                  border: "1px solid #6e4f27",
                }}
              >
                <div
                  className="absolute left-1/2 top-0 h-full w-px -translate-x-1/2"
                  style={{ background: "#6e4f27" }}
                />
                <div
                  className="absolute left-0 top-1/2 h-px w-full -translate-y-1/2"
                  style={{ background: "#6e4f27" }}
                />
                {i === 3 && (
                  <div
                    className="absolute left-1/2 top-1/2 h-6 w-9 -translate-x-1/2 -translate-y-1/2"
                    style={{ background: "#f4efe2", border: "1px solid #cdbf9a" }}
                  />
                )}
              </div>
            ))}
          </div>
          <div
            className="pointer-events-none absolute inset-0"
            style={{ background: "linear-gradient(180deg,transparent 30%,#0a0908 95%)" }}
          />
        </div>
      }
      text={
        <TextBlock
          tone={DARK}
          kicker="İade Tahmini"
          adim="4. adım:"
          title="İade riskini ölçüyoruz."
          body="Bu ürünün kaç müşteri tarafından iade edildiğini ve neden iade edildiğini hesaplıyoruz. Düşük risk paket müşteriye ulaşır demektir; yüksek risk kategori ortalamasının üzerindedir."
          stat="%21"
          statSub="İade Oranı · Kategori Ortalaması %14"
        />
      }
    />
  );
}

/* ════════════════════════════════════════════════════════════
   05 — FİYAT KARŞILAŞTIRMASI
   ════════════════════════════════════════════════════════════ */
function StepFive() {
  return (
    <Section
      index={5}
      evre="Fiyat Karşılaştırması"
      sub="Fiyatlar alternatifle sınanıyor"
      tone={TAN}
      footer="— Alternatiflerin üzerine gelin —"
      illustration={
        <div className="relative h-[420px] w-full max-w-[520px]">
          {/* Dikey direk */}
          <div
            className="absolute bottom-0 left-1/2 w-[10px] -translate-x-1/2"
            style={{ height: "92%", background: "linear-gradient(90deg,#8a6533,#e0c477,#8a6533)" }}
          />
          {/* Tepe topuzu */}
          <div
            className="absolute left-1/2 top-[4%] h-4 w-12 -translate-x-1/2 rounded-full"
            style={{ background: "linear-gradient(90deg,#8a6533,#e0c477,#8a6533)" }}
          />
          {/* Eğik kol */}
          <div
            className="absolute left-1/2 top-[24%] h-[8px] w-[400px] -translate-x-1/2"
            style={{
              background: "linear-gradient(90deg,#8a6533,#e0c477,#8a6533)",
              transform: "rotate(-9deg)",
            }}
          />
          {/* Sol kefe — daha ağır (alçak) */}
          <div className="absolute left-[6%] top-[44%] flex flex-col items-center">
            <div className="h-12 w-px" style={{ background: "#8a6533" }} />
            <div
              className="flex h-14 w-24 flex-col items-center justify-center border"
              style={{ background: "#caa258", borderColor: "#7a5a2c" }}
            >
              <span className="fl-serif text-[20px]" style={{ color: "#3a2c12" }}>
                ₺
              </span>
            </div>
            <p className="fl-mono mt-2 text-[8px] uppercase tracking-[0.12em]" style={{ color: "#6a5836" }}>
              Stellar X2
            </p>
            <p className="fl-serif text-[15px]" style={{ color: "#3a3120" }}>
              2.847 ₺
            </p>
          </div>
          {/* Sağ kefe — daha hafif (yüksek) */}
          <div className="absolute right-[4%] top-[20%] flex flex-col items-center">
            <div className="h-10 w-px" style={{ background: "#8a6533" }} />
            <div
              className="flex h-12 w-28 items-center justify-center gap-1.5 border"
              style={{ background: "#e6dcc2", borderColor: "#bda979" }}
            >
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="h-6 w-4" style={{ background: "#6f6655" }} />
              ))}
            </div>
            <p className="fl-mono mt-2 text-[8px] uppercase tracking-[0.12em]" style={{ color: "#6a5836" }}>
              Alternatifler
            </p>
            <p className="fl-serif text-[15px]" style={{ color: "#3a3120" }}>
              2.399 – 3.099 ₺
            </p>
          </div>
        </div>
      }
      text={
        <TextBlock
          tone={TAN}
          kicker="Pazar Karşılaştırması"
          adim="5. adım:"
          title="Fiyatı karşılaştırıyoruz."
          body="Sol kefede sizin seçtiğiniz ürün, sağ kefede pazardaki dört alternatif. Eğim, fiyat farkını gösterir. Bir alternatifin üzerine gelin: adı, fiyatı ve linki anında karşınıza çıkar."
          stat="+%14"
          statSub="Pazar Ortalamasının %14 Üzerinde"
        />
      }
    />
  );
}

/* ════════════════════════════════════════════════════════════
   06 — NİHAİ KARAR
   ════════════════════════════════════════════════════════════ */
function StepSix() {
  const doors = [
    { name: "Alınabilir", tag: "Alınabilir", color: "var(--verdict-buy)", active: false },
    { name: "Dikkatli incele", tag: "Dikkatli İncele", color: "var(--brass)", active: true },
    { name: "Bekle", tag: "Bekle", color: "var(--verdict-wait)", active: false },
  ];
  return (
    <Section
      index={6}
      evre="Nihai Karar"
      sub="Tüm sinyaller birleşiyor"
      tone={DARK}
      footer="— Kapalı bir kapıya dokunun —"
      illustration={
        <div className="flex items-end justify-center gap-5">
          {doors.map((d) => (
            <div
              key={d.name}
              className="relative flex w-[150px] flex-col items-center justify-end overflow-hidden p-5 text-center"
              style={{
                height: d.active ? 440 : 392,
                borderRadius: "75px 75px 3px 3px",
                border: `1px solid ${d.active ? d.color : "#2a2823"}`,
                background: d.active
                  ? "linear-gradient(180deg,#3a2c12 0%,#caa05a 55%,#8a6533 100%)"
                  : `linear-gradient(180deg,#15140f 0%,${d.color}22 120%)`,
              }}
            >
              {d.active && (
                <p
                  className="absolute left-5 right-5 top-[26%] fl-serif text-[12px] italic leading-snug"
                  style={{ color: "#2a2008" }}
                >
                  Almadan önce iki yorum daha okuyorsun. Boya soyulması ihtimali için renk seçimini
                  yeniden düşünüyorsun.
                </p>
              )}
              <p
                className="fl-serif italic text-[20px]"
                style={{ color: d.active ? "#2a2008" : d.color }}
              >
                {d.name}
              </p>
              <p
                className="fl-mono mt-1 text-[8px] uppercase tracking-[0.18em]"
                style={{ color: d.active ? "#5a4318" : "var(--ink-50)" }}
              >
                {d.tag}
              </p>
            </div>
          ))}
        </div>
      }
      text={
        <div className="w-full max-w-[340px] shrink-0">
          <p className="fl-mono text-[9px] uppercase tracking-[0.16em]" style={{ color: DARK.dim }}>
            Sizin İçin Seçtiğimiz Tek Seçenek
          </p>
          <p className="fl-serif italic mt-5 text-[26px]" style={{ color: "var(--brass)" }}>
            6. adım:
          </p>
          <h2 className="fl-serif text-[44px] leading-[1.04]" style={{ color: DARK.text }}>
            Kararla biten yol.
          </h2>
          <p className="fl-sans mt-5 text-[13px] leading-relaxed" style={{ color: DARK.dim }}>
            Tüm verileri birleştirip size tek bir cevap veriyoruz: alınabilir, dikkatli inceleyin ya
            da bekleyin. Kapalı bir kapıya dokunun, neden o seçeneği önermediğimizi görün.
          </p>
          <p className="fl-serif mt-8 text-[34px] uppercase leading-none" style={{ color: "var(--brass)" }}>
            Dikkatli İncele
          </p>
          <div className="mt-4 flex items-center gap-3">
            <span className="fl-pill" style={{ color: "var(--verdict-caution)" }}>
              Orta Güven
            </span>
            <span className="fl-mono text-[9px] uppercase tracking-[0.14em]" style={{ color: DARK.dim }}>
              Güven %68
            </span>
          </div>
        </div>
      }
    />
  );
}

/* ── Dışa aktarım ─────────────────────────────────────────── */
export function ProcessJourney() {
  return (
    <>
      <StepOne />
      <StepTwo />
      <StepThree />
      <StepFour />
      <StepFive />
      <StepSix />
    </>
  );
}
