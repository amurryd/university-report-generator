# =========================================
# streamlit_app.py
# Streamlit UI for University AI Report Generator
# LED IAPT 4.1 Support with Report Editor
# =========================================

import streamlit as st
from pathlib import Path
import traceback
import os
import json
from datetime import datetime

# ---- Import existing project modules ----
from config import Config
from data_aggregator import DataAggregator
from data_processor import DataProcessor
from report_generator import ReportGenerator
from output_manager import OutputManager
from oauth_client import OAuthClient
from storage_manager import StorageManager


# =========================================
# Available UGM APIs
# =========================================
AVAILABLE_APIS = {
    "Student Aktif": "https://api.simaster.ugm.ac.id/data/v1/test/public/student-aktif",
    "Prodi Unggul": "https://api.simaster.ugm.ac.id/data/v1/test/public/prodi-unggul",
    "Staff Guru Besar": "https://api.simaster.ugm.ac.id/data/v1/test/public/staff-guru-besar",
}

# LED IAPT 4.1 Sections
LED_SECTIONS = {
    "section_1": "1. Pendahuluan dan Konteks (500-700 kata)",
    "section_2": "2. Dokumen Renstra SDM (600-800 kata)",
    "section_3": "3. Ketersediaan Dosen - Kriteria 2.1.2.A (1200-1500 kata)",
    "section_4": "4. Tenaga Kependidikan - Kriteria 2.1.2.B (800-1000 kata)",
    "section_5": "5. Rasio Mahasiswa-Dosen - Kriteria 2.1.2.C (1000-1200 kata)",
    "section_6": "6. Analisis Kekuatan dan Area Perbaikan (1200-1500 kata)",
    "section_7": "7. Kesimpulan dan Rekomendasi (1000-1200 kata)",
}


