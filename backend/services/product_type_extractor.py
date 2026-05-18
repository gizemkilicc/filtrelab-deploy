"""
Product type extractor.

Given a product name + category, identifies the specific product type
(e.g. "nemlendirici krem", "solar bahçe lambası", "t-shirt") and returns:
  - canonical type name
  - ordered search queries for finding alternatives on Trendyol
  - required keywords: at least one must appear in a valid alternative
  - forbidden keywords: none may appear in a valid alternative
"""

import re

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _norm(text: str) -> str:
    tr = str.maketrans({
        "ı": "i", "İ": "i", "ö": "o", "Ö": "o",
        "ü": "u", "Ü": "u", "ş": "s", "Ş": "s",
        "ğ": "g", "Ğ": "g", "ç": "c", "Ç": "c",
        "â": "a", "î": "i", "û": "u",
    })
    return text.lower().translate(tr)


def _contains(haystack: str, *phrases: str) -> bool:
    h = _norm(haystack)
    return any(_norm(p) in h for p in phrases)


# ---------------------------------------------------------------------------
# Type definitions
# Each entry:
#   "trigger_words" — if product name contains ANY of these → this type
#   "queries"       — Trendyol search queries, most specific first
#   "required"      — at least one must appear in alternative name (normalised)
#   "forbidden"     — none may appear in alternative name
# ---------------------------------------------------------------------------

