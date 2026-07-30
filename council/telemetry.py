"""
DuckDB Telemetry & Audit Query Logger for AI Consilium
"""

import json
import uuid
import datetime
import logging
from typing import List, Dict, Any, Optional
import duckdb

from council.schemas import ConsiliumFinalArtifact

logger = logging.getLogger(__name__)


class DuckDBTelemetryLogger:
    """Telemetry and audit query logger backed by embedded DuckDB."""

    def __init__(self, db_path: str = "ai_consilium.duckdb"):
        self.db_path = db_path
        self.conn = duckdb.connect(db_path)
        self._init_database()

    def _init_database(self) -> None:
        """Create query_logs table if not exists."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS query_logs (
                run_id VARCHAR PRIMARY KEY,
                timestamp TIMESTAMP,
                query VARCHAR,
                consensus_score FLOAT,
                num_models INTEGER,
                prompt_tokens INTEGER,
                completion_tokens INTEGER,
                total_tokens INTEGER,
                total_cost_usd FLOAT,
                avg_latency_ms FLOAT,
                model_latencies VARCHAR,
                num_contradictions INTEGER,
                user_rating INTEGER DEFAULT 0,
                user_feedback_comment VARCHAR DEFAULT ''
            );
        """)
        # Safe migration if table exists without new columns
        try:
            self.conn.execute("ALTER TABLE query_logs ADD COLUMN user_rating INTEGER DEFAULT 0;")
        except Exception:
            pass
        try:
            self.conn.execute("ALTER TABLE query_logs ADD COLUMN user_feedback_comment VARCHAR DEFAULT '';")
        except Exception:
            pass

    def log_query_run(self, artifact: ConsiliumFinalArtifact) -> str:
        """
        Record detailed telemetry for an execution run.
        Returns the unique run_id.
        """
        run_id = f"run-{uuid.uuid4().hex[:12]}"
        now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        responses = artifact.responses or []
        num_models = len(responses)

        prompt_tokens = sum(r.prompt_tokens for r in responses)
        completion_tokens = sum(r.completion_tokens for r in responses)
        total_tokens = prompt_tokens + completion_tokens

        total_cost_usd = sum(r.cost_usd for r in responses)
        latencies = [r.latency_ms for r in responses if r.latency_ms > 0]
        avg_latency = float(sum(latencies) / len(latencies)) if latencies else 0.0

        model_latencies_dict = {r.model_name: r.latency_ms for r in responses}
        model_latencies_json = json.dumps(model_latencies_dict)

        num_contradictions = len(artifact.contradictions) if artifact.contradictions else 0

        self.conn.execute(
            """
            INSERT INTO query_logs (
                run_id, timestamp, query, consensus_score, num_models,
                prompt_tokens, completion_tokens, total_tokens, total_cost_usd,
                avg_latency_ms, model_latencies, num_contradictions
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                now_str,
                artifact.query,
                float(artifact.consensus_score),
                num_models,
                prompt_tokens,
                completion_tokens,
                total_tokens,
                float(total_cost_usd),
                float(avg_latency),
                model_latencies_json,
                num_contradictions,
            ),
        )

        logger.info(f"Logged query execution run {run_id} to DuckDB query_logs.")
        return run_id

    def update_user_feedback(self, run_id: str, rating: int, comment: str = "") -> None:
        """Update user rating (+1 / -1) and optional comment for a run."""
        self.conn.execute(
            """
            UPDATE query_logs
            SET user_rating = ?, user_feedback_comment = ?
            WHERE run_id = ?
            """,
            (rating, comment, run_id),
        )
        logger.info(f"Updated user feedback for run {run_id}: rating={rating}")

    def get_audit_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve historical query execution logs ordered by timestamp descending."""
        res = self.conn.execute(
            """
            SELECT run_id, timestamp, query, consensus_score, num_models,
                   total_tokens, total_cost_usd, avg_latency_ms, model_latencies, num_contradictions,
                   user_rating, user_feedback_comment
            FROM query_logs
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        history = []
        for run_id, ts, q, score, num_m, tokens, cost, latency, latencies_json, contradictions, rating, comment in res:
            history.append({
                "run_id": run_id,
                "timestamp": str(ts),
                "query": q,
                "consensus_score": float(score),
                "num_models": num_m,
                "total_tokens": tokens,
                "total_cost_usd": float(cost),
                "avg_latency_ms": float(latency),
                "model_latencies": json.loads(latencies_json) if latencies_json else {},
                "num_contradictions": contradictions,
                "user_rating": rating or 0,
                "user_feedback_comment": comment or "",
            })
        return history

    def get_telemetry_summary(self) -> Dict[str, Any]:
        """Aggregate total queries, average consensus score, tokens, cost, latency, and satisfaction rate."""
        res = self.conn.execute(
            """
            SELECT COUNT(*),
                   COALESCE(AVG(consensus_score), 0.0),
                   COALESCE(SUM(total_tokens), 0),
                   COALESCE(SUM(total_cost_usd), 0.0),
                   COALESCE(AVG(avg_latency_ms), 0.0),
                   COALESCE(SUM(CASE WHEN user_rating > 0 THEN 1 ELSE 0 END), 0),
                   COALESCE(SUM(CASE WHEN user_rating != 0 THEN 1 ELSE 0 END), 0)
            FROM query_logs
            """
        ).fetchone()

        total_queries, avg_score, total_tokens, total_cost, avg_latency, pos_ratings, total_rated = res
        satisfaction_rate = round((pos_ratings / total_rated) * 100.0, 1) if total_rated > 0 else 100.0

        return {
            "total_queries": total_queries,
            "avg_consensus_score": round(float(avg_score), 2),
            "total_tokens": int(total_tokens),
            "total_cost_usd": round(float(total_cost), 6),
            "avg_latency_ms": round(float(avg_latency), 2),
            "satisfaction_rate_percentage": satisfaction_rate,
            "total_rated_queries": total_rated,
        }

    def close(self) -> None:
        """Close database connection."""
        self.conn.close()
