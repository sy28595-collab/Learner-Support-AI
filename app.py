import os
import streamlit as st

from ui_pages import dashboard
from ui_pages import summarizer
from ui_pages import review
from ui_pages import history
from ui_pages import analytics
from ui_pages import export

from database.db import get_connection, init_db
from database.import_data import import_conversations
from src.search import search_conversations


# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="Learner Support AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==========================================
# 2. DATABASE INITIALIZATION
# ==========================================

@st.cache_resource
def initialize_app():

    init_db()

    with get_connection() as connection:

        count = connection.execute(
            "SELECT COUNT(*) FROM support_threads"
        ).fetchone()[0]

    if count == 0:
        import_conversations()

    return True


initialize_app()


# ==========================================
# 3. SESSION STATE
# ==========================================

if "page_navigation" not in st.session_state:
    st.session_state["page_navigation"] = "Dashboard"

if "global_search" not in st.session_state:
    st.session_state["global_search"] = ""

if "search_results" not in st.session_state:
    st.session_state["search_results"] = None

if "search_submitted" not in st.session_state:
    st.session_state["search_submitted"] = False


# ==========================================
# 4. NAVIGATION FUNCTIONS
# ==========================================

def go_home():

    st.session_state["page_navigation"] = "Dashboard"


def go_to_review():

    st.session_state["page_navigation"] = "Handover Review"


def go_to_history():

    st.session_state["page_navigation"] = "Conversation History"


# ==========================================
# 5. GLOBAL SEARCH
# ==========================================

def run_global_search():

    query = st.session_state.get(
        "global_search", ""
    ).strip()

    if not query:

        st.session_state["search_results"] = None
        st.session_state["search_submitted"] = False

        return

    try:

        result = search_conversations(
            query=query,
            page=1,
            page_size=10
        )

        st.session_state["search_results"] = result
        st.session_state["search_submitted"] = True

    except Exception as error:

        st.session_state["search_results"] = {
            "error": str(error)
        }

        st.session_state["search_submitted"] = True


# ==========================================
# 6. DATABASE STATUS
# ==========================================

def get_database_status():

    try:

        with get_connection() as connection:

            connection.execute("SELECT 1").fetchone()

        return True

    except Exception:

        return False


# ==========================================
# 7. GEMINI CONFIGURATION STATUS
# ==========================================

def get_gemini_status():

    if os.getenv("GEMINI_API_KEY"):
        return True

    try:
        return bool(st.secrets.get("GEMINI_API_KEY"))

    except Exception:
        return False


# ==========================================
# 8. PENDING NOTIFICATIONS
# ==========================================

def get_pending_notifications():

    try:

        with get_connection() as connection:

            result = connection.execute(
                """
                SELECT COUNT(*)
                FROM handover_summaries
                WHERE review_status = 'pending'
                """
            ).fetchone()

        return result[0]

    except Exception:

        return 0


# ==========================================
# 9. GLOBAL CSS
# ==========================================

