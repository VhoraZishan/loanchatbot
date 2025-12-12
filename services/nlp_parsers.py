# services/nlp_parsers.py
import re


# ----------------------------------------
# NORMALISE TEXT
# ----------------------------------------
def normalize(text: str) -> str:
    return text.lower().replace(",", "").strip()


# ----------------------------------------
# CORE NUMERIC EXTRACTOR (big brains)
# ----------------------------------------
def parse_indian_number(text: str):
    """
    Extracts numeric values from natural language expressions commonly used in India.
    Handles:
    - 50k, 2k, 5K
    - 1 lakh, 1 lac, 2.5 lakh, 1 lack
    - 1 crore, 1 cr, 2.3cr
    - ₹50000, 10000rs
    - "I want a loan of 2 lakhs"
    - decimal numbers
    """

    if not text:
        return False, 0

    t = normalize(text)

    # direct numeric only
    if t.replace(".", "").isdigit():
        return True, int(float(t))

    # remove ₹ and rs
    t = t.replace("₹", "").replace("rs", "").replace("rupees", "")

    # multipliers
    multipliers = {
        "k": 1_000,
        "k.": 1_000,
        "thousand": 1_000,
        "thousands": 1_000,

        "lakh": 100_000,
        "lakhs": 100_000,
        "lac": 100_000,
        "lacs": 100_000,
        "lack": 100_000,  # common misspelling

        "cr": 10_000_000,
        "crore": 10_000_000,
        "crores": 10_000_000,
    }

    # Handle formats like "2.5 lakh", "10k", "3 cr"
    for word, mul in multipliers.items():
        if word in t:
            nums = re.findall(r"[\d\.]+", t)
            if nums:
                try:
                    value = float(nums[0]) * mul
                    return True, int(value)
                except:
                    pass

    # Fallback — any lone number
    nums = re.findall(r"\d+", t)
    if nums:
        return True, int(nums[0])

    return False, 0


# ----------------------------------------
# PARSER: LOAN AMOUNT
# ----------------------------------------
def parse_loan_amount(text: str):
    ok, num = parse_indian_number(text)
    return ok, num


# ----------------------------------------
# PARSER: MONTHLY INCOME
# ----------------------------------------
def parse_monthly_income(text: str):
    """
    Understands phrases like:
    - I earn 20k per month
    - My salary is 35000
    - I make around 50k
    - monthly income is 15,000
    """

    t = normalize(text)

    # look for salary/income words
    income_keywords = ["income", "salary", "earn", "earning", "per month", "monthly"]

    if any(k in t for k in income_keywords):
        ok, value = parse_indian_number(t)
        return ok, value

    # fallback: treat as raw number
    return parse_indian_number(t)
