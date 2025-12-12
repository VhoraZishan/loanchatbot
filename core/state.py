import streamlit as st

# ---- ALL allowed states in the system ----
MASTER = "MASTER"
SALES_REQUIREMENTS = "SALES_REQUIREMENTS"
UNDERWRITING_INITIAL = "UNDERWRITING_INITIAL"
SALES_NEGOTIATION = "SALES_NEGOTIATION"
VERIFICATION = "VERIFICATION"
UNDERWRITING_FINAL = "UNDERWRITING_FINAL"
SANCTION = "SANCTION"
POST_SANCTION_QUERY = "POST_SANCTION_QUERY"
POST_SANCTION_HELP = "POST_SANCTION_HELP"
END = "END"


class SessionState:
    """
    Wrapper around Streamlit session_state.
    Stores everything we need across the entire chat flow.
    """

    @staticmethod
    def init():
        if "state" not in st.session_state:
            st.session_state.state = MASTER

        if "history" not in st.session_state:
            st.session_state.history = []

        if "data" not in st.session_state:
            st.session_state.data = {
                "name": None,
                "requested_amount": None,
                "income": None,
                "hard_limit": None,
                "soft_limit": None,
                "suggested_amount": None,   # <-- MISSING, ADD THIS
                "approved_amount": None,
                "emi": None,
                "tenure": None,
                "pan": None,
                "pdf_path": None,
            }


    # --------- Conversation State Management ---------

    @staticmethod
    def set_state(new_state: str):
        st.session_state.state = new_state

    @staticmethod
    def get_state() -> str:
        return st.session_state.state

    # --------- Chat History ---------

    @staticmethod
    def add_bot_message(msg: str):
        st.session_state.history.append(("bot", msg))

    @staticmethod
    def add_user_message(msg: str):
        st.session_state.history.append(("user", msg))

    @staticmethod
    def get_history():
        return st.session_state.history

    # --------- Data Store Accessors ---------

    @staticmethod
    def set_data(key: str, value):
        st.session_state.data[key] = value

    @staticmethod
    def get_data(key: str):
        return st.session_state.data.get(key, None)

    @staticmethod
    def all_data():
        return st.session_state.data

    # --------- Reset Everything ---------

    @staticmethod
    def reset():
        st.session_state.clear()
