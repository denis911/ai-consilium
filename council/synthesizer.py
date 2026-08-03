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
    "o3-mini",
    "anthropic/claude-sonnet-5",
    "xai/grok-4.5",
    "openrouter/google/gemma-3-27b-it:free",
]


def _fix_decision_node(m: re.Match) -> str:
    """Fix decision nodes with unquoted text containing parens or special chars: C{Text (parens)?} -> C{"Text (parens)?"}"""
    node_id = m.group(1)
    content = m.group(2).strip()
    if not (content.startswith('"') and content.endswith('"')):
        content = f'"{content}"'
    return f'{node_id}{{{content}}}'


def _fix_node_parens(m: re.Match) -> str:
    """Fix 'Node(Label containing parens or colons)' pattern to 'Node["Label"]'"""
    node_id = m.group(1)
    content = m.group(2).strip()
    if content.startswith("(") and content.endswith(")"):
        content = content[1:-1]
    if not (content.startswith('"') and content.endswith('"')):
        content = f'"{content}"'
    return f'{node_id}[{content}]'


def _expand_and_nodes(line: str) -> Optional[List[str]]:
    """Expand 'NodeA & NodeB --> NodeC' pattern into individual connections."""
    if " & " in line and "-->" in line:
        parts = line.split("-->")
        if len(parts) == 2:
            left, right = parts[0].strip(), parts[1].strip()
            left_nodes = [n.strip() for n in left.split("&")]
            return [f"  {node} --> {right}" for node in left_nodes]
    return None


def _fix_square_bracket_node(m: re.Match) -> str:
    """Fix square bracket nodes containing parens or special chars: D[Text (parens)] -> D["Text (parens)"]"""
    node_id = m.group(1)
    content = m.group(2).strip()
    if not (content.startswith('"') and content.endswith('"')):
        content = f'"{content}"'
    return f'{node_id}[{content}]'


def _sanitize_mermaid_code(code: str) -> str:
    """Sanitize invalid Mermaid syntax."""
    if not code:
        return ""
    cleaned = code.replace("```mermaid", "").replace("```", "").strip()
    lines = cleaned.split("\n")
    cleaned_lines = []

    for raw_line in lines:
        line = raw_line.replace("Unsupported markdown: list", "Key Factors & Trade-offs")

        # Fix decision nodes
        line = re.sub(r'(\b[A-Za-z0-9_]+)\{([^}]+)\}', _fix_decision_node, line)

        # Fix square bracket nodes with parens or special chars: D[Text (parens)] -> D["Text (parens)"]
        line = re.sub(r'(\b[A-Za-z0-9_]+)\[([^\]]*[\(\)\:\,][^\]]*)\]', _fix_square_bracket_node, line)

        # Fix 'A -- Text --> B' pattern to valid 'A -->|Text| B'
        line = re.sub(r'(\b\w+)\s+--\s+([^\-\>]+)\s+-->\s+(\b\w+)', r'\1 -->|\2| \3', line)

        # Fix 'Node(Label containing parens or colons)' pattern to 'Node["Label"]'
        line = re.sub(r'(\b[A-Za-z0-9_]+)\(([^)]*[\(\:\-][^)]*)\)', _fix_node_parens, line)

        # Fix 'NodeA & NodeB --> NodeC' pattern
        expanded = _expand_and_nodes(line)
        if expanded is not None:
            cleaned_lines.extend(expanded)
            continue

        cleaned_lines.append(line)
    return "\n".join(cleaned_lines)


litellm.suppress_debug_info = True
litellm.turn_off_message_logging = True
litellm.telemetry = False
litellm.set_verbose = False


