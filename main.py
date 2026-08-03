"""
Standalone Command-Line CLI Entrypoint for AI Consilium
"""

import sys
import argparse
import asyncio
import json
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from council.schemas import ConsiliumQueryInput
from council.providers import LLMProviderEngine
from council.consensus import ConsensusEngine
from council.synthesizer import LLMJudgeSynthesizer
from council.exporter import ObsidianExporter
from council.telemetry import DuckDBTelemetryLogger

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


def parse_args(args=None):
    """Parse command-line flags."""
    parser = argparse.ArgumentParser(
        description="AI Consilium — Dual-Engine Consensus Research CLI"
    )
    parser.add_argument(
        "--query",
        "-q",
        type=str,
        required=True,
        help="Research query prompt text",
    )
    parser.add_argument(
        "--free-tier",
        action="store_true",
        help="Route requests through OpenRouter's 100% free model tier (:free)",
    )
    parser.add_argument(
        "--rag",
        action="store_true",
        help="Ground research query with past ingested notes from ai_consilium.duckdb",
    )
    parser.add_argument(
        "--export",
        "-e",
        action="store_true",
        help="Export formatted research note directly into Obsidian vault",
    )
    parser.add_argument(
        "--vault-path",
        type=str,
        default=None,
        help="Custom destination vault directory for --export",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output full JSON ConsiliumFinalArtifact payload to stdout",
    )
    return parser.parse_args(args)


async def run_cli(args_parsed):
    """Execute consensus pipeline via CLI."""
    query_text = args_parsed.query.strip()
    if not query_text:
        print("Error: Query string cannot be empty.", file=sys.stderr)
        sys.exit(1)

    context_chunks = []
    if args_parsed.rag:
        try:
            from council.rag import DuckDBRAGEngine
            rag_engine = DuckDBRAGEngine(db_path="ai_consilium.duckdb")
            vault_results = rag_engine.search(query_text, top_k=3)
            total_char_budget = 10000
            current_chars = 0
            for r in vault_results:
                snippet_title = r['title']
                snippet_content = r['content'].strip()

                # Strip Mermaid code & raw provider response blocks to maximize consensus density
                if "## 📊 Consensus Architecture" in snippet_content:
                    snippet_content = snippet_content.split("## 📊 Consensus Architecture")[0].strip()
                elif "## 🔍 Multi-Model Raw Provider Responses" in snippet_content:
                    snippet_content = snippet_content.split("## 🔍 Multi-Model Raw Provider Responses")[0].strip()

                formatted_chunk = f"[Vault Note: {snippet_title}]\n{snippet_content}"
                if current_chars + len(formatted_chunk) > total_char_budget:
                    remaining_budget = total_char_budget - current_chars
                    if remaining_budget > 100:
                        truncated_content = snippet_content[:remaining_budget - 50] + "... [Truncated for Context Budget]"
                        context_chunks.append(f"[Vault Note: {snippet_title}]\n{truncated_content}")
                    break
                else:
                    context_chunks.append(formatted_chunk)
                    current_chars += len(formatted_chunk)
            rag_engine.close()
        except Exception as e:
            logger.warning(f"CLI RAG retrieval warning: {e}")

    query_input = ConsiliumQueryInput(query=query_text, context_chunks=context_chunks)

    # Step 1: Multi-Model Async Querying
    provider_engine = LLMProviderEngine(default_timeout=35.0)
    responses = await provider_engine.query_concurrently(
        query_input, use_free_tier=args_parsed.free_tier
    )

    # Step 2: Mathematical Consensus Matrix & Outlier Detection
    consensus_engine = ConsensusEngine()
    consensus_metrics = consensus_engine.compute_consensus(responses)

    # Step 3: LLM Judge Qualitative Synthesis
    synthesizer = LLMJudgeSynthesizer()
    artifact = await synthesizer.synthesize(query_input, responses, consensus_metrics)

    # Step 4: Telemetry Logging
    telemetry = DuckDBTelemetryLogger()
    telemetry.log_query_run(artifact)
    telemetry.close()

    # Step 5: Optional Obsidian Export
    exported_path = None
    if args_parsed.export:
        exporter = ObsidianExporter(default_vault_path=args_parsed.vault_path)
        exported_path = exporter.export_artifact(artifact, vault_path=args_parsed.vault_path)

    # Step 6: Terminal Output
    if args_parsed.json:
        print(artifact.model_dump_json(indent=2))
    else:
        print("\n" + "=" * 60)
        print(f"🏛️  AI CONSILIUM EXECUTIVE BRIEF: {artifact.query}")
        print("=" * 60)
        print(f"📊 Consensus Score: {artifact.consensus_score:.1f}%")
        print(f"🤖 Models Queried: {len(artifact.responses)}")
        print("\n✅ Points of Agreement:")
        for pt in artifact.agreement_points:
            print(f"  - {pt}")

        if artifact.contradictions:
            print("\n⚠️  Contradiction Audit Log:")
            for c in artifact.contradictions:
                print(f"  - [{c.topic}]: {c.description}")
        else:
            print("\n✅ Zero Contradictions Detected.")

        if exported_path:
            print(f"\n📥 Note Exported: {exported_path}")
        print("=" * 60 + "\n")


def main():
    args = parse_args()
    asyncio.run(run_cli(args))


if __name__ == "__main__":
    main()