_TYPES: list[dict] = [

    # ── Kozmetik / Cilt Bakımı ─────────────────────────────────────────────

    {
        "name": "güneş kremi",
        "trigger": ["güneş kremi", "güneş koruyucu", "sunscreen", "spf 50", "spf 30", "güneş filtresi"],
        "queries": ["güneş kremi spf", "güneş koruyucu krem", "spf krem"],
        "required": ["güneş", "spf", "koruyucu", "sunscreen"],
        "forbidden": ["parfüm", "maskara", "deodorant", "ruj", "lamba", "kıyafet", "ayakkabı", "telefon"],
    },
    {
        "name": "tonik",
        "trigger": ["tonik", "toner"],
        "queries": ["cilt toniği", "tonik yüz bakım", "glikolik tonik", "aha tonik"],
        "required": ["tonik", "toner", "esans", "serum"],
        "forbidden": ["parfüm", "maskara", "deodorant", "ruj", "şampuan", "lamba", "telefon", "kıyafet"],
    },
    {
        "name": "serum",
        "trigger": ["serum", "ampoule", "ampul serum"],
        "queries": ["cilt serumu", "yüz serumu", "vitamin c serum", "hyaluronik asit serum"],
        "required": ["serum", "ampul", "esans"],
        "forbidden": ["parfüm", "maskara", "deodorant", "ruj", "şampuan", "lamba", "telefon"],
    },
    {
        "name": "nemlendirici krem",
        "trigger": [
            "nemlendirici", "moisturizer", "krem", "cream", "bariyer",
            "atoderm", "cerat", "balsam", "balm", "vücut bakım",
            "yüz bakım", "cilt bakım",
        ],
        "queries": ["nemlendirici krem", "kuru cilt kremi", "yüz vücut bakım kremi", "cilt nemlendirici"],
        "required": ["krem", "nemlendirici", "cream", "balsam", "atoderm", "cerave", "avene", "bioderma", "la roche"],
        "forbidden": ["parfüm", "deodorant", "maskara", "ruj", "far", "eyeliner", "oje", "saç boyası", "peeling", "scrub", "selülit", "selulit", "losyon", "lamba", "telefon", "kıyafet", "ayakkabı"],
    },
    {
        "name": "yüz temizleme jeli",
        "trigger": ["temizleme jeli", "temizleyici jel", "micellar", "makyaj temizleyici", "yüz temizleyici"],
        "queries": ["yüz temizleme jeli", "temizleyici köpük", "micellar su"],
        "required": ["temizleme", "temizleyici", "micellar", "köpük", "jel"],
        "forbidden": ["parfüm", "maskara", "ruj", "lamba", "telefon", "kıyafet"],
    },
    {
        "name": "şampuan",
        "trigger": ["şampuan", "shampoo", "saç yıkama"],
        "queries": ["şampuan saç bakım", "şampuan kuru saç"],
        "required": ["şampuan", "saç", "shampoo"],
        "forbidden": ["parfüm", "krem", "maskara", "ruj", "lamba", "telefon"],
    },
    {
        "name": "saç bakım kremi",
        "trigger": ["saç kremi", "saç maskesi", "saç balsamı", "conditioner", "saç onarıcı"],
        "queries": ["saç bakım kremi", "saç maskesi", "saç kremi onarıcı"],
        "required": ["saç", "krem", "maske", "balsam"],
        "forbidden": ["parfüm", "maskara", "ruj", "lamba", "telefon", "kıyafet"],
    },
    {
        "name": "deodorant",
        "trigger": ["deodorant", "deo", "roll-on", "antiperspirant"],
        "queries": ["deodorant roll on", "antiperspirant deodorant"],
        "required": ["deodorant", "deo", "roll", "antiperspirant"],
        "forbidden": ["parfüm", "krem", "maskara", "lamba", "telefon", "kıyafet"],
    },
    {
        "name": "parfüm",
        "trigger": ["parfüm", "edp", "edt", "eau de", "cologne", "kolonya"],
        "queries": ["parfüm bayan", "parfüm erkek", "edp parfüm"],
        "required": ["parfüm", "edp", "edt", "cologne", "kolonya"],
        "forbidden": ["krem", "maskara", "deodorant", "lamba", "telefon", "kıyafet"],
    },
    {
        "name": "maskara",
        "trigger": ["maskara", "mascara", "kirpik"],
        "queries": ["maskara", "siyah maskara", "hacim veren maskara", "kirpik uzatıcı maskara"],
        "required": ["maskara", "mascara"],
        "forbidden": ["parfüm", "krem", "cream", "nemlendirici", "deodorant", "lamba", "telefon", "kıyafet"],
    },
    {
        "name": "ruj",
        "trigger": ["ruj", "lipstick", "lip gloss", "dudak", "lip liner"],
        "queries": ["ruj dudak makyajı", "mat ruj", "lip gloss"],
        "required": ["ruj", "dudak", "lip"],
        "forbidden": ["parfüm", "krem", "maskara", "lamba", "telefon"],
    },

    # ── Aydınlatma ─────────────────────────────────────────────────────────

    {
        "name": "solar bahçe lambası",
        "trigger": ["solar", "güneş enerjili", "güneş paneli lamba", "solar lamba", "solar led"],
        "queries": ["solar bahçe lambası", "güneş enerjili led lamba", "solar led bahçe aydınlatma"],
        "required": ["solar", "güneş enerjili", "bahçe", "lamba", "led"],
        "forbidden": ["krem", "parfüm", "kıyafet", "ayakkabı", "telefon", "laptop", "deodorant", "maskara"],
    },
    {
        "name": "led bahçe aydınlatma",
        "trigger": ["bahçe lambası", "bahçe aydınlatma", "dış mekan lamba", "dış mekan aydınlatma"],
        "queries": ["led bahçe lambası", "bahçe aydınlatma dış mekan", "dış mekan led lamba"],
        "required": ["bahçe", "lamba", "led", "aydınlatma", "dış mekan"],
        "forbidden": ["krem", "parfüm", "kıyafet", "ayakkabı", "telefon", "laptop"],
    },
    {
        "name": "led ampul",
        "trigger": ["ampul", "led ampul", "e27", "e14", "g9"],
        "queries": ["led ampul", "enerji tasarruflu ampul", "led bulb"],
        "required": ["ampul", "led", "bulb", "e27", "e14"],
        "forbidden": ["krem", "parfüm", "kıyafet", "ayakkabı", "telefon"],
    },
    {
        "name": "avize",
        "trigger": ["avize", "sarkıt", "tavan armatürü"],
        "queries": ["avize tavan", "sarkıt aydınlatma", "tavan armatürü"],
        "required": ["avize", "sarkıt", "tavan"],
        "forbidden": ["krem", "parfüm", "kıyafet", "telefon"],
    },

    # ── Giyim ──────────────────────────────────────────────────────────────

    {
        "name": "t-shirt",
        "trigger": ["t-shirt", "tişört", "tshirt", "t shirt"],
        "queries": ["t-shirt basic", "erkek t-shirt", "kadın tişört", "basic tişört"],
        "required": ["t-shirt", "tişört", "tshirt"],
        "forbidden": ["krem", "parfüm", "lamba", "telefon", "laptop", "pantolon", "elbise", "ayakkabı"],
    },
    {
        "name": "sweatshirt",
        "trigger": ["sweatshirt", "hoodie", "kapüşonlu"],
        "queries": ["sweatshirt kapüşonlu", "hoodie oversize", "basic sweatshirt"],
        "required": ["sweatshirt", "hoodie", "kapüşonlu"],
        "forbidden": ["krem", "parfüm", "lamba", "telefon", "t-shirt", "elbise"],
    },
    {
        "name": "pantolon",
        "trigger": ["pantolon", "jean", "denim", "jogger pant"],
        "queries": ["erkek pantolon", "kadın pantolon", "slim fit pantolon"],
        "required": ["pantolon", "jean", "denim"],
        "forbidden": ["krem", "parfüm", "lamba", "telefon", "t-shirt", "elbise", "sweatshirt"],
    },
    {
        "name": "elbise",
        "trigger": ["elbise", "dress", "etek"],
        "queries": ["kadın elbise", "midi elbise", "günlük elbise"],
        "required": ["elbise", "dress", "etek"],
        "forbidden": ["krem", "parfüm", "lamba", "telefon", "pantolon", "t-shirt"],
    },
    {
        "name": "gömlek",
        "trigger": ["gömlek", "shirt", "bluz", "tunik"],
        "queries": ["erkek gömlek", "kadın gömlek", "oversize gömlek"],
        "required": ["gömlek", "shirt", "bluz"],
        "forbidden": ["krem", "parfüm", "lamba", "telefon", "pantolon", "t-shirt"],
    },

    # ── Ayakkabı ───────────────────────────────────────────────────────────

    {
        "name": "spor ayakkabı",
        "trigger": ["spor ayakkabı", "sneaker", "koşu ayakkabısı", "yürüyüş ayakkabısı"],
        "queries": ["spor ayakkabı erkek", "sneaker kadın", "koşu ayakkabısı"],
        "required": ["ayakkabı", "sneaker"],
        "forbidden": ["krem", "parfüm", "lamba", "telefon", "bot", "sandalet", "terlik"],
    },
    {
        "name": "bot",
        "trigger": ["bot", "çizme", "ankle boot"],
        "queries": ["bot kadın", "çizme erkek", "ankle boot"],
        "required": ["bot", "çizme"],
        "forbidden": ["krem", "parfüm", "lamba", "telefon", "sandalet", "spor ayakkabı"],
    },
    {
        "name": "sandalet",
        "trigger": ["sandalet", "terlik", "flip flop"],
        "queries": ["kadın sandalet", "erkek terlik", "flip flop"],
        "required": ["sandalet", "terlik", "flip"],
        "forbidden": ["krem", "parfüm", "lamba", "telefon", "bot"],
    },

    # ── Elektronik ─────────────────────────────────────────────────────────

    {
        "name": "kablosuz kulaklık",
        "trigger": ["bluetooth kulaklık", "kablosuz kulaklık", "airpod", "tws", "wireless earphone"],
        "queries": ["bluetooth kablosuz kulaklık", "tws kulaklık", "in ear bluetooth kulaklık"],
        "required": ["kulaklık", "earphone", "tws", "bluetooth", "airpod"],
        "forbidden": ["krem", "parfüm", "lamba", "kıyafet", "ayakkabı", "laptop", "telefon", "hoparlör"],
    },
    {
        "name": "kulak üstü kulaklık",
        "trigger": ["kulak üstü kulaklık", "over ear", "kablolu kulaklık", "headphone"],
        "queries": ["kulak üstü kulaklık", "over ear headphone", "kablolu kulaklık"],
        "required": ["kulaklık", "headphone"],
        "forbidden": ["krem", "parfüm", "lamba", "kıyafet", "laptop", "bluetooth", "tws"],
    },
    {
        "name": "akıllı telefon",
        "trigger": ["samsung galaxy", "iphone", "xiaomi", "redmi", "huawei", "akıllı telefon", "smartphone"],
        "queries": ["akıllı telefon android", "samsung galaxy telefon", "xiaomi telefon"],
        "required": ["telefon", "smartphone", "galaxy", "iphone", "redmi"],
        "forbidden": ["krem", "parfüm", "lamba", "kıyafet", "kulaklık", "laptop", "tablet", "kılıf", "kilif", "case", "şarj", "sarj", "kablo", "adaptör", "adapter", "cam", "ekran koruyucu"],
    },
    {
        "name": "powerbank",
        "trigger": ["powerbank", "power bank", "taşınabilir şarj"],
        "queries": ["powerbank 20000mah", "taşınabilir şarj aleti", "powerbank hızlı şarj"],
        "required": ["powerbank", "şarj", "mah"],
        "forbidden": ["krem", "parfüm", "lamba", "kıyafet", "kulaklık", "laptop"],
    },
    {
        "name": "laptop",
        "trigger": ["laptop", "notebook", "dizüstü"],
        "queries": ["laptop notebook", "dizüstü bilgisayar", "gaming laptop"],
        "required": ["laptop", "notebook", "dizüstü", "bilgisayar"],
        "forbidden": ["krem", "parfüm", "lamba", "kıyafet", "kulaklık", "telefon", "tablet"],
    },
    {
        "name": "bluetooth hoparlör",
        "trigger": ["bluetooth hoparlör", "bluetooth speaker", "taşınabilir hoparlör"],
        "queries": ["bluetooth hoparlör taşınabilir", "mini bluetooth speaker"],
        "required": ["hoparlör", "speaker", "bluetooth"],
        "forbidden": ["krem", "parfüm", "lamba", "kıyafet", "kulaklık", "telefon"],
    },

    # ── Çanta ──────────────────────────────────────────────────────────────

    {
        "name": "sırt çantası",
        "trigger": ["sırt çantası", "backpack", "sırt paketi"],
        "queries": ["sırt çantası unisex", "okul sırt çantası", "backpack"],
        "required": ["sırt çantası", "backpack", "sırt"],
        "forbidden": ["krem", "parfüm", "lamba", "telefon", "el çantası", "omuz çantası"],
    },
    {
        "name": "el çantası",
        "trigger": ["el çantası", "omuz çantası", "tote bag", "çapraz çanta"],
        "queries": ["kadın el çantası", "omuz çantası deri", "tote bag"],
        "required": ["çanta", "bag"],
        "forbidden": ["krem", "parfüm", "lamba", "telefon", "sırt çantası"],
    },

    # ── Saat ───────────────────────────────────────────────────────────────

    {
        "name": "akıllı saat",
        "trigger": ["akıllı saat", "smartwatch", "smart watch", "fitness bileklik"],
        "queries": ["akıllı saat smartwatch", "fitness bileklik", "smart watch android"],
        "required": ["saat", "smartwatch", "bileklik"],
        "forbidden": ["krem", "parfüm", "lamba", "telefon", "laptop", "kulaklık"],
    },
    {
        "name": "kol saati",
        "trigger": ["kol saati", "mekanik saat", "analog saat", "kadrans"],
        "queries": ["kol saati erkek", "kadın kol saati", "analog kol saati"],
        "required": ["saat"],
        "forbidden": ["krem", "parfüm", "lamba", "telefon", "akıllı saat", "smartwatch"],
    },
]

