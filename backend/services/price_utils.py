"""Shared price parsing utilities used by all scrapers."""

import re


def parse_price_to_string(raw) -> str | None:
    """
    Convert any price representation to Turkish display format "1.299,99 TL".

    Handles:
      - "277,90 TL"    → "277,90 TL"
      - "1.299,99 TL"  → "1.299,99 TL"
      - "1299.99"      → "1.299,99 TL"
      - "1299,99"      → "1.299,99 TL"
      - "₺1.299,99"    → "1.299,99 TL"
      - 169            → "169 TL"
      - None           → None
    """
    if raw is None:
        return None
    s = str(raw).strip()

    # Strip currency symbols
    s = (
        s.replace("₺", "")
         .replace("TL", "")
         .replace("$", "")
         .replace("€", "")
         .replace("USD", "")
         .replace("EUR", "")
         .strip()
    )

    if not s:
        return None

    # Already Turkish format with thousands dots: "1.299,99" or "1.299"
    # Detect: has a comma and the part after comma is exactly 2 digits
    if re.match(r"^\d{1,3}(\.\d{3})*,\d{2}$", s):
        return s + " TL"

    # Turkish format without decimal: "1.299" (dot as thousands separator)
    if re.match(r"^\d{1,3}(\.\d{3})+$", s):
        return s + " TL"

    # Normalise: remove any character that's not digit, dot, or comma
    s = re.sub(r"[^\d.,]", "", s)
    if not s:
        return None

    # Determine numeric value
    float_val: float | None = None

    dot_pos = s.rfind(".")
    comma_pos = s.rfind(",")

    if dot_pos > 0 and comma_pos > 0:
        if dot_pos < comma_pos:
            # European/Turkish: 1.299,99  →  dot=thousands, comma=decimal
            float_val = float(s.replace(".", "").replace(",", "."))
        else:
            # Anglo: 1,299.99  →  comma=thousands, dot=decimal
            float_val = float(s.replace(",", ""))
    elif comma_pos > 0:
        after_comma = s[comma_pos + 1:]
        if len(after_comma) == 2:
            # Decimal comma: 1299,99
            float_val = float(s.replace(",", "."))
        else:
            # Thousands comma only: 1,299
            float_val = float(s.replace(",", ""))
    elif dot_pos > 0:
        after_dot = s[dot_pos + 1:]
        if len(after_dot) == 2:
            # Decimal dot: 1299.99
            float_val = float(s)
        else:
            # Thousands dot only: 1.299
            float_val = float(s.replace(".", ""))
    else:
        try:
            float_val = float(s)
        except ValueError:
            return None

    if float_val is None or float_val <= 0:
        return None

    int_part = int(float_val)
    dec_part = round((float_val - int_part) * 100)
    int_str = f"{int_part:,}".replace(",", ".")
    if dec_part > 0:
        return f"{int_str},{dec_part:02d} TL"
    return f"{int_str} TL"