class LLMJudgeSynthesizer:
    """Synthesizer module using a lead LLM to evaluate multi-model consensus and contradictions."""

    def __init__(self, default_lead_model: str = "gemini/gemini-2.5-flash", timeout: float = 30.0):
        self.default_lead_model = default_lead_model
        self.timeout = timeout
        litellm.suppress_debug_info = True
        litellm.turn_off_message_logging = True
        litellm.telemetry = False
        litellm.set_verbose = False

    def _build_synthesis_prompt(
        self,
        query_input: ConsiliumQueryInput,
        responses: List[ModelResponsePayload],
        consensus_metrics: ConsensusMetrics,
    ) -> List[dict]:
        """Construct structured evaluation prompt for the lead LLM judge."""
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
            '  "mermaid_code": "flowchart TD\\n  A[Topic] --> B[Consensus]",\n'
            '  "obsidian_title": "topic-name",\n'
            '  "tags": ["tag1", "tag2"]\n'
            "}\n"
            "You are an executive AI Consilium Synthesizer. Your job is to analyze individual LLM responses to a query "
            "and synthesize an executive brief. Output strictly valid JSON without any markdown formatting."
        )

        models_data = []
        for r in responses:
            models_data.append({
                "model_name": r.model_name,
                "status": r.status,
                "response_text": r.response_text,
                "latency_ms": r.latency_ms,
            })

        user_payload = {
            "query": query_input.query,
            "consensus_score": consensus_metrics.consensus_score,
            "outlier_models": consensus_metrics.outlier_models,
            "pairwise_similarity": consensus_metrics.pairwise_similarity,
            "model_responses": models_data,
        }

        user_content = (
            f"Analyze the following multi-model responses and consensus metrics:\n\n"
            f"```json\n{json.dumps(user_payload, indent=2)}\n```\n\n"
            "Return a single JSON object with the following exact keys:\n"
            "- \"agreement_points\": list of strings summarizing key points of unanimous consensus\n"
            "- \"contradictions\": list of objects with {\"topic\": string, \"description\": string, \"conflicting_models\": list of strings}\n"
            "- \"mermaid_code\": valid Mermaid.js flowchart code visualizing workflow/trade-offs. MUST follow rules: 1. Start with 'flowchart TD'. 2. Wrap node text in double quotes like A[\"Text (here)\"]. 3. Use A -->|Label| B for labeled arrows.\n"
            "- \"obsidian_title\": recommended note title string (kebab-case)\n"
            "- \"tags\": list of 3-5 relevance tags\n"
        )

        return [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_content},
        ]

    def _extract_outermost_json(self, text: str) -> dict:
        """Extract and parse the outermost JSON object from text, ignoring braces in string literals."""
        depth = 0
        start = None
        in_string = False
        escaped = False

        for i, ch in enumerate(text):
            if ch == '"' and not escaped:
                in_string = not in_string
                continue

            if in_string:
                if ch == '\\':
                    escaped = not escaped
                else:
                    escaped = False
                continue

            # Outside string literals, track brace depth
            if ch == '{':
                if depth == 0:
                    start = i
                depth += 1
            elif ch == '}':
                if depth > 0:
                    depth -= 1
                    if depth == 0 and start is not None:
                        json_candidate = text[start:i + 1]
                        try:
                            return json.loads(json_candidate)
                        except Exception:
                            pass
        raise ValueError(f"Could not parse valid JSON from synthesis response: {text[:100]}...")

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
            return self._extract_outermost_json(cleaned)

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

                mermaid_code = _sanitize_mermaid_code(str(parsed.get("mermaid_code", "")))

                return ConsiliumFinalArtifact(
                    query=query_input.query,
                    consensus_score=consensus_metrics.consensus_score,
                    agreement_points=list(parsed.get("agreement_points", [])),
                    contradictions=contradiction_objs,
                    mermaid_code=mermaid_code,
                    obsidian_title=str(parsed.get("obsidian_title", "consensus-research")),
                    tags=list(parsed.get("tags", ["consensus", "research"])),
                    responses=responses,
                    context_chunks=query_input.context_chunks,
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
            mermaid_code=_sanitize_mermaid_code(fallback_mermaid),
            obsidian_title="consensus-research-fallback",
            tags=["consensus", "fallback"],
            responses=responses,
            context_chunks=query_input.context_chunks,
        )
