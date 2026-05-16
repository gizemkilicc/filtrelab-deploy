export type AIAnalysisResult = {
  productName: string;
  price: string;
  image: string;
  fakeReviewRisk: number; // 0 to 100
  trustScore: number; // 0 to 100
  returnProbability: "Düşük" | "Orta" | "Yüksek";
  sentimentScore: number; // 0 to 10
  pricePerformanceScore: number; // 0 to 10
  psychologyWarning: string;
  finalDecision: "ALINABİLİR" | "BEKLE" | "ÖNERİLMEZ";
  decisionReason: string;
  fakeReviewExplanation: string;
  returnReasonExplanation: string;
  betterAlternatives: {
    name: string;
    price: string;
    image: string;
    reason: string;
  }[];
};

const normalizeText = (text: string) => {
  return text
    .toLowerCase()
    .replace(/ı/g, 'i')
    .replace(/ö/g, 'o')
    .replace(/ü/g, 'u')
    .replace(/ş/g, 's')
    .replace(/ğ/g, 'g')
    .replace(/ç/g, 'c')
    .replace(/[^a-z0-9-]/g, '-');
};

const getRandomNumber = (min: number, max: number) => {
  return Math.floor(Math.random() * (max - min + 1)) + min;
};

const getRandomFloat = (min: number, max: number) => {
  return parseFloat((Math.random() * (max - min) + min).toFixed(1));
};

const formatPrice = (price: number) => {
  return new Intl.NumberFormat('tr-TR').format(price) + " TL";
};

const categoryKeywords = {
  kozmetik: ["serum", "tonik", "toner", "skincare", "beauty", "makeup", "kozmetik", "cilt", "bakim", "bakım", "glikolik", "asit", "nemlendirici", "krem", "gunes", "güneş", "spf", "makyaj", "purest", "hyaluronic", "niacinamide"],
  elektronik: ["headphone", "earbud", "kulaklik", "kulaklık", "airpods", "bluetooth", "headset"],
  laptop: ["laptop", "notebook", "macbook", "thinkpad", "gaming-laptop"],
  telefon: ["iphone", "samsung", "telefon", "phone", "xiaomi"],
  ayakkabi: ["sneaker", "shoes", "ayakkabi", "ayakkabı", "nike", "adidas", "puma"],
  canta: ["bag", "canta", "çanta", "backpack"],
  saat: ["watch", "saat", "smartwatch"],
  kahve: ["coffee", "kahve", "espresso", "latte", "machine"]
};

