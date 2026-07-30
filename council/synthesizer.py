"""
LLM-as-a-Judge Qualitative Synthesizer Module for AI Consilium
"""

import json
import re
import logging
from typing import List, Optional
import litellm

from council.schemas import (
    ConsiliumQueryInput,
    ModelResponsePayload,
    ConsensusMetrics,
    ContradictionItem,
    ConsiliumFinalArtifact,
)

logger = logging.getLogger(__name__)

JUDGE_FALLBACK_CHAIN = [
    "gemini/gemini-2.5-flash",
    "gpt-4o",
    "claude-3-5-haiku-20241022",
    "openrouter/google/gemma-4-31b-it:free",
]


class LLMJudgeSynthesizer:
    """Synthesizer module using a lead LLM to evaluate multi-model consensus and contradictions."""

    def __init__(self, default_lead_model: str = "gemini/gemini-2.5-flash", timeout: float = 30.0):
        self.default_lead_model = default_lead_model
        self.timeout = timeout
        litellm.suppress_debug_info = True

    def _build_synthesis_prompt(
        self,
        query_input: ConsiliumQueryInput,
        responses: List[ModelResponsePayload],
        consensus_metrics: ConsensusMetrics,
    ) -> List[dict]:
        """Construct structured evaluation prompt for the lead LLM judge."""
        valid_responses = [r for r in responses if r.status == "success"]

        responses_formatted = "\n\n".join([
            f"=== Model: {r.model_name} (Latency: {r.latency_ms:.1f}ms) ===\n{r.response_text}"
            for r in valid_responses
        ])

        outliers_str = ", ".join(consensus_metrics.outlier_models) if consensus_metrics.outlier_models else "None"

        system_instruction = (
            "You are AI Consilium's Chief Research Judge. Your job is to cross-examine multiple frontier LLM responses, "
            "synthesize unanimous consensus points, identify explicit contradictions, generate a clean Mermaid.js diagram "
            "(architecture diagram, sequence diagram, or flowchart), suggest a human-readable title, and assign 2-4 tags.\n"
            "Respond ONLY with valid JSON matching this exact structure:\n"
            "{\n"
            '  "agreement_points": ["point 1", "point 2"],\n'
            '  "contradictions": [\n'
            '    {"topic": "topic name", "description": "why they contradict", "conflicting_models": ["model1", "model2"]}\n'
            "  ],\n"
            '  "mermaid_code": "graph TD\\n  A[Topic] --> B[Consensus]",\n'
            '  "obsidian_title": "2026-07-25-topic-name",\n'
            '  "tags": ["tag1", "tag2"]\n'
            "}"
        )

        user_content = (
            f"User Research Query: {query_input.query}\n\n"
            f"Calculated Embedding Consensus Score: {consensus_metrics.consensus_score:.1f}%\n"
            f"Flagged Statistical Outliers: {outliers_str}\n\n"
            f"Model Responses to Evaluate:\n{responses_formatted}"
        )

        return [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_content},
        ]

    def _clean_json_response(self, text: str) -> dict:
        """Clean markdown wrapping and parse raw LLM JSON response."""
        cleaned = text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except Exception:
            # Fallback non-greedy regex search for JSON object inside braces
            match = re.search(r"(\{.*?\})", cleaned, re.DOTALL)
            if match:
                return json.loads(match.group(1))
            raise ValueError(f"Could not parse valid JSON from synthesis response: {text[:100]}...")

    async def synthesize(
        self,
        query_input: ConsiliumQueryInput,
        responses: List[ModelResponsePayload],
        consensus_metrics: ConsensusMetrics,
        lead_model: Optional[str] = None,
    ) -> ConsiliumFinalArtifact:
        """
        Execute qualitative synthesis via lead LLM judge and return validated ConsiliumFinalArtifact.
        Attempts models in JUDGE_FALLBACK_CHAIN sequentially if lead model fails.
        """
        candidate_models = [lead_model] if lead_model else [self.default_lead_model] + [
            m for m in JUDGE_FALLBACK_CHAIN if m != self.default_lead_model
        ]

        messages = self._build_synthesis_prompt(query_input, responses, consensus_metrics)
        last_error = None

        for model in candidate_models:
            try:
                res = await litellm.acompletion(
                    model=model,
                    messages=messages,
                    response_format={"type": "json_object"},
                    timeout=self.timeout,
                )

                raw_text = res.choices[0].message.content or "{}"
                parsed = self._clean_json_response(raw_text)

                contradiction_objs = [
                    ContradictionItem(
                        topic=str(c.get("topic", "General")),
                        description=str(c.get("description", "")),
                        conflicting_models=list(c.get("conflicting_models", [])),
                    )
                    for c in parsed.get("contradictions", [])
                ]

                return ConsiliumFinalArtifact(
                    query=query_input.query,
                    consensus_score=consensus_metrics.consensus_score,
                    agreement_points=list(parsed.get("agreement_points", [])),
                    contradictions=contradiction_objs,
                    mermaid_code=str(parsed.get("mermaid_code", "")),
                    obsidian_title=str(parsed.get("obsidian_title", "consensus-research")),
                    tags=list(parsed.get("tags", ["consensus", "research"])),
                    responses=responses,
                )
            except Exception as e:
                logger.warning(f"Synthesis failed with judge model {model}: {e}. Trying fallback...")
                last_error = e

        # Heuristic fallback if all judge models fail
        logger.error(f"All LLM judge models in chain failed ({last_error}). Using heuristic fallback.")
        valid_responses = [r for r in responses if r.status == "success"]
        fallback_agreements = [f"Synthesized answer across {len(valid_responses)} models."]

        fallback_mermaid = (
            "graph TD\n"
            f"  Q[\"{query_input.query[:30]}...\"] --> C[\"Consensus: {consensus_metrics.consensus_score}%\"]\n"
        )

        return ConsiliumFinalArtifact(
            query=query_input.query,
            consensus_score=consensus_metrics.consensus_score,
            agreement_points=fallback_agreements,
            contradictions=[],
            mermaid_code=fallback_mermaid,
            obsidian_title="consensus-research-report",
            tags=["consensus", "research"],
            responses=responses,
        )
