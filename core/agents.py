# core/agents.py
from datetime import datetime
from typing import Dict, Any
from core import state as STATES
from core.calculator import compute_hard_limit, compute_soft_limit, compute_emi
from core.validators import parse_int, is_valid_pan, normalize_pan, is_reasonable_loan_request, sanitize_text


def _base_result(messages=None, next_state=None, store=None):
    return {
        "pending_messages": messages or [],
        "next_state": next_state,
        "store": store or {},
    }


def handle_master(user_msg: str) -> Dict[str, Any]:
    m = (user_msg or "").strip().lower()
    if "loan" in m:
        return _base_result(
            messages=["Great — I can help with a Personal Loan. Before we begin, may I have your full name?"],
            next_state=STATES.SALES_REQUIREMENTS,
        )
    return _base_result(
        messages=["I can assist with Personal Loans. Please type 'loan' to begin the loan application flow."],
        next_state=STATES.MASTER,
    )


def handle_sales(user_msg: str) -> dict:
    text = sanitize_text(user_msg)

    if len(text) < 2:
        return _base_result(
            messages=["Please enter your full name."],
            next_state=STATES.SALES_REQUIREMENTS,
            store={}
        )

    # Do NOT send messages. App decides next prompt.
    return _base_result(
        messages=[],
        next_state=STATES.SALES_REQUIREMENTS,
        store={"name": text},
    )


def handle_initial_underwriting(session_data: dict) -> Dict[str, Any]:
    requested = session_data.get("requested_amount")
    income = session_data.get("income")

    if requested is None or income is None:
        return _base_result(["Required data missing."], STATES.SALES_REQUIREMENTS)

    hard = compute_hard_limit(income)
    soft = compute_soft_limit(income)

    if not is_reasonable_loan_request(requested, hard):
        return _base_result(
            [f"Requested amount Rs. {requested:,} is unreasonably high."],
            STATES.SALES_REQUIREMENTS,
        )

    if requested <= hard:
        messages = [
            "Checking eligibility...",
            f"Good news — your requested amount Rs. {requested:,} is eligible.",
            "Would you like to proceed? (yes/change)"
        ]
        return _base_result(messages, STATES.SALES_NEGOTIATION,
                            store={"hard_limit": hard, "soft_limit": soft})

    else:
        messages = [
            "Checking eligibility...",
            f"Requested amount Rs. {requested:,} exceeds your limit.",
            f"We can offer Rs. {soft:,}. Proceed? (yes/no/change)"
        ]
        return _base_result(messages, STATES.SALES_NEGOTIATION,
                            store={"hard_limit": hard, "soft_limit": soft,
                                   "suggested_amount": soft})


def handle_negotiation(user_msg: str, session_data: dict) -> Dict[str, Any]:
    t = (user_msg or "").strip().lower()
    suggested = session_data.get("suggested_amount")
    requested = session_data.get("requested_amount")
    hard = session_data.get("hard_limit")

    if t in ("yes", "y", "ok", "proceed"):
        approved = suggested if suggested and suggested < requested else requested
        approved = min(approved, hard)

        tenure = session_data.get("tenure") or 12
        emi = compute_emi(approved, tenure)

        return _base_result(
            [
                f"Approved amount: Rs. {approved:,}",
                f"Estimated EMI: Rs. {emi:,}",
                "Please provide your PAN number (ABCDE1234F)."
            ],
            STATES.VERIFICATION,
            store={"approved_amount": approved, "tenure": tenure, "emi": emi}
        )

    if t in ("change", "edit", "no", "n"):
        return _base_result(
            ["Okay — enter the new amount."],
            STATES.SALES_REQUIREMENTS,
            store={"requested_amount": None}
        )

    if t.replace(",", "").isdigit():
        amt = int(t.replace(",", ""))
        if not is_reasonable_loan_request(amt, hard):
            return _base_result(
                [f"Rs. {amt:,} is still too high."],
                STATES.SALES_NEGOTIATION
            )
        return _base_result(
            [f"Noted. Rechecking eligibility..."],
            STATES.UNDERWRITING_INITIAL,
            store={"requested_amount": amt}
        )

    return _base_result(
        ["Say 'yes' to proceed or 'change' to edit."],
        STATES.SALES_NEGOTIATION
    )


def handle_verification(user_msg: str) -> Dict[str, Any]:
    pan = normalize_pan(user_msg)
    if is_valid_pan(pan):
        return _base_result(
            ["PAN verified successfully."],
            STATES.UNDERWRITING_FINAL,
            store={"pan": pan}
        )
    return _base_result(
        ["Invalid PAN. Use format ABCDE1234F."],
        STATES.VERIFICATION
    )


def handle_final_underwriting(session_data: dict) -> Dict[str, Any]:
    approved = session_data.get("approved_amount")
    hard = session_data.get("hard_limit")
    name = session_data.get("name", "Applicant")

    if approved is None or hard is None:
        return _base_result(["Missing data."], STATES.SALES_REQUIREMENTS)

    if approved <= hard:
        return _base_result(
            [
                f"Congratulations {name}! Your loan of Rs. {approved:,} is approved.",
                "Generating your sanction letter..."
            ],
            STATES.SANCTION,
            store={"sanction_timestamp": datetime.utcnow().isoformat()}
        )

    return _base_result(
        ["We cannot approve this amount. Try lowering it."],
        STATES.SALES_REQUIREMENTS
    )


def handle_sanction(session_data: dict) -> Dict[str, Any]:
    approved = session_data.get("approved_amount")
    if approved is None:
        return _base_result(
            ["No approved amount found."],
            STATES.SALES_REQUIREMENTS
        )
    return _base_result(
        ["Generating sanction letter..."],
        STATES.SANCTION
    )
