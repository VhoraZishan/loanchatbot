import streamlit as st
import re

from core.state import SessionState
from core import state as STATES
from core.agents import (
    handle_master,
    handle_sales,
    handle_initial_underwriting,
    handle_negotiation,
    handle_verification,
    handle_final_underwriting,
    handle_sanction,
)
from core.pdf_generator import generate_sanction_letter

# NEW NLP PARSERS
from services.nlp_parsers import parse_loan_amount, parse_monthly_income

# LLM SALES AGENT
from services.llm_sales_agent import llm_sales_response


# ---------------------------------------------------------
# PAGE SETUP
# ---------------------------------------------------------
st.set_page_config(page_title="AI Loan Chatbot", page_icon="💬")
st.title("💬 Personal Loan AI Prototype")

SessionState.init()


# ---------------------------------------------------------
# UTILITY: Apply agent output
# ---------------------------------------------------------
def apply_agent_result(result: dict):
    if not result:
        return

    for k, v in (result.get("store") or {}).items():
        SessionState.set_data(k, v)

    if result.get("next_state") is not None:
        SessionState.set_state(result["next_state"])

    SessionState.set_data("pending_messages", list(result.get("pending_messages") or []))


def get_recent_history(n=8):
    hist = SessionState.get_history()
    return "\n".join([f"{sender}: {msg}" for sender, msg in hist[-n:]])


# ---------------------------------------------------------
# 1. FLUSH PENDING MESSAGES (ONE PER RERUN)
# ---------------------------------------------------------
pending = SessionState.get_data("pending_messages") or []

if pending:
    next_msg = pending.pop(0)
    SessionState.add_bot_message(next_msg)
    SessionState.set_data("pending_messages", pending)

    if pending:
        st.rerun()


# ---------------------------------------------------------
# 2. USER INPUT
# ---------------------------------------------------------
if SessionState.get_state() == STATES.END:
    user_input = None
else:
    user_input = st.chat_input("Type your message...")


if user_input:
    SessionState.add_user_message(user_input)
    lower = user_input.strip().lower()
    data = SessionState.all_data()

    # EXIT
    if lower in ("exit", "quit", "stop"):
        apply_agent_result({
            "pending_messages": ["Session ended. Type 'start' to restart."],
            "next_state": STATES.END
        })
        st.rerun()

    # RESET
    if lower == "start":
        SessionState.reset()
        SessionState.init()
        SessionState.add_bot_message("Restarted! Type 'loan' to begin.")
        st.rerun()

    state = SessionState.get_state()

    # -----------------------------------------------------
    # MASTER
    # -----------------------------------------------------
    if state == STATES.MASTER:
        result = handle_master(user_input)


    # -----------------------------------------------------
    # UNDERWRITING INITIAL
    # -----------------------------------------------------
    elif state == STATES.UNDERWRITING_INITIAL:
        result = handle_initial_underwriting(data)


    # -----------------------------------------------------
    # SALES NEGOTIATION
    # -----------------------------------------------------
    elif state == STATES.SALES_NEGOTIATION:
        result = handle_negotiation(user_input, data)


    # -----------------------------------------------------
    # VERIFICATION
    # -----------------------------------------------------
    elif state == STATES.VERIFICATION:
        result = handle_verification(user_input)


    # -----------------------------------------------------
    # UNDERWRITING FINAL (auto-run below)
    # -----------------------------------------------------
    elif state == STATES.UNDERWRITING_FINAL:
        result = {"pending_messages": [], "next_state": STATES.UNDERWRITING_FINAL}


    # -----------------------------------------------------
    # SANCTION (auto-run below)
    # -----------------------------------------------------
    elif state == STATES.SANCTION:
        result = handle_sanction(data)


    # -----------------------------------------------------
    # END STATE
    # -----------------------------------------------------
    elif state == STATES.END:
        result = {"pending_messages": ["Session closed. Type 'start' to restart."], "next_state": STATES.END}


    # -----------------------------------------------------
    # POST-SANCTION QUESTION
    # -----------------------------------------------------
    elif state == STATES.POST_SANCTION_QUERY:
        choice = lower

        if choice in ("yes", "y"):
            result = {
                "pending_messages": ["Sure — what else can I help you with?"],
                "next_state": STATES.POST_SANCTION_HELP
            }
        elif choice in ("no", "n"):
            result = {
                "pending_messages": ["Alright! Thank you for using the Loan Assistant."],
                "next_state": STATES.END
            }
        else:
            result = {
                "pending_messages": ["Please reply 'yes' or 'no'."],
                "next_state": STATES.POST_SANCTION_QUERY
            }


    # -----------------------------------------------------
    # SALES REQUIREMENTS (NAME → LOAN → INCOME)
    # -----------------------------------------------------
    elif state == STATES.SALES_REQUIREMENTS:

        data = SessionState.all_data()

        # STEP 1 — NAME
        if data.get("name") is None:
            # store name
            result = handle_sales(user_input)
            apply_agent_result(result)

            # ask LLM for next missing field: loan_amount
            history = get_recent_history()
            llm_msg = llm_sales_response(history, "loan_amount")

            apply_agent_result({
                "pending_messages": [llm_msg],
                "next_state": STATES.SALES_REQUIREMENTS
            })
            st.rerun()


        # STEP 2 — LOAN AMOUNT
        elif data.get("requested_amount") is None:

            ok, amt = parse_loan_amount(user_input)

            if ok and amt > 0:

                history = get_recent_history()
                llm_msg = llm_sales_response(history, "monthly_income")

                msgs = [llm_msg] if llm_msg else []

                apply_agent_result({
                    "pending_messages": msgs,
                    "store": {"requested_amount": amt},
                    "next_state": STATES.SALES_REQUIREMENTS
                })
                st.rerun()

            else:
                apply_agent_result({
                    "pending_messages": ["Enter a valid loan amount."],
                    "next_state": STATES.SALES_REQUIREMENTS
                })
                st.rerun()


        # STEP 3 — MONTHLY INCOME
        elif data.get("income") is None:

            ok, inc = parse_monthly_income(user_input)

            if ok and inc > 0:
                full = SessionState.all_data().copy()
                full["income"] = inc

                result = handle_initial_underwriting(full)

                if "store" not in result:
                    result["store"] = {}

                result["store"]["income"] = inc

                history = get_recent_history()
                llm_msg = llm_sales_response(history, "monthly_income")

                if llm_msg:
                    result["pending_messages"].insert(0, llm_msg)

            else:
                result = {
                    "pending_messages": ["Enter a valid monthly income."],
                    "next_state": STATES.SALES_REQUIREMENTS
                }


        else:
            result = handle_initial_underwriting(SessionState.all_data())


    else:
        result = {"pending_messages": ["Unexpected state."], "next_state": STATES.MASTER}

    apply_agent_result(result)
    st.rerun()


