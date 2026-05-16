"""
Production-grade category detector.

Strategy
--------
1. Normalise all input text (Turkish chars → ASCII, lowercase, punctuation → space).
2. For every candidate category maintain:
   - positive phrases (substring match adds weight)
   - negative phrases (substring match subtracts weight)
3. Long / specific phrases are weighted higher than single words.
4. Select the category with the highest net score.
5. Require a minimum score of 1 to commit; otherwise → "Genel".
6. Breadcrumb data (from scraped page) gets a bonus multiplier.
"""

import re


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _norm(text: str) -> str:
    """Lowercase + Turkish-to-ASCII + collapse to single spaces."""
    if not text:
        return ""
    t = text.lower()
    tr = str.maketrans({
        "ı": "i", "İ": "i",
        "ö": "o", "Ö": "o",
        "ü": "u", "Ü": "u",
        "ş": "s", "Ş": "s",
        "ğ": "g", "Ğ": "g",
        "ç": "c", "Ç": "c",
        "â": "a", "Â": "a",
        "ê": "e", "Ê": "e",
        "î": "i", "Î": "i",
        "û": "u", "Û": "u",
    })
    t = t.translate(tr)
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return t.strip()


def _score(text: str, rules: list[tuple[str, int]]) -> int:
    """Sum weights of all rules whose phrase appears in text."""
    total = 0
    for phrase, weight in rules:
        if phrase in text:
            total += weight
    return total


# ---------------------------------------------------------------------------
# Category definitions
# Each entry: { "display": str, "pos": [(phrase, weight), ...], "neg": [(phrase, weight), ...] }
# ---------------------------------------------------------------------------

