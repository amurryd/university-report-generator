# =========================================
# streamlit_app.py
# Streamlit UI for University AI Report Generator
# =========================================

import streamlit as st
from pathlib import Path
import traceback

# ---- Import existing project modules ----
from config import Config
from data_aggregator import DataAggregator
from data_processor import DataProcessor
from report_generator import ReportGenerator
from output_manager import OutputManager


# =========================================
# Page Configuration
# =========================================
st.set_page_config(
    page_title="University AI Report Generator",
    layout="centered",
)

st.title("🎓 University AI Report Generator")
st.caption("AI-based institutional report generation for academic documents")

st.divider()


# =========================================
# Sidebar – Configuration
# =========================================
st.sidebar.header("⚙️ Configuration")

report_type = st.sidebar.selectbox(
    "Report Type",
    ["academic", "cooperation", "accreditation"],
    help="Choose the type of institutional report to generate"
)

aggregation_mode = st.sidebar.selectbox(
    "Data Source Mode",
    ["local", "api"],
    help="Use local CSV files or external API"
)

api_endpoint = None
if aggregation_mode == "api":
    api_endpoint = st.sidebar.text_input(
        "API Endpoint URL",
        placeholder="https://api.simaster.ugm.ac.id/..."
    )


# =========================================
# Main Input – Custom Prompt
# =========================================
st.subheader("📝 Custom Prompt (Optional)")

custom_prompt = st.text_area(
    "Additional Instructions",
    height=120,
    placeholder=(
        "Tambahkan instruksi khusus, misalnya:\n"
        "- Fokus pada tren 5 tahun terakhir\n"
        "- Gunakan gaya bahasa formal BAN-PT\n"
        "- Tekankan aspek kerjasama internasional"
    )
)

st.divider()


# =========================================
# Session State Initialization
# =========================================
if "report_text" not in st.session_state:
    st.session_state.report_text = None

if "analysis" not in st.session_state:
    st.session_state.analysis = None

if "usage" not in st.session_state:
    st.session_state.usage = None

if "last_error" not in st.session_state:
    st.session_state.last_error = None


# =========================================
# Generate Button
# =========================================
if st.button("🚀 Generate Report", use_container_width=True):
    st.session_state.report_text = None
    st.session_state.last_error = None

    progress = st.progress(0, text="Initializing...")

    try:
        # ---------------------------------
        # 1. Load config
        # ---------------------------------
        cfg = Config()
        progress.progress(10, text="Loading configuration...")

        # ---------------------------------
        # 2. Data ingestion
        # ---------------------------------
        aggregator = DataAggregator(cache_dir=str(cfg.CACHE_DIR))

        if aggregation_mode == "api" and api_endpoint:
            sources = [api_endpoint]
        else:
            sources = cfg.get_ingestion_sources()

        progress.progress(25, text="Ingesting data...")
        df = aggregator.ingest(sources, cache=True)

        # ---------------------------------
        # 3. Data processing
        # ---------------------------------
        processor = DataProcessor()
        clean_df = processor.clean_data(df)

        progress.progress(45, text="Analyzing data...")
        analysis = processor.analyze_data(clean_df)

        # ---------------------------------
        # 4. AI report generation
        # ---------------------------------
        progress.progress(65, text="Generating AI report...")

        generator = ReportGenerator(
            api_key=cfg.get_api_key(),
            model_name=cfg.get_setting("model_name"),
        )

        report_text, usage = generator.generate_report(
            data_summary=analysis,
            report_type=report_type,
            custom_prompt=custom_prompt  # <-- IMPORTANT
        )

        # ---------------------------------
        # Save to session state
        # ---------------------------------
        st.session_state.report_text = report_text
        st.session_state.analysis = analysis
        st.session_state.usage = usage

        progress.progress(100, text="Completed")

        st.success("Report generated successfully!")

    except Exception as e:
        st.session_state.last_error = traceback.format_exc()
        progress.empty()
        st.error("Failed to generate report")


# =========================================
# Error Display
# =========================================
if st.session_state.last_error:
    with st.expander("❌ Error Details"):
        st.code(st.session_state.last_error)


# =========================================
# Preview Section
# =========================================
if st.session_state.report_text:
    st.divider()
    st.subheader("📄 Report Preview")

    st.markdown(st.session_state.report_text, unsafe_allow_html=True)

    st.divider()

    # ---------------------------------
    # Regenerate / Approve Actions
    # ---------------------------------
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔄 Regenerate", use_container_width=True):
            st.session_state.report_text = None
            st.rerun()

    with col2:
        if st.button("✅ Approve & Save", use_container_width=True):
            try:
                out = OutputManager()
                result = out.save_report(
                    st.session_state.report_text,
                    report_type=f"{report_type}_report",
                    metadata={
                        "token_usage": st.session_state.usage,
                        "source": aggregation_mode,
                    }
                )

                st.success("Report saved successfully!")
                st.write("📄 Markdown:", result["markdown_path"])
                st.write("🖨️ HTML:", result["html_path"])

            except Exception as e:
                st.error("Failed to save report")
                st.code(traceback.format_exc())