# =========================================
# Page Configuration
# =========================================
st.set_page_config(
    page_title="LED IAPT 4.1 Report Generator",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🎓 LED IAPT 4.1 Report Generator")
st.caption("Laporan Evaluasi Diri untuk Akreditasi Perguruan Tinggi - BAN-PT")

st.divider()


# =========================================
# Initialize Config and Storage Manager
# =========================================
cfg = Config()

@st.cache_resource
def get_storage_manager():
    """Initialize and cache storage manager"""
    try:
        storage = StorageManager(**cfg.get_postgres_config())
        return storage
    except Exception as e:
        st.sidebar.warning(f"⚠️ Database not available: {e}")
        return None

storage = get_storage_manager()


# =========================================
# Sidebar – Configuration
# =========================================
st.sidebar.header("⚙️ Configuration")

# Report generation mode
generation_mode = st.sidebar.radio(
    "Generation Mode",
    ["Complete Report (All Sections)", "Individual Section"],
    help="Generate complete LED report or specific sections only"
)

# Section selection for individual mode
selected_section = None
if generation_mode == "Individual Section":
    selected_section = st.sidebar.selectbox(
        "Select Section",
        options=list(LED_SECTIONS.keys()),
        format_func=lambda x: LED_SECTIONS[x],
        help="Choose which section to generate"
    )
    st.sidebar.info(f"📝 **Target:** {LED_SECTIONS[selected_section].split('(')[1].strip(')')}")

st.sidebar.divider()

# Data source configuration
st.sidebar.subheader("📊 Data Sources")

aggregation_mode = st.sidebar.selectbox(
    "Data Source Mode",
    ["multi-api", "api", "local"],
    help="Multi-API recommended for LED reports",
)

# API Selection based on mode
api_endpoints = []

if aggregation_mode == "api":
    # Single API mode
    single_api = st.sidebar.selectbox(
        "Select API",
        options=list(AVAILABLE_APIS.keys()),
        help="Choose one API endpoint"
    )
    api_endpoints = [AVAILABLE_APIS[single_api]]
    
elif aggregation_mode == "multi-api":
    # Multiple API mode (default for LED)
    selected_apis = st.sidebar.multiselect(
        "Select APIs",
        options=list(AVAILABLE_APIS.keys()),
        default=list(AVAILABLE_APIS.keys()),  # All selected by default
        help="LED reports require all three APIs for complete data"
    )
    api_endpoints = [AVAILABLE_APIS[api] for api in selected_apis]
    
    # Show selected count
    if selected_apis:
        st.sidebar.success(f"✓ {len(selected_apis)} API(s) selected")
        
        # Validation for LED reports
        if len(selected_apis) < 3:
            st.sidebar.warning("⚠️ LED reports work best with all 3 APIs")
    
    # Option to add custom API
    with st.sidebar.expander("➕ Add Custom API"):
        custom_api = st.text_input(
            "Custom API URL",
            placeholder="https://api.example.com/endpoint",
            key="custom_api_input"
        )
        if custom_api and custom_api.startswith("http"):
            api_endpoints.append(custom_api)
            st.success(f"✓ Custom API added")

st.sidebar.divider()

# Advanced settings
with st.sidebar.expander("⚙️ Advanced Settings"):
    enable_validation = st.checkbox("Enable Report Validation", value=True)
    show_data_preview = st.checkbox("Show Data Preview", value=True)
    show_token_usage = st.checkbox("Show Token Usage Details", value=True)

# Report History in Sidebar
if storage:
    st.sidebar.divider()
    st.sidebar.subheader("📚 Report History")
    
    try:
        reports = storage.list_reports(
            report_type="led_iapt_4.1",
            limit=10
        )
        
        if reports:
            for report in reports:
                with st.sidebar.expander(f"📄 {report['title'][:35]}..."):
                    st.caption(f"🕒 {report['created_at'].strftime('%Y-%m-%d %H:%M')}")
                    st.caption(f"📝 {report['word_count']:,} words")
                    st.caption(f"Status: {report['status']}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Load", key=f"load_{report['id']}"):
                            loaded_report = storage.get_report(report['id'])
                            st.session_state.report_text = loaded_report['content']
                            st.session_state.original_report = loaded_report['content']
                            st.success("✅ Report loaded!")
                            st.rerun()
                    
                    with col2:
                        if st.button("Del", key=f"del_{report['id']}"):
                            storage.delete_report(report['id'])
                            st.success("🗑️ Deleted!")
                            st.rerun()
        else:
            st.sidebar.info("No saved reports yet")
            
    except Exception as e:
        st.sidebar.error(f"Error loading history: {e}")


# =========================================
# Main Input – Custom Prompt
# =========================================
st.subheader("📝 Custom Instructions (Optional)")

col1, col2 = st.columns([2, 1])

with col1:
    custom_prompt = st.text_area(
        "Additional Instructions for AI",
        height=150,
        placeholder=(
            "Contoh instruksi tambahan:\n"
            "- Fokus pada prodi Teknik dan MIPA\n"
            "- Tekankan analisis rasio mahasiswa-dosen\n"
            "- Gunakan bahasa formal BAN-PT\n"
            "- Sertakan rekomendasi spesifik untuk Renstra 2026-2030"
        ),
        help="Instruksi khusus akan ditambahkan ke setiap bagian yang dihasilkan"
    )

with col2:
    st.info("""
    **💡 Tips:**
    - Spesifik lebih baik
    - Fokus pada aspek tertentu
    - Referensi dokumen/data
    - Gunakan bahasa Indonesia
    """)

st.divider()


# =========================================
# Session State Initialization
# =========================================
session_keys = [
    "report_text", "analysis", "usage", "html_path", 
    "last_error", "ingested_df", "validation_results",
    "generated_sections", "data_summary", "edit_mode",
    "edited_report", "edit_history", "original_report"
]

for key in session_keys:
    if key not in st.session_state:
        st.session_state[key] = None

# Initialize sections dict and edit history
if st.session_state.generated_sections is None:
    st.session_state.generated_sections = {}

if st.session_state.edit_history is None:
    st.session_state.edit_history = []

if st.session_state.edit_mode is None:
    st.session_state.edit_mode = False


# =========================================
# Generate Button
# =========================================
button_label = "🚀 Generate Complete Report" if generation_mode == "Complete Report (All Sections)" else f"📝 Generate {LED_SECTIONS[selected_section].split('.')[1].split('(')[0].strip()}"

if st.button(button_label, type="primary", width="stretch"):
    # Reset state
    st.session_state.report_text = None
    st.session_state.last_error = None
    st.session_state.html_path = None
    st.session_state.validation_results = None
    st.session_state.edit_mode = False
    st.session_state.edited_report = None

    progress = st.progress(0, text="Initializing...")

    try:
        # ---------------------------------
        # 1. Load config (already done above)
        # ---------------------------------
        progress.progress(5, text="Loading configuration...")

        # ---------------------------------
        # 2. OAuth (API mode only)
        # ---------------------------------
        oauth_client = None
        if aggregation_mode in ["api", "multi-api"]:
            progress.progress(10, text="Authenticating with UGM API...")
            oauth_client = OAuthClient(
                client_id=st.secrets["UGM_CLIENT_ID"],
                client_secret=st.secrets["UGM_CLIENT_SECRET"],
                token_url="https://oauth.simaster.ugm.ac.id/oauth/token",
                scope="dataset.public.test.read",
            )

        # ---------------------------------
        # 3. Data ingestion
        # ---------------------------------
        aggregator = DataAggregator(
    cache_dir=cfg.cache_dir,          # Use config
    oauth_client=oauth_client,
    cache_ttl_hours=cfg.cache_ttl_hours  # ADD THIS
)

        # Determine sources based on mode
        if aggregation_mode == "local":
            sources = cfg.get_ingestion_sources()
        elif aggregation_mode in ["api", "multi-api"]:
            if not api_endpoints:
                st.error("⚠️ Please select at least one API endpoint")
                st.stop()
            sources = api_endpoints
        else:
            sources = cfg.get_ingestion_sources()

        progress.progress(20, text=f"Ingesting data from {len(sources)} source(s)...")
        df = aggregator.ingest(sources, cache=True)
        
        # Store ingested data
        st.session_state.ingested_df = df

        st.info(f"📊 Ingested {len(df):,} rows from {len(sources)} source(s)")

        # ---------------------------------
        # 4. Data processing
        # ---------------------------------
        progress.progress(35, text="Processing and analyzing data...")
        processor = DataProcessor()
        clean_df = processor.clean_data(df)

        # Enhanced analysis for LED reports
        analysis = processor.analyze_data(clean_df)
        
        # Store processed data summary
        st.session_state.data_summary = analysis
        st.session_state.analysis = analysis

        # ---------------------------------
        # 5. AI report generation
        # ---------------------------------
        generator = ReportGenerator(
            api_key=cfg.get_api_key(),
            model_name=cfg.get_setting("model_name"),
            prompt_path="prompts/prompt_templates.json",
        )

        if generation_mode == "Complete Report (All Sections)":
            # Generate complete LED report
            progress.progress(50, text="Generating complete LED report (7 sections)...")
            
            with st.spinner("🔄 Generating all sections... This may take 2-3 minutes"):
                report_text, usage = generator.generate_full_led_report(
                    data_summary=analysis,
                    custom_prompt=custom_prompt
                )
            
            st.session_state.report_text = report_text
            st.session_state.original_report = report_text  # Save original
            st.session_state.usage = usage
            
        else:
            # Generate individual section
            section_num = selected_section.split('_')[1]
            progress.progress(50, text=f"Generating Section {section_num}...")
            
            report_text, usage = generator.generate_report(
                data_summary=analysis,
                section=selected_section,
                custom_prompt=custom_prompt
            )
            
            # Store in sections dict
            st.session_state.generated_sections[selected_section] = report_text
            st.session_state.report_text = report_text
            st.session_state.original_report = report_text  # Save original
            st.session_state.usage = usage

        progress.progress(90, text="Validating report...")

        # ---------------------------------
        # 6. Validation (if enabled)
        # ---------------------------------
        if enable_validation:
            validation = generator.validate_report(
                report_text=report_text,
                data_summary=analysis,
                section=selected_section if generation_mode == "Individual Section" else None
            )
            st.session_state.validation_results = validation

        progress.progress(100, text="Completed!")
        st.success("✅ Report generated successfully!")
        
        # ---------------------------------
        # 7. Save to database (if available)
        # ---------------------------------
        if storage and st.session_state.report_text:
            try:
                final_report = st.session_state.report_text
                
                # Determine report title
                if generation_mode == "Complete Report (All Sections)":
                    report_title = f"LED IAPT 4.1 - Complete Report"
                else:
                    section_name = LED_SECTIONS[selected_section].split('.')[1].split('(')[0].strip()
                    report_title = f"LED IAPT 4.1 - {section_name}"
                
                # Save to database
                report_id = storage.save_report(
                    content=final_report,
                    report_type="led_iapt_4.1",
                    section=selected_section if generation_mode == "Individual Section" else None,
                    title=f"{report_title} - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    metadata={
                        'generation_mode': generation_mode,
                        'word_count': len(final_report.split()),
                        'custom_prompt': custom_prompt if custom_prompt else None,
                        'api_count': len(api_endpoints) if api_endpoints else 0,
                    },
                    status='draft'
                )
                
                # Track token usage if available
                if st.session_state.usage:
                    usage = st.session_state.usage
                    storage.track_token_usage(
                        report_id=report_id,
                        prompt_tokens=usage.get('prompt_tokens', 0),
                        output_tokens=usage.get('output_tokens', 0),
                        total_tokens=usage.get('total_tokens', 0),
                        model_name="gemini-2.5-flash"
                    )
                
                st.info(f"💾 Report saved to database (ID: {report_id})")
                
            except Exception as e:
                st.warning(f"⚠️ Report generated but could not save to database: {e}")

    except Exception as e:
        st.session_state.last_error = traceback.format_exc()
        progress.empty()
        st.error(f"❌ Failed to generate report: {str(e)}")


