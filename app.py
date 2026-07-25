import streamlit as st
from datetime import datetime
from core.pdf_extractor import extract_text_from_pdf, is_text_extractable
from core.parameter_parser import parse_parameters
from core.abnormality_detector import annotate_dataframe, parse_range
from core.summary_generator import generate_structured_summary
from core.ocr_extractor import extract_text_with_ocr
from core.analytics import show_status_donut, show_range_position_chart

st.set_page_config(page_title="Medical Report Analyzer", page_icon="🩺", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #F4FAF9; }
    .subtitle { color: #4B5563; font-size: 1.05rem; margin-top: -10px; margin-bottom: 1.5rem; }
    div[data-testid="stMetric"] {
        background: #E6F5F3; border: 1px solid #A7DDD8; border-radius: 10px; padding: 0.8rem;
    }
    .param-card {
        background: white; border: 1px solid #E2E8F0; border-radius: 10px;
        padding: 0.9rem 1.1rem; margin-bottom: 0.6rem;
    }
    .status-normal { color: #059669; font-weight: 600; }
    .status-high { color: #DC2626; font-weight: 600; }
    .status-low { color: #D97706; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "report_history" not in st.session_state:
    st.session_state.report_history = []

def login_page():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("### 🩺 Medical Report Analyzer")
            st.caption("Secure sign-in to access your health reports")
            username = st.text_input("Username", placeholder="Enter username")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            if st.button("Sign In", type="primary", use_container_width=True):
                if username == "admin" and password == "admin123":
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Invalid username or password")
            st.caption("Demo — Username: `admin` | Password: `admin123`")

def render_analysis(df, text, summary, show_ai_insight=True, key_prefix="current"):
    total = len(df)
    abnormal = len(df[df["Status"].isin(["High", "Low"])])
    normal = total - abnormal

    with st.container(border=True):
        st.subheader("🩺 Health Snapshot")
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Parameters", total)
        c2.metric("Normal", normal)
        c3.metric("Abnormal", abnormal)

    if show_ai_insight and summary:
        with st.container(border=True):
            st.subheader("🤖 AI Health Insight")
            st.markdown(f"**Overview:** {summary.get('overview', '')}")

            findings = summary.get("findings", [])
            if findings:
                st.markdown("**Key Findings:**")
                for f in findings:
                    st.markdown(f"""
                    <div class="param-card">
                        <b>⚠️ {f.get('parameter', '')}</b><br>
                        <small>{f.get('explanation', '')}</small>
                    </div>
                    """, unsafe_allow_html=True)

            general_notes = summary.get("general_notes", "")
            if general_notes:
                st.markdown(f"**General Notes:** {general_notes}")

            st.caption("⚠️ This is an AI-generated informational summary, not a medical diagnosis. Please consult your doctor for professional interpretation.")

    with st.container(border=True):
        st.subheader("📊 Analytics")
        tab1, tab2 = st.tabs(["Status Overview", "Range Position"])
        with tab1:
            show_status_donut(df, key=f"{key_prefix}_donut")
        with tab2:
            show_range_position_chart(df, parse_range, key=f"{key_prefix}_range")

    with st.container(border=True):
        st.subheader("🧪 Parameter Details")
        for _, row in df.iterrows():
            low, high = parse_range(row["Reference Range"])
            try:
                value = float(row["Result"])
            except ValueError:
                value = None

            status_class = {"Normal": "status-normal", "High": "status-high", "Low": "status-low"}.get(row["Status"], "")
            status_icon = {"Normal": "✅", "High": "⬆️", "Low": "⬇️"}.get(row["Status"], "❔")

            st.markdown(f"""
            <div class="param-card">
                <b>{row['Parameter']}</b> — {row['Result']} {row['Unit']}
                &nbsp;&nbsp; <span class="{status_class}">{status_icon} {row['Status']}</span>
                <br><small>Reference Range: {row['Reference Range']} {row['Unit']}</small>
            </div>
            """, unsafe_allow_html=True)

            if low is not None and high is not None and value is not None:
                span = high - low
                position = (value - low) / span if span > 0 else 0.5
                position = max(0, min(1, position))
                st.progress(position)

    with st.expander("📄 View Full Extracted Text"):
        st.text_area("Report content", text, height=250, label_visibility="collapsed")

def dashboard_page():
    with st.sidebar:
        st.header("⚙️ Settings")
        show_ai_insight = st.checkbox("Show AI Health Insight", value=True)
        ocr_tolerance = st.slider("OCR Row Sensitivity", min_value=5, max_value=25, value=12,
                                    help="Adjust if scanned report rows aren't grouping correctly. Lower = stricter row grouping.")
        st.divider()
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

    col1, col2 = st.columns([5, 1])
    with col1:
        st.title("🩺 Medical Report Analyzer")
        st.markdown('<p class="subtitle">Upload a lab report to extract, analyze, and understand your health parameters</p>', unsafe_allow_html=True)

    tab_upload, tab_history = st.tabs(["📁 Upload & Analyze", "🕘 Report History"])

    with tab_upload:
        with st.container(border=True):
            st.subheader("📁 Upload Report")
            st.caption("Upload one lab report at a time (PDF)")
            uploaded_file = st.file_uploader("Upload a lab report (PDF)", type=["pdf"], label_visibility="collapsed")

        if uploaded_file is not None:
            text = None
            try:
                uploaded_file.seek(0)
                if is_text_extractable(uploaded_file):
                    uploaded_file.seek(0)
                    text = extract_text_from_pdf(uploaded_file)
                else:
                    st.info("📸 Scanned/image-based PDF detected — running OCR (this may take a moment)...")
                    uploaded_file.seek(0)
                    file_bytes = uploaded_file.read()
                    with st.spinner("Extracting text using OCR..."):
                        text = extract_text_with_ocr(file_bytes, row_tolerance=ocr_tolerance)
            except Exception as e:
                st.error(f"❌ Could not read this PDF: {e}")

            if text is not None:
                df = parse_parameters(text)

                if not df.empty:
                    df = annotate_dataframe(df)

                    summary = None
                    if show_ai_insight:
                        with st.spinner("Analyzing report..."):
                            summary = generate_structured_summary(df)

                    render_analysis(df, text, summary, show_ai_insight=show_ai_insight, key_prefix="current")

                    already_saved = any(
                        entry["filename"] == uploaded_file.name and entry["text"] == text
                        for entry in st.session_state.report_history
                    )
                    if not already_saved:
                        st.session_state.report_history.append({
                            "filename": uploaded_file.name,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "df": df,
                            "text": text,
                            "summary": summary,
                            "total": len(df),
                            "abnormal": len(df[df["Status"].isin(["High", "Low"])])
                        })
                else:
                    st.warning("Could not parse any parameters — check report format.")
                    with st.expander("🔍 Debug: Raw OCR/Extracted Text"):
                        st.text(text)

    with tab_history:
        if not st.session_state.report_history:
            st.info("No reports analyzed yet in this session. Upload a report to see it here.")
        else:
            st.caption(f"{len(st.session_state.report_history)} report(s) analyzed this session")
            for i, entry in enumerate(reversed(st.session_state.report_history)):
                with st.container(border=True):
                    col1, col2, col3 = st.columns([3, 1, 1])
                    col1.markdown(f"**{entry['filename']}**")
                    col2.caption(entry['timestamp'])
                    col3.caption(f"{entry['abnormal']}/{entry['total']} abnormal")

                    if st.button("View Details", key=f"view_{i}"):
                        st.session_state[f"expanded_{i}"] = not st.session_state.get(f"expanded_{i}", False)

                    if st.session_state.get(f"expanded_{i}", False):
                        render_analysis(entry["df"], entry["text"], entry["summary"], show_ai_insight=show_ai_insight, key_prefix=f"history_{i}")

if st.session_state.logged_in:
    dashboard_page()
else:
    login_page()