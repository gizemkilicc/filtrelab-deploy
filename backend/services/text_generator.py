def generate_explanations(category: str, scores: dict):
    fake_risk = scores.get("fakeReviewRisk", 30)
    return_risk = scores.get("returnRisk", scores.get("returnProbability", "Orta"))
    trust_score = scores.get("trustScore", 50)
    final_decision = scores.get("finalDecision", "BEKLE")

    # ── Fake review explanation (1 sentence) ──────────────────────────────────
    if fake_risk > 60:
        fake_explanation = "Yorumların önemli bir kısmı bot aktivitesine işaret ediyor; dikkatli olunması önerilir."
    elif fake_risk > 35:
        fake_explanation = "Bazı yorumlar kalıplaşmış ifadeler içeriyor; satın almadan önce eleştirel yorumları da okuyun."
    else:
        fake_explanation = "Yorumlar büyük ölçüde gerçek alıcılara ait; sahte yorum riski düşük."

    # ── Return risk explanation (1 sentence) ─────────────────────────────────
    if return_risk == "Yüksek":
        return_explanation = "Ürün açıklamasıyla gerçek ürün arasında farklılık bildirimi fazla; iade riski yüksek."
    elif return_risk == "Orta":
        return_explanation = "Bazı kullanıcılar beklentiyle uyumsuzluk yaşamış; ürün özelliklerini dikkatlice kontrol edin."
    else:
        return_explanation = "İade oranı düşük; satıcı ve ürün güvenilir görünüyor."

    # ── Psychology warning (1 sentence) ──────────────────────────────────────
    if trust_score > 75:
        psychology_warning = "Bu ürün ihtiyacınıza ve bütçenize uygun rasyonel bir seçim."
    elif trust_score > 50:
        psychology_warning = "Satın alma kararı vermeden önce 24 saat bekleyin ve alternatiflere göz atın."
    else:
        psychology_warning = "Düşük güven skoru; benzer ürünleri karşılaştırmadan satın almayın."

    # ── Category-specific analysis (2-3 short sentences) ─────────────────────
    cat = (category or "").lower()

    if "kozmetik" in cat or "cilt" in cat or "güzellik" in cat or "parfüm" in cat:
        analysis = (
            "Ürün cilt bakım kategorisinde değerlendirildi. "
            "Cilt tipi ve içerik uyumluluğunu kontrol ederek, hassas ciltler için önce küçük miktarda test etmeniz önerilir."
        )
    elif "telefon" in cat or "akıllı" in cat or "smartphone" in cat:
        analysis = (
            "Ürün akıllı telefon kategorisinde değerlendirildi. "
            "Kamera, batarya ömrü ve yazılım güncellemelerini karşılaştırarak karar verin."
        )
    elif "laptop" in cat or "bilgisayar" in cat or "notebook" in cat:
        analysis = (
            "Ürün bilgisayar kategorisinde değerlendirildi. "
            "İşlemci, RAM ve ekran kalitesini kullanım amacınıza göre değerlendirin."
        )
    elif "elektronik" in cat or "kulaklık" in cat or "hoparlör" in cat:
        analysis = (
            "Ürün elektronik kategorisinde değerlendirildi. "
            "Ses kalitesi, bağlantı stabilitesi ve garanti koşullarını göz önünde bulundurun."
        )
    elif "aydinlatma" in cat or "lamba" in cat or "led" in cat or "aydınlatma" in cat:
        analysis = (
            "Ürün dış mekan aydınlatma kategorisinde değerlendirildi. "
            "Işık gücü, şarj süresi ve su geçirmezlik derecesi satın alma kararında belirleyicidir."
        )
    elif "bahçe" in cat or "yapı market" in cat:
        analysis = (
            "Ürün bahçe ve yapı market kategorisinde değerlendirildi. "
            "Malzeme dayanıklılığı ve montaj kolaylığı bu kategoride öncelikli kriterlerdir."
        )
    elif "ev" in cat or "yaşam" in cat or "mutfak" in cat or "dekorasyon" in cat:
        analysis = (
            "Ürün ev ve yaşam kategorisinde değerlendirildi. "
            "Tasarım, malzeme kalitesi ve günlük kullanım pratiği ön plana çıkıyor."
        )
    elif "giyim" in cat or "t-shirt" in cat or "pantolon" in cat or "elbise" in cat or "sweatshirt" in cat:
        analysis = (
            "Ürün giyim kategorisinde değerlendirildi. "
            "Beden uyumu, kumaş kalitesi ve kullanıcı yorumlarını dikkate alarak karar verin."
        )
    elif "ayakkabı" in cat or "bot" in cat or "sandalet" in cat:
        analysis = (
            "Ürün ayakkabı kategorisinde değerlendirildi. "
            "Taban kalitesi ve beden uyumu için kullanıcı yorumlarına bakmanız önerilir."
        )
    elif "çanta" in cat or "cüzdan" in cat or "sırt çantası" in cat:
        analysis = (
            "Ürün çanta ve aksesuar kategorisinde değerlendirildi. "
            "Malzeme kalitesi ve fermuar dayanıklılığı uzun vadeli memnuniyet için kritiktir."
        )
    elif "saat" in cat or "aksesuar" in cat:
        analysis = (
            "Ürün saat ve aksesuar kategorisinde değerlendirildi. "
            "Pil ömrü, su geçirmezlik ve ekran kalitesi öne çıkan değerlendirme kriterleridir."
        )
    elif "spor" in cat or "outdoor" in cat or "fitness" in cat:
        analysis = (
            "Ürün spor ve outdoor kategorisinde değerlendirildi. "
            "Malzeme dayanıklılığı ve beden uyumu bu kategoride en çok şikayet edilen konulardır."
        )
    elif "süpermarket" in cat or "gıda" in cat or "içecek" in cat:
        analysis = (
            "Ürün süpermarket kategorisinde değerlendirildi. "
            "İçerik listesi, tazelik ve fiyat-miktar dengesi değerlendirilmelidir."
        )
    elif "anne" in cat or "çocuk" in cat or "bebek" in cat or "oyuncak" in cat:
        analysis = (
            "Ürün anne ve çocuk kategorisinde değerlendirildi. "
            "Güvenlik sertifikaları ve malzeme güvenilirliği bu kategoride birincil önceliktir."
        )
    elif "otomotiv" in cat or "araç" in cat or "oto" in cat:
        analysis = (
            "Ürün otomotiv kategorisinde değerlendirildi. "
            "Araç uyumluluğu ve montaj kolaylığı satın alma öncesi doğrulanmalıdır."
        )
    elif "kitap" in cat or "hobi" in cat or "sanat" in cat or "müzik" in cat:
        analysis = (
            "Ürün kitap ve hobi kategorisinde değerlendirildi. "
            "İçerik kalitesi ve teslimat süreci bu kategoride öne çıkan değerlendirme kriterleridir."
        )
    elif "kahve" in cat or "çay" in cat or "küçük ev aletleri" in cat:
        analysis = (
            "Ürün küçük ev aletleri kategorisinde değerlendirildi. "
            "Demleme kalitesi, temizlik kolaylığı ve gürültü seviyesi öne çıkan kriterlerdir."
        )
    else:
        analysis = (
            "Ürün genel alışveriş kriterlerine göre analiz edildi. "
            "Fiyat, kullanıcı yorumu ve iade riski birlikte değerlendirilmelidir."
        )

    # ── Append 1-sentence decision context ───────────────────────────────────
    if final_decision == "ALINABİLİR":
        analysis += " Genel skorlar olumlu; güvenle satın alınabilir."
    elif final_decision == "ÖNERİLMEZ":
        analysis += f" {fake_explanation}"
    else:
        analysis += " Alternatifleri karşılaştırdıktan sonra karar vermeniz önerilir."

    return {
        "fakeReviewExplanation": fake_explanation,
        "returnReasonExplanation": return_explanation,
        "psychologyWarning": psychology_warning,
        "decisionReason": analysis,
    }