_CATS: dict[str, dict] = {

    # ── Kozmetik ────────────────────────────────────────────────────────────
    "kozmetik": {
        "display": "Kozmetik / Cilt Bakımı",
        "pos": [
            # Very specific — weight 4
            ("glikolik asit",    4), ("hyaluronic",        4),
            ("niacinamide",      4), ("retinol",           4),
            ("retinoid",         4), ("vitamin c serum",   4),
            ("aha bha",          4), ("kolik asit",        4),
            ("salisilik asit",   4), ("azelaic",           4),
            ("peptide",          4), ("ceramide",          4),
            ("cilt bakım",       4), ("yuz serumu",        4),
            ("goz kremi",        4), ("pore",              4),
            ("anti aging",       4), ("anti-aging",        4),
            ("collagen krem",    4), ("misel suyu",        4),
            ("temizleyici jel",  4), ("peeling kremi",     4),
            ("fondoten",         4), ("fondöten",          4),
            ("günes kremi",      4), ("günes koruyucu",    4),
            ("spf 50",           4), ("spf 30",            4),
            ("spf",              3),
            # Specific — weight 3
            ("serum",            3), ("tonik",             3),
            ("toner",            3), ("krem",              3),
            ("peeling",         3), ("makyaj",            3),
            ("ruj",             3), ("maskara",           3),
            ("allık",           3), ("nemlendirici",      3),
            ("losyon",          3), ("göz alti",          3),
            ("cilt",            3), ("deodorant",         3),
            ("parfüm",          3), ("sampuan",           3),
            ("sac kremi",       3), ("sac bakim",         3),
            # Generic — weight 1
            ("kozmetik",        1), ("güzellik",          1),
            ("dermatoloji",     1), ("eczane",            1),
        ],
        "neg": [
            # These phrases make kozmetik very unlikely — weight 5
            ("günes enerjili",  5), ("solar panel",       5),
            ("günes paneli",    5), ("günes lambasi",     5),
            ("bahce lambasi",   5), ("led panel",         5),
            ("projektör",       5), ("avize",             5),
            ("aplik",           5), ("ampul",             5),
            ("sarj cihazi",     5), ("sarj aleti",        5),
            ("matkap",         5), ("tornavida",         5),
            ("hortum",         5), ("sulama",            5),
            ("bahce aydınlatma",5),
            # Strong single — weight 3
            ("laptop",         3), ("notebook",          3),
            ("macbook",        3), ("iphone",            3),
            ("android",        3), ("kulaklık",          3),
            ("ayakkabi",       3), ("sneaker",           3),
            ("matkan",         3), ("vida",              3),
            ("bahce",          3), ("panel",             3),
            ("lamba",          2), ("led",               2),
            ("telefon",        2), ("tablet",            2),
            ("gitar",          2), ("bisiklet",          2),
        ],
    },

    # ── Telefon ─────────────────────────────────────────────────────────────
    "telefon": {
        "display": "Telefon",
        "pos": [
            ("iphone",          5), ("samsung galaxy",   5),
            ("samsung s2",      5), ("samsung a2",       4),
            ("xiaomi",          4), ("oppo",             4),
            ("huawei",          4), ("oneplus",          4),
            ("google pixel",    5), ("realme",           4),
            ("redmi",           4), ("motorola",         4),
            ("akilli telefon",  5), ("cep telefonu",     5),
            ("smartphone",      5), ("snapdragon",       4),
            ("mediatek",        4), ("5g telefon",       5),
            ("telefon",         3), ("phone",            3),
        ],
        "neg": [
            ("telefon kilifi",  4), ("telefon kablosu",  4),
            ("telefon tutucu",  4), ("sarj kablosu",     3),
            ("kulaklık",        2), ("laptop",           3),
            ("kozmetik",        3), ("krem",             3),
        ],
    },

    # ── Bilgisayar / Laptop ─────────────────────────────────────────────────
    "laptop": {
        "display": "Bilgisayar / Laptop",
        "pos": [
            ("macbook",         5), ("thinkpad",         5),
            ("laptop",          5), ("notebook",         5),
            ("gaming laptop",   5), ("gaming notebook",  5),
            ("ultrabook",       5), ("chromebook",       4),
            ("bilgisayar",      4), ("pc",               2),
            ("i7",              3), ("i9",               3),
            ("ryzen",           4), ("m1 chip",          5),
            ("m2 chip",         5), ("m3 chip",          5),
            ("ssd",             2), ("ram gb",           3),
            ("ekran karti",     4),
        ],
        "neg": [
            ("telefon",         3), ("kulaklık",         2),
            ("kozmetik",        3), ("krem",             3),
            ("kilif",           3),
        ],
    },

    # ── Elektronik (kulaklık, hoparlör, ses sistemleri) ─────────────────────
    "elektronik": {
        "display": "Elektronik",
        "pos": [
            ("bluetooth kulaklik",  5), ("kablosuz kulaklik", 5),
            ("true wireless",       5), ("anc kulaklik",      5),
            ("noise cancelling",    5), ("gaming kulaklik",   5),
            ("earbuds",             5), ("headphone",         5),
            ("airpods",             5), ("galaxy buds",       5),
            ("kulaklik",            4), ("hoparlör",          4),
            ("ses sistemi",         4), ("subwoofer",         4),
            ("bluetooth",           3), ("wireless",          3),
            ("headset",             4), ("earbud",            4),
            ("amplifikatör",        4),
        ],
        "neg": [
            ("telefon",         2), ("laptop",           2),
            ("kozmetik",        3), ("krem",             3),
            ("lamba",           3), ("led",              2),
        ],
    },

    # ── Ayakkabı ────────────────────────────────────────────────────────────
    "ayakkabi": {
        "display": "Ayakkabı",
        "pos": [
            ("sneaker",         5), ("spor ayakkabi",    5),
            ("kosu ayakkabisi", 5), ("trekking",         4),
            ("bot",             3), ("çizme",            4),
            ("topuklu",         4), ("sandalet",         4),
            ("terlik",          3), ("loafer",           4),
            ("ayakkabi",        4), ("shoes",            4),
            ("numara",          3), ("taban",            3),
            ("nike",            3), ("adidas",           3),
            ("puma",            3), ("new balance",      4),
            ("converse",        4), ("vans",             3),
            ("skechers",        4),
        ],
        "neg": [
            ("kozmetik",        4), ("krem",             4),
            ("telefon",         4), ("laptop",           4),
            ("lamba",           3),
        ],
    },

    # ── Giyim ───────────────────────────────────────────────────────────────
    "giyim": {
        "display": "Giyim",
        "pos": [
            ("t-shirt",         5), ("tshirt",           5),
            ("gomlek",          5), ("sweatshirt",       5),
            ("hoodıe",          4), ("hoodie",           4),
            ("pantolon",        5), ("etek",             5),
            ("elbise",          5), ("kazak",            5),
            ("mont",            5), ("kaban",            5),
            ("esofman",         5), ("sort",             4),
            ("atlet",           4), ("tisort",           4),
            ("bluz",            4), ("ceket",            4),
            ("beden",           3), ("oversize",         4),
            ("slim fit",        4), ("regular fit",      4),
        ],
        "neg": [
            ("kozmetik",        4), ("krem",             4),
            ("telefon",         4), ("laptop",           4),
            ("lamba",           3), ("ayakkabi",         3),
        ],
    },

    # ── Çanta ───────────────────────────────────────────────────────────────
    "canta": {
        "display": "Çanta",
        "pos": [
            ("sırt cantası",    5), ("omuz cantası",     5),
            ("el cantası",      5), ("laptop cantası",   5),
            ("seyahat cantası", 5), ("backpack",         5),
            ("crossbody",       5), ("clutch",           4),
            ("portföy",         4), ("deri canta",       4),
            ("canta",           4), ("bag",              3),
            ("wallet",          3), ("cuzdan",           4),
        ],
        "neg": [
            ("kozmetik",        4), ("telefon",          4),
            ("laptop",          3), ("lamba",            3),
        ],
    },

    # ── Saat & Aksesuar ─────────────────────────────────────────────────────
    "saat": {
        "display": "Saat & Aksesuar",
        "pos": [
            ("akilli saat",     5), ("smartwatch",       5),
            ("apple watch",     5), ("galaxy watch",     5),
            ("garmin",          4), ("fitbit",           4),
            ("analog saat",     5), ("dijital saat",     5),
            ("kol saati",       5), ("saat",             4),
            ("watch",           4), ("bileklik",         3),
            ("kolye",           3), ("yüzük",            3),
            ("küpe",            3), ("takı",             3),
            ("aksesuar",        2),
        ],
        "neg": [
            ("kozmetik",        4), ("telefon",          4),
            ("laptop",          4), ("lamba",            3),
        ],
    },

    # ── Aydınlatma ──────────────────────────────────────────────────────────
    "aydinlatma": {
        "display": "Aydınlatma",
        "pos": [
            ("led lamba",       5), ("led ampul",        5),
            ("led strip",       5), ("avize",            5),
            ("aplik",           5), ("projektör",        5),
            ("spotluk",         4), ("spot lamba",       5),
            ("gece lambasi",    4), ("bahce lambasi",    5),
            ("bahce aydinlatma",5), ("dis mekan lamba",  5),
            ("solar lamba",     5), ("günes enerjili lamba", 5),
            ("sensörlü lamba",  5), ("hareket sensörlü", 5),
            ("ampul",           4), ("lamba",            4),
            ("aydinlatma",      4), ("isik",             3),
        ],
        "neg": [
            ("kozmetik",        4), ("krem",             4),
            ("telefon",         3), ("laptop",           3),
            ("ayakkabi",        3),
        ],
    },

    # ── Bahçe & Yapı Market ─────────────────────────────────────────────────
    "bahce": {
        "display": "Bahçe & Yapı Market",
        "pos": [
            ("günes enerjili",  5), ("solar panel",      5),
            ("günes paneli",    5), ("bahce",            4),
            ("matkap",          5), ("tornavida",        5),
            ("vida",            4), ("çivi",             4),
            ("hortum",          4), ("sulama",           4),
            ("çim biçme",       5), ("peyzaj",           4),
            ("yapı market",     5), ("inşaat",           4),
            ("boya",            3), ("silikon",          3),
            ("tutkal",          3), ("dübel",            4),
            ("testere",         4), ("levye",            4),
            ("dis mekan",       3), ("bahce süsü",       4),
        ],
        "neg": [
            ("kozmetik",        4), ("krem",             4),
            ("telefon",         3), ("laptop",           3),
            ("lamba",           2),  # lamba tek başına bahçe değil ama negatif sayılmaz aslında
        ],
    },

    # ── Ev & Yaşam ──────────────────────────────────────────────────────────
    "ev": {
        "display": "Ev & Yaşam",
        "pos": [
            ("kahve makinesi",  5), ("espresso makinesi",5),
            ("tost makinesi",   5), ("waffle makinesi",  5),
            ("firin",           4), ("mikrodalga",       4),
            ("buzdolabi",       5), ("camasir makinesi", 5),
            ("bulaşik makinesi",5), ("supürge",          4),
            ("elektrik supürge",5), ("klima",            5),
            ("ev tekstil",      4), ("yatak örtüsü",     4),
            ("nevresim",        4), ("havlu",            3),
            ("tencere",         4), ("tava",             4),
            ("mutfak",          3), ("bıçak seti",       4),
            ("ev aletleri",     4), ("küçük ev aleti",   4),
        ],
        "neg": [
            ("kozmetik",        4), ("telefon",          3),
            ("laptop",          3), ("lamba",            2),
        ],
    },

    # ── Süpermarket ─────────────────────────────────────────────────────────
    "supermarket": {
        "display": "Süpermarket",
        "pos": [
            ("gida",            4), ("atistirma",        4),
            ("çikolata",        4), ("kahve çekirdeği",  4),
            ("bitki çayı",      4), ("protein bar",      5),
            ("vitamin",         4), ("takviye",          4),
            ("organik",         3), ("bitkisel",         3),
            ("deterjan",        4), ("temizlik ürünü",   5),
            ("bebek mamasi",    5),
        ],
        "neg": [
            ("kozmetik",        3), ("telefon",          4),
            ("laptop",          4), ("lamba",            3),
        ],
    },

    # ── Anne & Çocuk ────────────────────────────────────────────────────────
    "anne_cocuk": {
        "display": "Anne & Çocuk",
        "pos": [
            ("bebek bezi",      5), ("bebek",            4),
            ("çocuk",           4), ("emzirme",          5),
            ("mama sandalyesi", 5), ("bebek arabası",    5),
            ("oyuncak",         4), ("lego",             4),
            ("yenidogan",       5), ("bebek ürünü",      5),
            ("anne bebek",      5), ("cocuk",            4),
        ],
        "neg": [
            ("telefon",         3), ("laptop",           3),
            ("lamba",           3),
        ],
    },

    # ── Spor & Outdoor ──────────────────────────────────────────────────────
    "spor": {
        "display": "Spor & Outdoor",
        "pos": [
            ("protein tozu",    5), ("whey protein",     5),
            ("creatine",        5), ("fitness",          4),
            ("dumbbell",        5), ("halter",           5),
            ("yoga matı",       5), ("yoga mat",         5),
            ("bisiklet",        4), ("kampçılık",        4),
            ("çadır",           4), ("uyku tulumu",      4),
            ("outdoor",         4), ("hiking",           4),
            ("kamp",            3), ("trekking",         4),
            ("spor ekipman",    4), ("antrenman",        4),
        ],
        "neg": [
            ("kozmetik",        4), ("lamba",            3),
            ("laptop",          3), ("telefon",          3),
        ],
    },

    # ── Otomotiv ────────────────────────────────────────────────────────────
    "otomotiv": {
        "display": "Otomotiv",
        "pos": [
            ("araç",            4), ("araba",            4),
            ("motor yagi",      5), ("fren balatasi",    5),
            ("lastik",          5), ("jant",             5),
            ("oto aksesuar",    5), ("araç içi",         5),
            ("dashcam",         4), ("oto koku",         4),
            ("araba kılıfı",    4),
        ],
        "neg": [
            ("kozmetik",        4), ("telefon",          3),
            ("laptop",          3),
        ],
    },

    # ── Kitap / Hobi ────────────────────────────────────────────────────────
    "kitap": {
        "display": "Kitap / Hobi",
        "pos": [
            ("roman",           5), ("kitap",            5),
            ("bölüm",           3), ("yazar",            3),
            ("gitar",           5), ("piyano",           5),
            ("enstrüman",       5), ("müzik aleti",      5),
            ("boyama",          4), ("puzzle",           4),
            ("hobi",            3), ("el işi",           4),
        ],
        "neg": [
            ("kozmetik",        4), ("telefon",          3),
            ("laptop",          3),
        ],
    },
}