# =========================================
# Error Display
# =========================================
if st.session_state.last_error:
    with st.expander("❌ Error Details", expanded=False):
        st.code(st.session_state.last_error, language="python")


# =========================================
# Data Preview & Analysis (Optional)
# =========================================
if st.session_state.ingested_df is not None and show_data_preview:
    with st.expander("📊 View Ingested Data & Analysis", expanded=False):
        df = st.session_state.ingested_df
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Rows", f"{len(df):,}")
        with col2:
            st.metric("Total Columns", len(df.columns))
        with col3:
            sources_count = df['source_endpoint'].nunique() if 'source_endpoint' in df.columns else 1
            st.metric("API Sources", sources_count)
        with col4:
            if st.session_state.analysis:
                total_students = st.session_state.analysis.get('total_students', 0)
                st.metric("Total Students", f"{total_students:,}")
        
        # Data preview tabs
        tab1, tab2, tab3 = st.tabs(["📋 Raw Data", "📈 Analysis Summary", "🔍 Data Quality"])
        
        with tab1:
            st.dataframe(df.head(50), width="stretch")
        
        with tab2:
            if st.session_state.analysis:
                st.json(st.session_state.analysis, expanded=False)
        
        with tab3:
            # Data quality metrics
            quality_cols = st.columns(3)
            with quality_cols[0]:
                null_pct = (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
                st.metric("Null Values", f"{null_pct:.2f}%")
            with quality_cols[1]:
                duplicate_pct = (df.duplicated().sum() / len(df)) * 100
                st.metric("Duplicates", f"{duplicate_pct:.2f}%")
            with quality_cols[2]:
                st.metric("Data Freshness", "Real-time" if aggregation_mode != "local" else "Cached")


# =========================================
# Validation Results Display
# =========================================
if st.session_state.validation_results and enable_validation:
    with st.expander("✅ Validation Results", expanded=True):
        validation = st.session_state.validation_results
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if validation["is_valid"]:
                st.success("✅ Valid")
            else:
                st.error("❌ Issues Found")
        
        with col2:
            st.metric("Issues", len(validation.get("issues", [])))
        
        with col3:
            st.metric("Warnings", len(validation.get("warnings", [])))
        
        if validation.get("issues"):
            st.subheader("🚨 Issues")
            for issue in validation["issues"]:
                st.error(f"• {issue}")
        
        if validation.get("warnings"):
            st.subheader("⚠️ Warnings")
            for warning in validation["warnings"]:
                st.warning(f"• {warning}")
        
        if validation["is_valid"]:
            st.success("👍 Report meets all validation criteria!")


# =========================================
# Report Preview & Editor
# =========================================
if st.session_state.report_text:
    st.divider()
    
    # Header with metadata
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        display_text = st.session_state.edited_report if st.session_state.edited_report else st.session_state.report_text
        st.metric("Report Length", f"{len(display_text):,} chars")
    with col2:
        word_count = len(display_text.split())
        st.metric("Word Count", f"{word_count:,} words")
    with col3:
        if st.session_state.usage and show_token_usage:
            total_tokens = st.session_state.usage.get('total_tokens', 0)
            st.metric("Total Tokens", f"{total_tokens:,}")
    with col4:
        if st.session_state.edited_report:
            st.metric("Status", "📝 Edited")
        else:
            st.metric("Status", "🤖 AI Generated")
    
    # =========================================
    # REPORT EDITOR SECTION
    # =========================================
    st.subheader("📝 Report Editor")
    
    # Editor mode toggle
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        if st.session_state.edit_mode:
            st.info("✏️ **Edit Mode Active** - Make changes below")
        else:
            st.info("👁️ **Preview Mode** - Click 'Edit Report' to make changes")
    
    with col2:
        if st.button(
            "✏️ Edit Report" if not st.session_state.edit_mode else "👁️ Preview Mode",
            width="stretch",
            type="primary" if not st.session_state.edit_mode else "secondary"
        ):
            st.session_state.edit_mode = not st.session_state.edit_mode
            st.rerun()
    
    with col3:
        if st.session_state.edited_report and st.session_state.original_report:
            if st.button("🔄 Restore Original", width="stretch"):
                st.session_state.edited_report = None
                st.session_state.edit_mode = False
                st.success("✅ Restored to original AI-generated version")
                st.rerun()
    
    # Display editor or preview based on mode
    if st.session_state.edit_mode:
        # ========================================
        # EDIT MODE - Text Editor
        # ========================================
        st.markdown("---")
        
        # Editor tabs for different editing modes
        edit_tab1, edit_tab2, edit_tab3 = st.tabs([
            "📝 Full Editor",
            "✂️ Section Editor", 
            "🔍 Find & Replace"
        ])
        
        with edit_tab1:
            st.caption("Edit the complete report below. Changes are saved automatically.")
            
            # Get current text (edited or original)
            current_text = st.session_state.edited_report if st.session_state.edited_report else st.session_state.report_text
            
            # Text editor with proper height
            edited_text = st.text_area(
                "Report Content",
                value=current_text,
                height=600,
                key="full_editor",
                help="Edit the report content. Markdown formatting is supported."
            )
            
            # Save button
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                words_changed = len(edited_text.split()) - len(current_text.split())
                st.caption(f"Word count change: {words_changed:+d} words")
            
            with col2:
                if st.button("💾 Save Changes", width="stretch", type="primary"):
                    # Save to edit history
                    st.session_state.edit_history.append({
                        'timestamp': datetime.now().isoformat(),
                        'previous': current_text,
                        'new': edited_text,
                        'word_count_change': words_changed
                    })
                    
                    st.session_state.edited_report = edited_text
                    st.success("✅ Changes saved!")
                    st.rerun()
            
            with col3:
                if st.button("❌ Discard", width="stretch"):
                    st.session_state.edit_mode = False
                    st.rerun()
        
        with edit_tab2:
            st.caption("Edit specific sections of your report")
            
            # Parse sections from report
            current_text = st.session_state.edited_report if st.session_state.edited_report else st.session_state.report_text
            
            # Simple section detection (by headers)
            sections = []
            current_section = {"title": "Introduction", "content": ""}
            
            for line in current_text.split('\n'):
                if line.strip().startswith('#'):
                    if current_section["content"]:
                        sections.append(current_section)
                    current_section = {"title": line.strip('#').strip(), "content": ""}
                else:
                    current_section["content"] += line + "\n"
            
            if current_section["content"]:
                sections.append(current_section)
            
            # Section selector
            if sections:
                selected_section_idx = st.selectbox(
                    "Select section to edit",
                    range(len(sections)),
                    format_func=lambda i: sections[i]["title"]
                )
                
                selected_sec = sections[selected_section_idx]
                
                st.markdown(f"### Editing: {selected_sec['title']}")
                
                edited_section = st.text_area(
                    "Section Content",
                    value=selected_sec["content"],
                    height=400,
                    key=f"section_editor_{selected_section_idx}"
                )
                
                if st.button("💾 Save Section", type="primary"):
                    # Rebuild full text with edited section
                    new_text = ""
                    for i, sec in enumerate(sections):
                        if i == selected_section_idx:
                            new_text += f"# {sec['title']}\n{edited_section}\n"
                        else:
                            new_text += f"# {sec['title']}\n{sec['content']}\n"
                    
                    st.session_state.edited_report = new_text.strip()
                    st.success(f"✅ Section '{selected_sec['title']}' updated!")
                    st.rerun()
            else:
                st.info("No sections detected. Use Full Editor instead.")
        
        with edit_tab3:
            st.caption("Find and replace text throughout the report")
            
            col1, col2 = st.columns(2)
            
            with col1:
                find_text = st.text_input(
                    "Find",
                    placeholder="Text to find...",
                    key="find_input"
                )
            
            with col2:
                replace_text = st.text_input(
                    "Replace with",
                    placeholder="Replacement text...",
                    key="replace_input"
                )
            
            # Options
            col1, col2 = st.columns(2)
            with col1:
                case_sensitive = st.checkbox("Case sensitive", value=False)
            with col2:
                whole_word = st.checkbox("Whole words only", value=False)
            
            current_text = st.session_state.edited_report if st.session_state.edited_report else st.session_state.report_text
            
            # Count occurrences
            if find_text:
                import re
                if case_sensitive:
                    pattern = re.escape(find_text)
                else:
                    pattern = re.escape(find_text)
                
                if whole_word:
                    pattern = r'\b' + pattern + r'\b'
                
                try:
                    occurrences = len(re.findall(pattern, current_text, 0 if case_sensitive else re.IGNORECASE))
                    st.info(f"Found {occurrences} occurrence(s)")
                except:
                    occurrences = 0
                    st.warning("Invalid search pattern")
                
                # Replace buttons
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("🔄 Replace All", width="stretch", type="primary"):
                        if find_text and replace_text is not None:
                            try:
                                if case_sensitive:
                                    new_text = re.sub(pattern, replace_text, current_text)
                                else:
                                    new_text = re.sub(pattern, replace_text, current_text, flags=re.IGNORECASE)
                                
                                st.session_state.edited_report = new_text
                                st.success(f"✅ Replaced {occurrences} occurrence(s)!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
                
                with col2:
                    if st.button("Preview Changes", width="stretch"):
                        if find_text:
                            # Show preview with highlights
                            preview = current_text[:500]
                            if find_text in preview:
                                highlighted = preview.replace(find_text, f"**{find_text}**")
                                st.markdown(highlighted)
    
    else:
        # ========================================
        # PREVIEW MODE - Read-only Display
        # ========================================
        
        # Report display with tabs
        preview_tab1, preview_tab2, preview_tab3 = st.tabs([
            "📖 Formatted View", 
            "📝 Raw Markdown",
            "📊 Statistics"
        ])
        
        display_text = st.session_state.edited_report if st.session_state.edited_report else st.session_state.report_text
        
        with preview_tab1:
            st.markdown(display_text, unsafe_allow_html=True)
        
        with preview_tab2:
            st.code(display_text, language="markdown")
        
        with preview_tab3:
            # Text statistics
            st.subheader("📊 Report Statistics")
            
            words = display_text.split()
            sentences = display_text.split('.')
            paragraphs = [p for p in display_text.split('\n\n') if p.strip()]
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Words", f"{len(words):,}")
            with col2:
                st.metric("Sentences", f"{len(sentences):,}")
            with col3:
                st.metric("Paragraphs", len(paragraphs))
            with col4:
                avg_words = len(words) / len(paragraphs) if paragraphs else 0
                st.metric("Avg Words/Para", f"{avg_words:.1f}")
            
            # Section breakdown
            if st.session_state.edited_report:
                st.subheader("📝 Edit History")
                if st.session_state.edit_history:
                    for i, edit in enumerate(reversed(st.session_state.edit_history[-5:]), 1):
                        with st.expander(f"Edit {i} - {edit['timestamp'][:19]}"):
                            st.caption(f"Word count change: {edit['word_count_change']:+d}")
                            if st.button(f"Revert to this version", key=f"revert_{i}"):
                                st.session_state.edited_report = edit['previous']
                                st.success("✅ Reverted!")
                                st.rerun()
                else:
                    st.info("No edit history yet")

    st.divider()

    # ---------------------------------
    # Token Usage Details (if enabled)
    # ---------------------------------
    if show_token_usage and st.session_state.usage:
        with st.expander("💡 Token Usage Details", expanded=False):
            usage = st.session_state.usage
            
            cols = st.columns(3)
            with cols[0]:
                st.metric(
                    "Prompt Tokens",
                    f"{usage.get('prompt_tokens', 0):,}",
                    help="Tokens used for input/context"
                )
            with cols[1]:
                st.metric(
                    "Output Tokens",
                    f"{usage.get('output_tokens', 0):,}",
                    help="Tokens generated in output"
                )
            with cols[2]:
                st.metric(
                    "Total Tokens",
                    f"{usage.get('total_tokens', 0):,}",
                    help="Total tokens consumed"
                )
            
            # Cost estimation (approximate)
            if usage.get('total_tokens'):
                # Gemini 2.5 Flash pricing (approximate)
                cost_per_million = 0.075  # Input: $0.075/1M, Output: $0.30/1M (average)
                estimated_cost = (usage['total_tokens'] / 1_000_000) * cost_per_million
                st.info(f"💰 Estimated cost: ${estimated_cost:.4f} USD")

    # ---------------------------------
    # Action Buttons
    # ---------------------------------
    st.subheader("⚡ Actions")
    
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("🔄 Regenerate", width="stretch"):
            st.session_state.report_text = None
            st.session_state.edited_report = None
            st.session_state.validation_results = None
            st.session_state.edit_mode = False
            st.rerun()

    with col2:
        # Determine which version to save
        final_report = st.session_state.edited_report if st.session_state.edited_report else st.session_state.report_text
        
        if st.button("✅ Approve & Save", type="primary", width="stretch"):
            try:
                out = OutputManager()
                
                # Determine report type
                if generation_mode == "Complete Report (All Sections)":
                    report_name = "led_iapt_4.1_complete"
                else:
                    section_name = LED_SECTIONS[selected_section].split('.')[1].split('(')[0].strip().replace(' ', '_')
                    report_name = f"led_iapt_4.1_{selected_section}"
                
                result = out.save_report(
                    final_report,  # Save edited version if exists
                    report_type=report_name,
                    metadata={
                        "token_usage": st.session_state.usage,
                        "source": aggregation_mode,
                        "api_count": len(api_endpoints) if api_endpoints else 0,
                        "generation_mode": generation_mode,
                        "section": selected_section if selected_section else "complete",
                        "validation": st.session_state.validation_results,
                        "edited": st.session_state.edited_report is not None,
                        "edit_count": len(st.session_state.edit_history) if st.session_state.edit_history else 0
                    },
                )

                html_path = result.get("html_path")
                st.session_state.html_path = html_path

                st.success("✅ Report approved and saved!")

            except Exception as e:
                st.error(f"❌ Failed to save report: {str(e)}")
                with st.expander("Error details"):
                    st.code(traceback.format_exc())

    with col3:
        if st.button("📋 Copy to Clipboard", width="stretch"):
            # This would require JavaScript - showing a message instead
            st.info("💡 Use the Raw Markdown tab above to copy the text")
    
    with col4:
        if st.session_state.edited_report:
            # Compare with original
            if st.button("🔍 Compare Versions", width="stretch"):
                st.session_state.show_diff = True
                st.rerun()


# =========================================
# Version Comparison (if edited)
# =========================================
if st.session_state.get('show_diff') and st.session_state.edited_report and st.session_state.original_report:
    st.divider()
    st.subheader("🔍 Version Comparison")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🤖 Original (AI Generated)")
        st.markdown(st.session_state.original_report[:2000] + "..." if len(st.session_state.original_report) > 2000 else st.session_state.original_report)
    
    with col2:
        st.markdown("### ✏️ Edited Version")
        st.markdown(st.session_state.edited_report[:2000] + "..." if len(st.session_state.edited_report) > 2000 else st.session_state.edited_report)
    
    # Statistics comparison
    st.markdown("### 📊 Changes Summary")
    
    orig_words = len(st.session_state.original_report.split())
    edit_words = len(st.session_state.edited_report.split())
    word_diff = edit_words - orig_words
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Original Word Count", f"{orig_words:,}")
    with col2:
        st.metric("Edited Word Count", f"{edit_words:,}")
    with col3:
        st.metric("Change", f"{word_diff:+,}", delta=f"{(word_diff/orig_words*100):+.1f}%")
    
    if st.button("Close Comparison"):
        st.session_state.show_diff = False
        st.rerun()


# =========================================
# Download Section
# =========================================
if st.session_state.html_path:
    st.divider()
    st.subheader("⬇️ Download Final Report")

    col1, col2 = st.columns(2)
    
    with col1:
        with open(st.session_state.html_path, "rb") as f:
            st.download_button(
                label="📥 Download HTML Report",
                data=f,
                file_name=Path(st.session_state.html_path).name,
                mime="text/html",
                width="stretch",
            )
    
    with col2:
        # Download the final version (edited if exists, otherwise original)
        final_report = st.session_state.edited_report if st.session_state.edited_report else st.session_state.report_text
        st.download_button(
            label="📥 Download Markdown",
            data=final_report,
            file_name=Path(st.session_state.html_path).stem + ".md",
            mime="text/markdown",
            width="stretch",
        )


# =========================================
# Section Management (for individual mode)
# =========================================
if generation_mode == "Individual Section" and st.session_state.generated_sections:
    st.divider()
    st.subheader("📚 Generated Sections")
    
    sections_list = list(st.session_state.generated_sections.keys())
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info(f"✓ {len(sections_list)} section(s) generated")
    with col2:
        if st.button("🗑️ Clear All", width="stretch"):
            st.session_state.generated_sections = {}
            st.rerun()
    
    # Display generated sections
    for section_key in sections_list:
        with st.expander(f"📄 {LED_SECTIONS[section_key]}", expanded=False):
            section_text = st.session_state.generated_sections[section_key]
            st.markdown(section_text[:500] + "..." if len(section_text) > 500 else section_text)
            
            if st.button(f"View Full {section_key}", key=f"view_{section_key}"):
                st.session_state.report_text = section_text
                st.rerun()


# =========================================
# Footer
# =========================================
st.divider()

footer_cols = st.columns([2, 1, 1])
with footer_cols[0]:
    st.caption("🎓 LED IAPT 4.1 Report Generator | BAN-PT Accreditation Tool")
with footer_cols[1]:
    st.caption(f"📊 APIs: {len(api_endpoints) if api_endpoints else 0}")
with footer_cols[2]:
    if st.session_state.usage:
        st.caption(f"🔢 Tokens: {st.session_state.usage.get('total_tokens', 0):,}")