const generateDynamicData = (category: string): AIAnalysisResult => {
  const trustScore = getRandomNumber(20, 95);
  const fakeReviewRisk = getRandomNumber(5, 80);
  const sentimentScore = getRandomFloat(3.0, 9.8);
  const pricePerformanceScore = getRandomFloat(3.0, 9.5);
  
  let returnProbability: "Düşük" | "Orta" | "Yüksek" = "Orta";
  if (trustScore > 75 && fakeReviewRisk < 30) returnProbability = "Düşük";
  else if (trustScore < 45 || fakeReviewRisk > 60) returnProbability = "Yüksek";

  let finalDecision: "ALINABİLİR" | "BEKLE" | "ÖNERİLMEZ" = "BEKLE";
  if (trustScore > 75 && returnProbability === "Düşük") {
    finalDecision = "ALINABİLİR";
  } else if (trustScore < 45 || fakeReviewRisk > 60 || returnProbability === "Yüksek") {
    finalDecision = "ÖNERİLMEZ";
  }

  const fakeExplanations = [
    "Yorumların bir kısmı benzer saatlerde yapılmış, bot aktivitesi şüphesi var.",
    "Genel kullanıcı yorumları gerçekçi ve detaylı görünüyor, sahte yorum riski oldukça düşük.",
    "Aşırı övgü dolu ve kalıplaşmış kelimelerin kullanıldığı yorumlar tespit edildi.",
    "Doğrulanmış alıcıların yaptığı uzun ve mantıklı değerlendirmeler ağırlıkta."
  ];

  const returnExplanations = [
    "Kullanıcılar ürünü genellikle beklentilerini karşılamadığı için iade etmiş.",
    "Üretim hataları veya kargo hasarları dışında iade talebi neredeyse yok.",
    "Kullanım zorluğu ve ürün defoları sebebiyle yüksek oranda iade ediliyor.",
    "Satıcı güvenilir ve kargo süreci hızlı olduğu için iade oranları çok düşük."
  ];

  const psychologyWarnings = [
    "Bu satın alma kararı indirim baskısıyla verilmiş olabilir. 24 saat beklemek mantıklı olabilir.",
    "Kısıtlı stok / zaman uyarısı sebebiyle dürtüsel bir satın alma eğilimi gösteriyorsunuz.",
    "Bu ürün bütçe planlamanıza ve ihtiyaçlarınıza uygun, rasyonel bir karar gibi görünüyor.",
    "Sosyal medya trendlerinden etkilenmiş olabilirsiniz, benzer alternatiflere göz atın."
  ];

  let productName = "Genel Ürün Analizi";
  let image = "/images/bg-navy.png";
  let price = formatPrice(getRandomNumber(100, 1000));
  let categoryAnalysis = "Bu ürünün detaylı içerik kalitesi ve genel özellikleri ortalama düzeyde değerlendirildi.";

  if (category === "kozmetik") {
    productName = "Cilt Bakım / Kozmetik Ürünü";
    image = "/images/crystal-bg.png";
    price = formatPrice(getRandomNumber(199, 899));
    categoryAnalysis = "Ürün içeriğindeki aktif bileşenler genel olarak iyi. Ancak hassas ciltli kullanıcılar kızarıklık şikayetinde bulunmuş. Kullanıcı memnuniyeti genel olarak dengeli.";
  } else if (category === "elektronik") {
    productName = "Kablosuz Kulaklık / Ses Cihazı";
    image = "/images/navy_spheres.png";
    price = formatPrice(getRandomNumber(999, 8999));
    categoryAnalysis = "Pil ömrü vaat edilen sürelere yakın, ancak bazı cihazlarda Bluetooth bağlantı kopmaları rapor edilmiş. Ses kalitesi bas ağırlıklı olarak övülüyor.";
  } else if (category === "laptop") {
    productName = "Performans Odaklı Dizüstü Bilgisayar";
    image = "/images/ui-cards.png";
    price = formatPrice(getRandomNumber(15000, 60000));
    categoryAnalysis = "İşlemci ve grafik kartı performansı yüksek olsa da yük altında aşırı ısınma ve kısa batarya ömrü şikayetleri dikkat çekiyor.";
  } else if (category === "telefon") {
    productName = "Yeni Nesil Akıllı Telefon";
    image = "/images/bg-orbs.png";
    price = formatPrice(getRandomNumber(15000, 80000));
    categoryAnalysis = "Kamera yetenekleri ve ekran kalitesi çok iyi bulunmuş. Fakat bazı yorumlarda yazılım güncellemeleri sonrası yavaşlama belirtilmiş.";
  } else if (category === "ayakkabi") {
    productName = "Ergonomik Spor Ayakkabı";
    image = "/images/navy_spheres.png";
    price = formatPrice(getRandomNumber(1500, 8000));
    categoryAnalysis = "Taban kalitesi ve rahatlığı genel olarak çok iyi. Ancak kalıbı biraz dar, kullanıcıların çoğu bir beden büyük almayı tavsiye ediyor.";
  } else if (category === "canta") {
    productName = "Tasarım Kadın / Sırt Çantası";
    image = "/images/crystal-bg.png";
    price = formatPrice(getRandomNumber(500, 5000));
    categoryAnalysis = "Kullanılan dikiş ve materyal kalitesi başarılı. Ancak fermuar kısımlarında uzun vadede takılmalar olduğuna dair bazı uyarılar var.";
  } else if (category === "saat") {
    productName = "Gelişmiş Akıllı Saat";
    image = "/images/ui-cards.png";
    price = formatPrice(getRandomNumber(2000, 15000));
    categoryAnalysis = "Sağlık sensörlerinin doğruluğu beğenilmiş, ancak arayüzde bazen yavaşlamalar oluyor ve pilin 2 gün zor dayandığı belirtiliyor.";
  } else if (category === "kahve") {
    productName = "Otomatik Kahve Makinesi";
    image = "/images/bg-navy.png";
    price = formatPrice(getRandomNumber(4000, 25000));
    categoryAnalysis = "Demleme kalitesi ve süt köpürtücü fonksiyonu çok başarılı. Fakat makinenin temizlik uyarısı çok sık verdiği için kullanımı zorlaştırdığı söyleniyor.";
  }

  let betterAlternatives: AIAnalysisResult["betterAlternatives"] = [];
  if (finalDecision !== "ALINABİLİR") {
    betterAlternatives = [
      {
        name: "Daha Yüksek Puanlı Alternatif",
        price: formatPrice(getRandomNumber(Math.floor(parseInt(price.replace(/[^0-9]/g, '')) * 0.8), parseInt(price.replace(/[^0-9]/g, '')))),
        image: image, // same placeholder category image
        reason: "Kanıtlanmış kalite, gerçek kullanıcı yorumları ve garantili satış."
      }
    ];
  }

  return {
    productName,
    price,
    image,
    fakeReviewRisk,
    trustScore,
    returnProbability,
    sentimentScore,
    pricePerformanceScore,
    psychologyWarning: psychologyWarnings[Math.floor(Math.random() * psychologyWarnings.length)],
    finalDecision,
    decisionReason: categoryAnalysis,
    fakeReviewExplanation: fakeExplanations[fakeReviewRisk > 50 ? (Math.random() > 0.5 ? 0 : 2) : (Math.random() > 0.5 ? 1 : 3)],
    returnReasonExplanation: returnExplanations[returnProbability === "Yüksek" ? (Math.random() > 0.5 ? 0 : 2) : (Math.random() > 0.5 ? 1 : 3)],
    betterAlternatives
  };
};

export const simulateAIAnalysis = async (url: string, onProgress: (step: number, message: string) => void): Promise<AIAnalysisResult> => {
  const steps = [
    { message: "Ürün linki inceleniyor...", time: 1000 },
    { message: "Yorumlar analiz ediliyor...", time: 1500 },
    { message: "Sahte yorum kalıpları aranıyor...", time: 1200 },
    { message: "İade riski hesaplanıyor...", time: 1800 },
    { message: "Alternatif ürünler karşılaştırılıyor...", time: 1500 },
    { message: "Nihai karar oluşturuluyor...", time: 1000 }
  ];

  for (let i = 0; i < steps.length; i++) {
    onProgress(i, steps[i].message);
    await new Promise(resolve => setTimeout(resolve, steps[i].time));
  }
  
  onProgress(steps.length, "Analiz Tamamlandı");

  const normalizedUrl = normalizeText(url);
  
  let detectedCategory = "genel";
  for (const [category, keywords] of Object.entries(categoryKeywords)) {
    if (keywords.some(kw => normalizedUrl.includes(kw))) {
      detectedCategory = category;
      break;
    }
  }

  return generateDynamicData(detectedCategory);
};