# Breadcrumb phrases that strongly confirm a category
_BREADCRUMB_HINTS: list[tuple[str, str]] = [
    ("kozmetik",          "kozmetik"),
    ("cilt bakım",        "kozmetik"),
    ("makyaj",            "kozmetik"),
    ("parfümeri",         "kozmetik"),
    ("kisisel bakim",     "kozmetik"),
    ("kulaklik",          "elektronik"),
    ("hoparlör",          "elektronik"),
    ("ses sistemi",       "elektronik"),
    ("cep telefonu",      "telefon"),
    ("akilli telefon",    "telefon"),
    ("laptop",            "laptop"),
    ("notebook",          "laptop"),
    ("bilgisayar",        "laptop"),
    ("ayakkabi",          "ayakkabi"),
    ("spor ayakkabi",     "ayakkabi"),
    ("giyim",             "giyim"),
    ("kadin giyim",       "giyim"),
    ("erkek giyim",       "giyim"),
    ("canta",             "canta"),
    ("saat",              "saat"),
    ("takı",              "saat"),
    ("aksesuar",          "saat"),
    ("led lamba",         "aydinlatma"),
    ("aydinlatma",        "aydinlatma"),
    ("bahce",             "bahce"),
    ("yapi market",       "bahce"),
    ("ev aletleri",       "ev"),
    ("mutfak",            "ev"),
    ("beyaz esya",        "ev"),
    ("bebek",             "anne_cocuk"),
    ("cocuk",             "anne_cocuk"),
    ("oyuncak",           "anne_cocuk"),
    ("spor",              "spor"),
    ("outdoor",           "spor"),
    ("otomotiv",          "otomotiv"),
    ("kitap",             "kitap"),
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_category(
    product_name: str = "",
    slug_keywords: list[str] | None = None,
    breadcrumb: str = "",
    brand: str = "",
    description: str = "",
) -> tuple[str, float]:
    """
    Returns (display_category_name, confidence 0–1).
    """
    # Build combined search text
    parts = [
        product_name,
        " ".join(slug_keywords or []),
        breadcrumb,
        brand,
        description,
    ]
    combined = _norm(" ".join(p for p in parts if p))

    scores: dict[str, int] = {}

    for key, cat in _CATS.items():
        pos = _score(combined, cat["pos"])
        neg = _score(combined, cat["neg"])
        net = pos - neg
        if net > 0:
            scores[key] = net

    # Breadcrumb bonus (+6 for confirmed category key)
    bc_norm = _norm(breadcrumb)
    for hint_phrase, cat_key in _BREADCRUMB_HINTS:
        if hint_phrase in bc_norm and cat_key in _CATS:
            scores[cat_key] = scores.get(cat_key, 0) + 6

    # Debug output
    top = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:4]
    print(
        f"[CATEGORY] name={product_name!r:.60} bc={breadcrumb!r:.40}\n"
        f"           topScores={top}"
    )

    if not scores:
        print("[CATEGORY] → Genel (no match)")
        return "Genel", 0.40

    best_key, best_score = max(scores.items(), key=lambda x: x[1])
    display = _CATS[best_key]["display"]

    # Confidence: normalise loosely to 0–1
    confidence = min(1.0, round(best_score / 12.0, 2))

    print(f"[CATEGORY] → {display}  (score={best_score}, confidence={confidence})")
    return display, confidence
