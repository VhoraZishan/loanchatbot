def compute_hard_limit(income: int) -> int:
    """
    Hard limit rule: income * 20
    """
    return income * 20


def compute_soft_limit(income: int) -> int:
    """
    Soft limit rule: 85% of hard limit
    """
    return int(compute_hard_limit(income) * 0.85)


def compute_emi(amount: int, tenure_months: int) -> float:
    """
    EMI is simplified for prototype:
    EMI = amount / tenure

    (No interest calculation to avoid LLM inconsistency issues.)
    """
    return round(amount / tenure_months, 2)