# ---------------------------------------------------------------------------
# Main function
# ---------------------------------------------------------------------------

def extract_product_type(product_name: str, category: str, brand: str = "", breadcrumb: str = "") -> dict:
    """
    Returns a dict with:
        name        — canonical type string
        queries     — list[str], ordered most→least specific
        required    — list[str], alt name must contain at least one
        forbidden   — list[str], alt name must contain none
    """
    name_only_norm = _norm(product_name or "")
    combined = " ".join([product_name or "", category or "", breadcrumb or "", brand or ""])
    name_norm = _norm(combined)

    def find_best(haystack: str) -> tuple[dict | None, int]:
        best_match: dict | None = None
        best_len = 0
        for pt in _TYPES:
            for trigger in pt["trigger"]:
                if _norm(trigger) in haystack and len(trigger) > best_len:
                    best_match = pt
                    best_len = len(trigger)
        return best_match, best_len

    # Product name is authoritative. Category words like "cilt bakım" must not
    # override a specific product name such as "maskara".
    best, best_trigger_len = find_best(name_only_norm)
    if not best:
        best, best_trigger_len = find_best(name_norm)

    if best:
        print(f"[product_type] detected: {best['name']!r}  (trigger len={best_trigger_len})")
        return {
            "name": best["name"],
            "queries": list(best["queries"]),
            "required": list(best["required"]),
            "forbidden": list(best["forbidden"]),
            "isSpecific": True,
        }

    # Fallback is intentionally non-specific. Callers should not use it for
    # alternatives because product type mismatch is the main source of bad recs.
    cat_l = _norm(category)
    print(f"[product_type] no specific type found, falling back to category: {category!r}")

    if "kozmetik" in cat_l or "cilt" in cat_l or "güzellik" in cat_l:
        return {
            "name": "kozmetik ürün",
            "queries": ["cilt bakım ürünü", "kozmetik"],
            "required": ["krem", "serum", "tonik", "losyon", "jel", "bakım", "cilt"],
            "forbidden": ["lamba", "telefon", "laptop", "kıyafet", "ayakkabı", "hoparlör"],
            "isSpecific": False,
        }
    if "aydinlatma" in cat_l or "lamba" in cat_l or "aydınlatma" in cat_l:
        return {
            "name": "aydınlatma ürünü",
            "queries": ["led lamba aydınlatma", "bahçe lambası"],
            "required": ["lamba", "led", "aydınlatma", "ampul", "solar"],
            "forbidden": ["krem", "parfüm", "kıyafet", "telefon"],
            "isSpecific": False,
        }
    if "giyim" in cat_l:
        return {
            "name": "giyim ürünü",
            "queries": ["giyim üst", "kıyafet"],
            "required": ["t-shirt", "gömlek", "sweatshirt", "pantolon", "elbise"],
            "forbidden": ["krem", "parfüm", "lamba", "telefon"],
            "isSpecific": False,
        }
    if "ayakkabı" in cat_l:
        return {
            "name": "ayakkabı",
            "queries": ["ayakkabı spor", "sneaker"],
            "required": ["ayakkabı", "sneaker", "bot"],
            "forbidden": ["krem", "parfüm", "lamba", "telefon"],
            "isSpecific": False,
        }
    if "elektronik" in cat_l or "teknoloji" in cat_l:
        return {
            "name": "elektronik ürün",
            "queries": ["elektronik aksesuar"],
            "required": ["kulaklık", "hoparlör", "şarj", "kablo", "adaptör"],
            "forbidden": ["krem", "parfüm", "lamba", "kıyafet"],
            "isSpecific": False,
        }

    # Generic fallback
    return {
        "name": "genel",
        "queries": [],          # caller will use category-based queries
        "required": [],         # no required filter — accept anything
        "forbidden": [],        # no forbidden filter
        "isSpecific": False,
    }
