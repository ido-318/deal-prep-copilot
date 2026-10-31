import json

import streamlit as st

import main as prep


st.set_page_config(page_title="עוזר הכנה לפגישות", page_icon="📝")
st.title("עוזר הכנה לפגישות — תרגול")
st.warning(
    "המידע בפרויקט מדומה. אין חיפוש חי ברשת ואין שימוש במודל שפה.",
    icon="⚠️",
)
st.caption(f"זמן ייחוס קבוע לתרגול: {prep.REFERENCE_NOW.isoformat()}")

companies_path = prep.PROJECT_DIR / "data" / "external" / "companies.json"
companies = json.loads(companies_path.read_text(encoding="utf-8"))
limitations = [
    chunk["text"]
    for chunk in prep.chunks
    if chunk["title"] == "מגבלות"
]

with st.form("brief_form"):
    company_input = st.text_input(
        "שם החברה",
        value="אופק ציוד משרדי",
        key="company_input",
    )
    goal_input = st.text_area("מטרת הפגישה", key="goal_input")
    submitted = st.form_submit_button("יצירת תדרוך", type="primary")

if submitted:
    company = company_input.strip()
    goal = goal_input.strip()
    if not company or not goal:
        st.session_state.pop("brief", None)
        st.session_state.pop("brief_company", None)
        st.session_state.pop("brief_goal", None)
        st.session_state["brief_error"] = "יש להזין שם חברה ומטרת פגישה."
    else:
        results = prep.search_chunks(goal, prep.chunks)
        brief = prep.build_brief(
            company,
            goal,
            companies.get(company),
            results,
            limitations,
        )
        st.session_state["brief"] = brief
        st.session_state["brief_company"] = company
        st.session_state["brief_goal"] = goal
        st.session_state.pop("brief_error", None)

if error := st.session_state.get("brief_error"):
    st.error(error)

if brief := st.session_state.get("brief"):
    st.subheader("התדרוך שנוצר")
    st.write(f"חברה: {st.session_state['brief_company']}")
    st.write(f"מטרת הפגישה: {st.session_state['brief_goal']}")
    st.download_button(
        "הורדת התדרוך כקובץ Markdown",
        data=brief.encode("utf-8"),
        file_name="deal-prep-brief.md",
        mime="text/markdown; charset=utf-8",
    )
    st.markdown(brief)
