def generate_explanations(category: str, scores: dict):
    fake_risk = scores.get("fakeReviewRisk", 30)
    return_risk = scores.get("returnRisk", scores.get("returnProbability", "Orta"))
    trust_score = scores.get("trustScore", 50)
    final_decision = scores.get("finalDecision", "BEKLE")

    # Fake review explanation — deterministic based on risk level
    if fake_risk > 60:
        fake_explanation = "Yorumların bir kısmı benzer saatlerde yapılmış, bot aktivitesi şüphesi var. Çok yüksek puanlara rağmen değerlendirme sayısı düşük."
    elif fake_risk > 35:
        fake_explanation = "Aşırı övgü dolu ve kalıplaşmış kelimelerin kullanıldığı yorumlar tespit edildi. Dikkatli inceleme önerilir."
    else:
        fake_explanation = "Doğrulanmış alıcıların yaptığı uzun ve mantıklı değerlendirmeler ağırlıkta. Sahte yorum riski düşük."

    # Return reason explanation — deterministic based on return risk level
    if return_risk == "Yüksek":
        return_explanation = "Kullanıcılar ürünü genellikle beklentilerini karşılamadığı için iade etmiş. Üretim hataları da raporlanmış."
    elif return_risk == "Orta":
        return_explanation = "Kullanıcıların bir kısmı ürün açıklamasıyla gerçek ürün arasında farklılık bildirmiş."
    else:
        return_explanation = "Satıcı güvenilir ve kargo süreci hızlı olduğu için iade oranları çok düşük."

    # Psychology warning — deterministic based on trust score
    if trust_score > 75:
        psychology_warning = "Bu ürün bütçe planlamanıza ve ihtiyaçlarınıza uygun, rasyonel bir karar gibi görünüyor."
    elif trust_score > 50:
        psychology_warning = "Bu satın alma kararı indirim baskısıyla verilmiş olabilir. 24 saat beklemek mantıklı olabilir."
    else:
        psychology_warning = "Sosyal medya trendlerinden etkilenmiş olabilirsiniz. Benzer alternatiflere göz atmanız önerilir."

    # Category-specific analysis
    category_lower = (category or "").lower()

    if "kozmetik" in category_lower or "cilt" in category_lower:
        category_analysis = "Kozmetik analizi: Ürünün aktif içerik yapısı ve formülasyonu genel olarak cilt tipleriyle uyumlu. Ancak hassas ciltli kullanıcılar adaptasyon sürecinde hafif reaksiyonlar raporlamış. Etkili sonuçlar için düzenli kullanım şarttır."
    elif "elektronik" in category_lower or "kulaklık" in category_lower:
        category_analysis = "Pil ömrü vaat edilen sürelere yakın, ancak bazı cihazlarda Bluetooth bağlantı kopmaları rapor edilmiş. Ses kalitesi bas ağırlıklı olarak övülüyor."
    elif "laptop" in category_lower or "bilgisayar" in category_lower:
        category_analysis = "İşlemci ve grafik kartı performansı yüksek olsa da yük altında aşırı ısınma ve kısa batarya ömrü şikayetleri dikkat çekiyor."
    elif "telefon" in category_lower:
        category_analysis = "Kamera yetenekleri ve ekran kalitesi çok iyi bulunmuş. Fakat bazı yorumlarda yazılım güncellemeleri sonrası yavaşlama belirtilmiş."
    elif "giyim" in category_lower or "ayakkabı" in category_lower:
        category_analysis = "Taban kalitesi ve rahatlığı genel olarak çok iyi. Ancak kalıbı biraz dar, kullanıcıların çoğu bir beden büyük almayı tavsiye ediyor."
    elif "çanta" in category_lower or "aksesuar" in category_lower:
        category_analysis = "Kullanılan dikiş ve materyal kalitesi başarılı. Ancak fermuar kısımlarında uzun vadede takılmalar olduğuna dair bazı uyarılar var."
    elif "saat" in category_lower:
        category_analysis = "Sağlık sensörlerinin doğruluğu beğenilmiş, ancak arayüzde bazen yavaşlamalar oluyor ve pilin 2 gün zor dayandığı belirtiliyor."
    elif "kahve" in category_lower:
        category_analysis = "Demleme kalitesi ve süt köpürtücü fonksiyonu çok başarılı. Fakat makinenin temizlik uyarısı çok sık verdiği için kullanımı zorlaştırdığı söyleniyor."
    else:
        category_analysis = "Bu ürünün genel özellikleri ve kullanıcı deneyimi incelendiğinde ortalama düzeyde memnuniyet görülüyor."

    # Append decision context
    if final_decision == "ALINABİLİR":
        category_analysis += " Genel değerlendirme olumlu, güvenle satın alınabilir."
    elif final_decision == "ÖNERİLMEZ":
        category_analysis += " " + fake_explanation
    else:
        category_analysis += " Alternatifleri değerlendirdikten sonra karar vermeniz önerilir."

    return {
        "fakeReviewExplanation": fake_explanation,
        "returnReasonExplanation": return_explanation,
        "psychologyWarning": psychology_warning,
        "decisionReason": category_analysis
    }