# ---------------------------------------------------------
# 3. AUTO-RUN FINAL UNDERWRITING
# ---------------------------------------------------------
if SessionState.get_state() == STATES.UNDERWRITING_FINAL and not (SessionState.get_data("pending_messages") or []):
    result = handle_final_underwriting(SessionState.all_data())
    apply_agent_result(result)
    st.rerun()


# ---------------------------------------------------------
# 4. AUTO-GENERATE SANCTION LETTER
# ---------------------------------------------------------
if SessionState.get_state() == STATES.SANCTION and not SessionState.get_data("pdf_path"):
    try:
        file_path = generate_sanction_letter(SessionState.all_data())
        SessionState.set_data("pdf_path", file_path)
        SessionState.set_state(STATES.POST_SANCTION_QUERY)

        apply_agent_result({
            "pending_messages": ["Your sanction letter is ready. Do you need anything else? (yes/no)"]
        })

    except Exception as e:
        apply_agent_result({
            "pending_messages": [f"Failed to generate PDF: {e}"]
        })

    st.rerun()


# ---------------------------------------------------------
# 5. GREETING ON EMPTY CHAT
# ---------------------------------------------------------
if len(SessionState.get_history()) == 0 and not SessionState.get_data("pending_messages"):
    SessionState.add_bot_message("Hello! I can assist you with a Personal Loan. Type 'loan' to begin.")
    st.rerun()


# ---------------------------------------------------------
# 6. RENDER CHAT HISTORY
# ---------------------------------------------------------
for sender, msg in SessionState.get_history():
    st.chat_message("assistant" if sender == "bot" else "user").write(msg)


# ---------------------------------------------------------
# 7. ALLOW PDF DOWNLOAD
# ---------------------------------------------------------
pdf = SessionState.get_data("pdf_path")
if pdf:
    with open(pdf, "rb") as f:
        st.download_button("📄 Download Sanction Letter", f, file_name=pdf.split("/")[-1])


# ---------------------------------------------------------
# 8. SHOW "NEW CHAT" BUTTON AT END
# ---------------------------------------------------------
if SessionState.get_state() == STATES.END:
    st.write("---")
    if st.button("Start New Chat"):
        SessionState.reset()
        SessionState.init()
        st.rerun()