st.markdown(
    """
    <style>

    /* GLOBAL BACKGROUND */

    .stApp {

        background:
            radial-gradient(
                circle at 5% 5%,
                rgba(99, 102, 241, 0.13),
                transparent 30%
            ),

            radial-gradient(
                circle at 95% 5%,
                rgba(168, 85, 247, 0.13),
                transparent 30%
            ),

            linear-gradient(
                135deg,
                #EEF2FF,
                #F5F3FF,
                #EDE9FE
            );

        color: #172554;
    }


    /* MAIN CONTENT */

    .main .block-container {

        max-width: 1550px;

        padding-top: 0.7rem !important;
        padding-bottom: 1.5rem !important;

        padding-left: 2rem;
        padding-right: 2rem;
    }


    /* PAGE HEADINGS */

    h1, h2, h3, h4 {

        color: #172554 !important;

        letter-spacing: -0.35px;
    }


    /* SIDEBAR BACKGROUND */

    section[data-testid="stSidebar"] {

        background: linear-gradient(
            180deg,
            #111C3A 0%,
            #172554 55%,
            #1E3A5F 100%
        );

        border-right: 1px solid rgba(255,255,255,0.10);
    }


    section[data-testid="stSidebar"] > div {

        background: transparent;
    }


    /* SIDEBAR TEXT */

    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {

        color: #EAF1FF !important;
    }


    /* SIDEBAR CAPTION */

    section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {

        color: #B8C7E6 !important;
    }


    /* SIDEBAR DIVIDER */

    section[data-testid="stSidebar"] hr {

        border-color: rgba(255,255,255,0.16);
    }


    /* SIDEBAR NAVIGATION */

    section[data-testid="stSidebar"] div[role="radiogroup"] {

        gap: 7px;
    }


    section[data-testid="stSidebar"] div[role="radiogroup"] label {

        padding: 10px 11px;

        border-radius: 11px;

        color: #EAF1FF !important;

        transition: all 0.2s ease;

        border: 1px solid transparent;
    }


    /* NAVIGATION HOVER */

    section[data-testid="stSidebar"]
    div[role="radiogroup"] label:hover {

        background: rgba(147, 197, 253, 0.16);

        transform: translateX(3px);
    }


    /* ACTIVE NAVIGATION */

    section[data-testid="stSidebar"]
    div[role="radiogroup"] label:has(input:checked) {

        background: linear-gradient(
            100deg,
            #5145E5,
            #7C3AED
        ) !important;

        border-radius: 11px !important;

        border: 1px solid rgba(255,255,255,0.15);

        box-shadow: 0 5px 14px rgba(99,102,241,0.25);
    }


    section[data-testid="stSidebar"]
    div[role="radiogroup"] label:has(input:checked) p {

        color: #FFFFFF !important;

        font-weight: 750 !important;
    }


    /* SIDEBAR SYSTEM STATUS */

    section[data-testid="stSidebar"] [data-testid="stAlert"] {

        background: #DCFCE7 !important;

        border: 1px solid #86EFAC !important;

        border-radius: 10px !important;

        padding: 10px !important;
    }


    section[data-testid="stSidebar"]
    [data-testid="stAlert"] p {

        color: #166534 !important;

        font-weight: 700 !important;

        opacity: 1 !important;
    }


    section[data-testid="stSidebar"]
    [data-testid="stAlert"] svg {

        fill: #15803D !important;
    }


    /* TOP NAVBAR */

    .st-key-main_navbar {

        background: linear-gradient(
            110deg,
            #FFFFFF,
            #EDF4FF
        );

        border: 1px solid #D7E3F5;

        border-radius: 15px;

        padding: 10px 14px;

        margin-top: 0px;

        margin-bottom: 16px;

        width: 100%;

        box-shadow: 0 6px 20px rgba(30,64,120,0.08);

        position: relative;

        z-index: 5;
    }


    .st-key-main_navbar [data-testid="stHorizontalBlock"] {

        align-items: center;

        gap: 9px;
    }


    .st-key-main_navbar [data-testid="stColumn"] {

        min-width: 0;
    }


    /* NAVBAR BUTTONS */

    .st-key-main_navbar .stButton button {

        min-height: 42px;

        border-radius: 10px;

        border: 1px solid #D7E3F5;

        background: #F8FAFF;

        color: #1E3A5F;

        font-weight: 650;

        transition: all 0.2s ease;

        white-space: nowrap;
    }


    .st-key-main_navbar .stButton button:hover {

        background: #E8F1FF;

        border-color: #93B8F3;

        color: #1D4ED8;

        transform: translateY(-1px);

        box-shadow: 0 5px 13px rgba(37,99,235,0.12);
    }


    /* NAVBAR SEARCH */

    .st-key-main_navbar input {

        min-height: 42px;

        border-radius: 10px !important;

        border: 1px solid #D5E0F0 !important;

        background: #FFFFFF !important;

        color: #172033 !important;
    }


    .st-key-main_navbar input::placeholder {

        color: #8291A8 !important;
    }


    .st-key-main_navbar input:focus {

        border-color: #4F83E3 !important;

        box-shadow: 0 0 0 3px rgba(59,130,246,0.13) !important;
    }


    /* NAVBAR POPOVER */

    .st-key-main_navbar div[data-testid="stPopover"] button {

        min-height: 42px;

        border-radius: 10px;

        border: 1px solid #D7E3F5;

        background: #F8FAFF;

        color: #1E3A5F;

        font-weight: 650;

        white-space: nowrap;
    }


    .st-key-main_navbar div[data-testid="stPopover"] button:hover {

        background: #E8F1FF;

        border-color: #93B8F3;
    }


    /* POPOVER CONTENT */

    div[data-testid="stPopoverBody"] {

        background: #FFFFFF;

        border: 1px solid #DCE6F5;

        border-radius: 13px;

        box-shadow: 0 12px 30px rgba(15,23,42,0.13);
    }


    /* GENERAL CARDS */

    div[data-testid="stVerticalBlockBorderWrapper"] {

        border-color: #DCE6F5;

        border-radius: 13px;

        background: rgba(255,255,255,0.82);
    }


    /* METRIC CARDS */

    div[data-testid="stMetric"] {

        background: linear-gradient(
            145deg,
            #FFFFFF,
            #F3F7FF
        ) !important;

        border: 1px solid #DCE6F5 !important;

        border-radius: 13px;

        padding: 12px !important;

        opacity: 1 !important;

        box-shadow: 0 4px 12px rgba(30,64,120,0.055);

        transition: all 0.2s ease;
    }


    div[data-testid="stMetric"]:hover {

        transform: translateY(-2px);

        border-color: #9DBCF0 !important;

        box-shadow: 0 7px 16px rgba(37,99,235,0.10);
    }


    div[data-testid="stMetric"] [data-testid="stMetricLabel"] {

        color: #536581 !important;

        opacity: 1 !important;

        font-weight: 650 !important;
    }


    div[data-testid="stMetric"] [data-testid="stMetricValue"] {

        color: #172554 !important;

        opacity: 1 !important;

        font-weight: 750 !important;
    }


    /* INPUT FIELDS */

    .stTextInput input,
    .stTextArea textarea,
    .stSelectbox div[data-baseweb="select"] > div {

        border-radius: 9px;
    }


    /* PRIMARY BUTTONS */

    .stButton button[kind="primary"],
    .stFormSubmitButton button[kind="primary"] {

        background: linear-gradient(
            100deg,
            #2563EB,
            #4F46E5
        );

        border: none;

        color: #FFFFFF;

        border-radius: 10px;

        font-weight: 650;

        transition: all 0.2s ease;
    }


    .stButton button[kind="primary"]:hover,
    .stFormSubmitButton button[kind="primary"]:hover {

        background: linear-gradient(
            100deg,
            #1D4ED8,
            #4338CA
        );

        box-shadow: 0 6px 15px rgba(59,130,246,0.22);

        transform: translateY(-1px);
    }


    /* DATAFRAME */

    div[data-testid="stDataFrame"] {

        border: 1px solid #DCE6F5;

        border-radius: 12px;

        overflow: hidden;

        background: #FFFFFF;
    }


    /* ALERTS */

    div[data-testid="stAlert"] {

        border-radius: 11px;
    }


    /* DIVIDERS */

    hr {

        border-color: #D9E3F1;
    }


    /* RESPONSIVE */

    @media (max-width: 900px) {

        .main .block-container {

            padding-left: 1rem;

            padding-right: 1rem;

            padding-top: 0.5rem !important;
        }

        .st-key-main_navbar {

            padding: 8px;
        }
    }


    /* ACCESSIBILITY */

    @media (prefers-reduced-motion: reduce) {

        *,
        *::before,
        *::after {

            animation-duration: 0.01ms !important;

            transition-duration: 0.01ms !important;
        }
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ==========================================
# 10. SIDEBAR NAVIGATION
# ==========================================

with st.sidebar:

    st.markdown("# 🎓 Learner Support AI")

    st.caption("AI-powered support management")

    st.divider()

    st.markdown("### WORKSPACE")


    page_icons = {

        "Dashboard": "🏠 Dashboard",

        "Conversation Summarizer":
            "💬 Conversation Summarizer",

        "Handover Review":
            "📋 Handover Review",

        "Conversation History":
            "📁 Conversation History",

        "Analytics":
            "📊 Analytics",

        "Export":
            "📤 Export"
    }


    selected_page = st.radio(

        "Navigation",

        list(page_icons.keys()),

        format_func=lambda page: page_icons[page],

        label_visibility="collapsed",

        key="page_navigation"
    )


    st.divider()

    # SYSTEM STATUS

    st.markdown("### SYSTEM STATUS")


    database_connected = get_database_status()

    if database_connected:

        st.success("Database Connected")

    else:

        st.error("Database Disconnected")


    gemini_configured = get_gemini_status()

    if gemini_configured:

        st.success("Gemini Configured")

    else:

        st.warning("Gemini Configuration Missing")


    st.caption("Model: gemini-3.6-flash")

    st.divider()

    st.caption("Learner Support AI | Version 1.0")


# ==========================================
# 11. TOP NAVBAR
# ==========================================

pending_count = get_pending_notifications()


with st.container(
    key="main_navbar",
    border=True
):

    (
        nav_search,
        nav_home,
        nav_notify,
        nav_refresh,
        nav_profile,
        nav_status
    ) = st.columns(

        [4.5, 0.8, 1.1, 1, 1.1, 1.2],

        vertical_alignment="center"
    )


    # SEARCH

    with nav_search:

        st.text_input(

            "Global Search",

            placeholder="Search Thread ID, Learner ID or keyword...",

            label_visibility="collapsed",

            key="global_search",

            on_change=run_global_search
        )


    # HOME

    with nav_home:

        st.button(

            "🏠",

            help="Go to Dashboard",

            width="stretch",

            on_click=go_home
        )


    # NOTIFICATIONS

    with nav_notify:

        with st.popover(

            f"🔔 {pending_count}",

            width="content"
        ):

            st.markdown("### Notifications")

            st.caption("Handover review updates")


            if pending_count > 0:

                st.warning(
                    f"{pending_count} summaries are waiting for review."
                )

                if st.button(
                    "Open Pending Reviews",
                    width="stretch"
                ):

                    go_to_review()

                    st.rerun()

            else:

                st.success("No pending reviews.")


    # REFRESH

    with nav_refresh:

        if st.button(

            "↻",

            help="Refresh current page",

            width="stretch"
        ):

            st.rerun()


    # USER PROFILE

    with nav_profile:

        with st.popover(

            "👤 Agent",

            width="content"
        ):

            st.markdown("### User Profile")

            st.markdown("**Support Agent**")

            st.caption("Role: Support Agent")

            st.divider()

            st.caption("Learner Support AI")

            st.caption("Version 1.0")


    # SYSTEM STATUS

    with nav_status:

        with st.popover(

            "🟢 Status",

            width="content"
        ):

            st.markdown("### System Status")


            if get_database_status():

                st.success("SQLite Database: Connected")

            else:

                st.error("SQLite Database: Disconnected")


            if get_gemini_status():

                st.success("Gemini: API key configured")

            else:

                st.warning("Gemini: API key missing")


            st.caption("Model: gemini-3.6-flash")

            st.info(
                "API configuration is checked here. "
                "A live Gemini API request is not performed."
            )


# ==========================================
# 12. GLOBAL SEARCH RESULTS
# ==========================================

search_result = st.session_state.get(
    "search_results"
)


if search_result and st.session_state.get("search_submitted"):

    st.markdown("### 🔍 Search Results")


    if "error" in search_result:

        st.error(
            f"Search failed: {search_result['error']}"
        )

    else:

        records = search_result.get("records", [])

        total_records = search_result.get(
            "total_records",
            len(records)
        )


        st.caption(
            f"{total_records} matching conversations found."
        )


        if records:

            for record in records:

                thread_id = record.get(
                    "thread_id",
                    "Unknown"
                )

                learner_id = record.get(
                    "learner_id",
                    "Unknown"
                )

                status = record.get(
                    "thread_status",
                    "Unknown"
                )


                with st.container(border=True):

                    col1, col2, col3 = st.columns(
                        [2, 2, 1]
                    )


                    with col1:

                        st.markdown(
                            f"**🧵 {thread_id}**"
                        )


                    with col2:

                        st.write(
                            f"👤 {learner_id}"
                        )


                    with col3:

                        st.caption(
                            status.title()
                        )

        else:

            st.info("No matching conversations found.")


    if st.button("✖ Close Search Results"):

        st.session_state["search_results"] = None

        st.session_state["search_submitted"] = False

        st.session_state["global_search"] = ""

        st.rerun()


# ==========================================
# 13. PAGE ROUTING
# ==========================================

if selected_page == "Dashboard":

    dashboard.show()


elif selected_page == "Conversation Summarizer":

    summarizer.show()


elif selected_page == "Handover Review":

    review.show()


elif selected_page == "Conversation History":

    history.show()


elif selected_page == "Analytics":

    analytics.show()


elif selected_page == "Export":

    export.show()