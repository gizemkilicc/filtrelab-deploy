import random

def generate_explanations(category: str, scores: dict):
    fake_explanations = [
        "Yorumların bir kısmı benzer saatlerde yapılmış, bot aktivitesi şüphesi var.",
        "Genel kullanıcı yorumları gerçekçi ve detaylı görünüyor, sahte yorum riski oldukça düşük.",
        "Aşırı övgü dolu ve kalıplaşmış kelimelerin kullanıldığı yorumlar tespit edildi.",
        "Doğrulanmış alıcıların yaptığı uzun ve mantıklı değerlendirmeler ağırlıkta."
    ]

    return_explanations = [
        "Kullanıcılar ürünü genellikle beklentilerini karşılamadığı için iade etmiş.",
        "Üretim hataları veya kargo hasarları dışında iade talebi neredeyse yok.",
        "Kullanım zorluğu ve ürün defoları sebebiyle yüksek oranda iade ediliyor.",
        "Satıcı güvenilir ve kargo süreci hızlı olduğu için iade oranları çok düşük."
    ]

    psychology_warnings = [
        "Bu satın alma kararı indirim baskısıyla verilmiş olabilir. 24 saat beklemek mantıklı olabilir.",
        "Kısıtlı stok veya zaman uyarısı sebebiyle dürtüsel bir satın alma eğilimi gösteriyorsunuz.",
        "Bu ürün bütçe planlamanıza ve ihtiyaçlarınıza uygun, rasyonel bir karar gibi görünüyor.",
        "Sosyal medya trendlerinden etkilenmiş olabilirsiniz, benzer alternatiflere göz atın."
    ]

    if scores["fakeReviewRisk"] > 50:
        fake_explanation = random.choice([fake_explanations[0], fake_explanations[2]])
    else:
        fake_explanation = random.choice([fake_explanations[1], fake_explanations[3]])

    if scores["returnProbability"] == "Yüksek":
        return_explanation = random.choice([return_explanations[0], return_explanations[2]])
    else:
        return_explanation = random.choice([return_explanations[1], return_explanations[3]])

    psychology_warning = random.choice(psychology_warnings)

    category_analysis = "Bu ürünün detaylı içerik kalitesi ve genel özellikleri ortalama düzeyde değerlendirildi."
    
    if category == "kozmetik":
        category_analysis = "Kozmetik analizi: Ürünün aktif içerik yapısı ve formülasyonu genel olarak cilt tipleriyle uyumlu. Ancak hassas ciltli kullanıcılar adaptasyon sürecinde hafif reaksiyonlar (hassasiyet) raporlamış. Etkili sonuçlar için düzenli kullanım şarttır, genel kullanıcı memnuniyeti ve içerik uyumluluğu yüksek seviyede."
    elif category == "elektronik":
        category_analysis = "Pil ömrü vaat edilen sürelere yakın, ancak bazı cihazlarda Bluetooth bağlantı kopmaları rapor edilmiş. Ses kalitesi bas ağırlıklı olarak övülüyor."
    elif category == "laptop":
        category_analysis = "İşlemci ve grafik kartı performansı yüksek olsa da yük altında aşırı ısınma ve kısa batarya ömrü şikayetleri dikkat çekiyor."
    elif category == "telefon":
        category_analysis = "Kamera yetenekleri ve ekran kalitesi çok iyi bulunmuş. Fakat bazı yorumlarda yazılım güncellemeleri sonrası yavaşlama belirtilmiş."
    elif category == "ayakkabi":
        category_analysis = "Taban kalitesi ve rahatlığı genel olarak çok iyi. Ancak kalıbı biraz dar, kullanıcıların çoğu bir beden büyük almayı tavsiye ediyor."
    elif category == "canta":
        category_analysis = "Kullanılan dikiş ve materyal kalitesi başarılı. Ancak fermuar kısımlarında uzun vadede takılmalar olduğuna dair bazı uyarılar var."
    elif category == "saat":
        category_analysis = "Sağlık sensörlerinin doğruluğu beğenilmiş, ancak arayüzde bazen yavaşlamalar oluyor ve pilin 2 gün zor dayandığı belirtiliyor."
    elif category == "kahve":
        category_analysis = "Demleme kalitesi ve süt köpürtücü fonksiyonu çok başarılı. Fakat makinenin temizlik uyarısı çok sık verdiği için kullanımı zorlaştırdığı söyleniyor."

    return {
        "fakeReviewExplanation": fake_explanation,
        "returnReasonExplanation": return_explanation,
        "psychologyWarning": psychology_warning,
        "decisionReason": category_analysis
    }
