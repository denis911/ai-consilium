"""
AI Consilium — Dual-Engine Consensus Research Dashboard & Audit Console
"""

import asyncio
import os
import streamlit as st
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

from council.schemas import ConsiliumQueryInput
from council.providers import LLMProviderEngine, DEFAULT_MODELS, OPENROUTER_FREE_MODELS
from council.rag import DuckDBRAGEngine
from council.consensus import ConsensusEngine
from council.synthesizer import LLMJudgeSynthesizer
from council.exporter import ObsidianExporter
from council.telemetry import DuckDBTelemetryLogger

# Page Configuration
st.set_page_config(
    page_title="AI Consilium — Multi-Model Consensus Engine",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.3rem;
        font-weight: 800;
        background: linear-gradient(90deg, #4F46E5, #9333EA, #EC4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #9CA3AF;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: #1F2937;
        border-radius: 12px;
        padding: 1.2rem;
        border: 1px solid #374151;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)


import nest_asyncio
nest_asyncio.apply()


@st.cache_resource
def get_telemetry_logger():
    """Cached DuckDB Telemetry Logger instance to prevent connection leaks across re-runs."""
    return DuckDBTelemetryLogger()


@st.cache_resource
def get_consensus_engine():
    """Cached Consensus Engine instance to prevent duplicate embedding model loads in memory."""
    return ConsensusEngine()


def run_async(coro):
    """Utility helper to run async coroutines safely in Streamlit."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


def main():
    # Header
    st.markdown('<div class="main-header">🏛️ AI Consilium</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Deterministic Multi-Model Consensus Research Harness for Solopreneurs & Founders</div>',
        unsafe_allow_html=True,
    )

    # Initialize Telemetry Logger (Cached Singleton)
    telemetry = get_telemetry_logger()

    # Sidebar Configuration
    st.sidebar.title("⚙️ Engine Settings")

    vault_path = os.environ.get("OBSIDIAN_VAULT_PATH", "C:/ai-memory/ai-concilium")
    st.sidebar.info(f"📂 **Obsidian Vault:**\n`{vault_path}`")

    use_free_tier = st.sidebar.toggle("⚡ OpenRouter $0 Free Model Tier", value=False)

    if use_free_tier:
        st.sidebar.caption("Routing queries to 5 free models on OpenRouter. ℹ️ *Free-tier models have rate limits; switch to frontier models for high-stakes decisions.*")
        selected_models = OPENROUTER_FREE_MODELS
    else:
        st.sidebar.caption("Querying frontier LLM APIs in parallel.")
        selected_models = DEFAULT_MODELS

    st.sidebar.markdown("---")
    st.sidebar.subheader("🔑 Active API Keys")
    st.sidebar.text(f"OpenAI: {'✅' if os.environ.get('OPENAI_API_KEY') else '❌'}")
    st.sidebar.text(f"Gemini: {'✅' if os.environ.get('GEMINI_API_KEY') else '❌'}")
    st.sidebar.text(f"OpenRouter: {'✅' if os.environ.get('OPENROUTER_API_KEY') else '❌'}")

    # Tabs
    tab1, tab2 = st.tabs(["🏛️ Consilium Research", "📊 Audit & Telemetry Console"])

    # ==========================================
    # TAB 1: Consilium Research
    # ==========================================
    with tab1:
        st.subheader("🔍 Research Query")

        user_query = st.text_area(
            "Enter your high-stakes architectural, legal, or business query:",
            placeholder="e.g. Compare PostgreSQL vs DuckDB for single-user desktop analytics with local persistence",
            height=100,
        )

        with st.expander("📚 Optional Reference Context (RAG Ingestion)"):
            st.caption("💡 **Pro-Tip (Pre-Fetch Summarization):** For PDFs, images, or screenshots, ask ChatGPT or Claude to summarize them into Markdown/plain text first, then paste here. This ensures all 5 consensus models receive 100% identical, balanced inputs!")
            rag_context_input = st.text_area(
                "Paste local reference notes or document snippets to ground the query:",
                height=120,
                placeholder="Paste contract clauses, technical specifications, or internal notes...",
            )

        col_run, col_clear = st.columns([1, 5])
        with col_run:
            run_button = st.button("🚀 Run Consilium Engine", type="primary", use_container_width=True)

        if run_button and user_query.strip():
            with st.status("🏛️ Executing Consilium Multi-Model Consensus Engine...", expanded=True) as status:

                # Resolve cached singletons early
                consensus_engine = get_consensus_engine()

                # Step 1: RAG Context Preparation
                status.update(label="1/4 📚 Ingesting context & retrieving RAG snippets...", state="running")
                context_chunks = []
                if rag_context_input.strip():
                    rag_engine = DuckDBRAGEngine(db_path=":memory:", shared_model=consensus_engine.model)
                    rag_engine.ingest_documents([
                        {"id": "doc1", "title": "Reference Context", "content": rag_context_input.strip()}
                    ])
                    results = rag_engine.search(user_query, top_k=3)
                    context_chunks = [r["content"] for r in results]
                    rag_engine.close()

                query_input = ConsiliumQueryInput(
                    query=user_query.strip(),
                    context_chunks=context_chunks,
                    selected_models=selected_models,
                )

                # Step 2: Multi-Model Async Querying
                status.update(label=f"2/4 🌐 Querying {len(selected_models)} LLM providers concurrently...", state="running")
                provider_engine = LLMProviderEngine(default_timeout=35.0)
                responses = run_async(provider_engine.query_concurrently(query_input, use_free_tier=use_free_tier))

                # Step 3: Mathematical Embedding Consensus Scoring
                status.update(label="3/4 📐 Calculating embedding similarity matrix & outlier detection...", state="running")
                consensus_metrics = consensus_engine.compute_consensus(responses)

                # Step 4: Qualitative Synthesis via LLM Judge
                status.update(label="4/4 ⚖️ Executing LLM-as-a-Judge qualitative synthesis...", state="running")
                synthesizer = LLMJudgeSynthesizer()
                final_artifact = run_async(synthesizer.synthesize(query_input, responses, consensus_metrics))

                # Log Telemetry to DuckDB
                run_id = telemetry.log_query_run(final_artifact)
                st.session_state["latest_run_id"] = run_id

                status.update(label="✅ Consilium Consensus Complete!", state="complete", expanded=False)

            # Store result in session state
            st.session_state["latest_artifact"] = final_artifact

        # Render Results if available in session state
        if "latest_artifact" in st.session_state:
            artifact = st.session_state["latest_artifact"]

            st.markdown("---")
            st.subheader("📊 Consensus Executive Brief")

            valid_count = len([r for r in artifact.responses if r.status == "success"])
            if valid_count < 2:
                st.warning("⚠️ **Warning: Insufficient Model Responses!** Only 1 model returned a response. Zero inter-model consensus validation is possible.")

            col_metric, col_outliers, col_vault = st.columns([2, 2, 2])
            with col_metric:
                st.metric(
                    label="Mathematical Consensus Score",
                    value=f"{artifact.consensus_score:.1f}%",
                    delta="High Agreement" if (artifact.consensus_score >= 75.0 and valid_count >= 2) else ("Insufficient Data" if valid_count < 2 else "Contradictions Detected"),
                )

            with col_outliers:
                outliers = [r.model_name for r in artifact.responses if r.status == "error"]
                st.metric(
                    label="Outlier / Failed Models",
                    value=len(outliers),
                    delta=f"{len(outliers)} flagged" if outliers else "Zero outliers",
                    delta_color="inverse",
                )

            with col_vault:
                exporter = ObsidianExporter()
                if st.button("📥 Export Note to Obsidian Vault", type="secondary", use_container_width=True):
                    saved_path = exporter.export_artifact(artifact, vault_path=vault_path)
                    st.success(f"✅ Note exported to: `{saved_path}`")

            # Feedback Rating Buttons
            st.markdown("**Rate this consensus brief:**")
            fb_col1, fb_col2, _ = st.columns([1, 1, 4])
            with fb_col1:
                if st.button("👍 Accurate", key="btn_pos", use_container_width=True):
                    if "latest_run_id" in st.session_state:
                        telemetry.update_user_feedback(st.session_state["latest_run_id"], rating=1)
                        st.success("Feedback recorded! 👍")
            with fb_col2:
                if st.button("👎 Contradictory", key="btn_neg", use_container_width=True):
                    if "latest_run_id" in st.session_state:
                        telemetry.update_user_feedback(st.session_state["latest_run_id"], rating=-1)
                        st.warning("Feedback recorded! 👎")

            col_left, col_right = st.columns([1, 1])

            with col_left:
                st.markdown("### ✅ Unanimous Points of Agreement")
                if artifact.agreement_points:
                    for pt in artifact.agreement_points:
                        st.markdown(f"- {pt}")
                else:
                    st.info("No explicit agreement points recorded.")

                st.markdown("### ⚠️ Contradiction & Disagreement Audit Log")
                if artifact.contradictions:
                    for c in artifact.contradictions:
                        st.warning(f"**📌 {c.topic}:** {c.description}")
                else:
                    st.success("Zero explicit contradictions detected across model ensemble.")

            with col_right:
                st.markdown("### 📊 Consensus Process Diagram")
                if artifact.mermaid_code:
                    st.code(artifact.mermaid_code, language="mermaid")
                else:
                    st.info("No diagram code generated.")

            st.markdown("---")
            st.markdown("### 🔍 Individual Model Responses")
            for resp in artifact.responses:
                with st.expander(f"🤖 {resp.model_name} (Status: {resp.status}, Latency: {resp.latency_ms:.1f}ms)"):
                    st.text_area(f"Raw Output - {resp.model_name}", value=resp.response_text, height=150, disabled=True)

    # ==========================================
    # TAB 2: Audit History & Telemetry Console
    # ==========================================
    with tab2:
        st.subheader("📊 Execution Audit Logs & Analytics")

        summary = telemetry.get_telemetry_summary()
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        with col1:
            st.metric("Total Queries", summary["total_queries"])
        with col2:
            st.metric("Avg Consensus Score", f"{summary['avg_consensus_score']:.1f}%")
        with col3:
            st.metric("Total Tokens", summary["total_tokens"])
        with col4:
            st.metric("Est. USD Cost", f"${summary['total_cost_usd']:.4f}")
        with col5:
            st.metric("Avg Latency", f"{summary['avg_latency_ms']:.0f} ms")
        with col6:
            st.metric("User Approval Rate", f"{summary.get('satisfaction_rate_percentage', 100.0):.1f}%")

        st.markdown("---")
        st.markdown("### 📜 Query Execution History")
        history = telemetry.get_audit_history(limit=50)

        if history:
            st.dataframe(history, use_container_width=True)
        else:
            st.info("No query logs recorded in DuckDB yet. Run a query in Tab 1 to generate telemetry.")


if __name__ == "__main__":
    main()
