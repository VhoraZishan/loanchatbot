import os
from dotenv import load_dotenv
load_dotenv()

try:
    from groq import Groq
except ImportError:
    Groq = None


# STRICT LLM INSTRUCTIONS — FIXED
SALES_PROMPT = """
You are a friendly loan officer.

Your ONLY job:
→ Ask the user for the NEXT missing field.
Allowed fields ONLY:
- name
- loan_amount
- monthly_income

Rules:
• If missing_field = name → ask for their full name.
• If missing_field = loan_amount → ask: "What loan amount are you looking for?"
• If missing_field = monthly_income → ask: "What is your monthly income (numbers only)?"
• NEVER ask for other data.
• NEVER repeat past mistakes.
• RESPONSE MUST BE ONE SHORT SENTENCE.
"""


def llm_sales_response(history: str, missing_field: str) -> str:
    print("\n========== LLM CALL ==========")
    print("Missing field:", missing_field)
    print("History:\n", history)
    print("==============================")

    if Groq is None:
        print("NO GROQ MODULE")
        return None

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("NO API KEY FOUND")
        return None

    try:
        client = Groq(api_key=api_key)
    except Exception as e:
        print("CLIENT ERROR:", e)
        return None

    prompt = f"""
{SALES_PROMPT}

Missing field: {missing_field}

Conversation:
{history}

Respond with ONLY one friendly sentence.
"""

    try:
        res = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "system", "content": prompt}],
            max_tokens=25,
        )
        text = res.choices[0].message.content.strip()
        print("LLM RESPONSE:", text)
        return text

    except Exception as e:
        print("LLM ERROR:", e)
        return None
