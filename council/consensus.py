"""
Hybrid Embedding Consensus Matrix & Outlier Detector for AI Consilium
"""

import logging
from typing import List, Dict, Optional
import numpy as np
from sentence_transformers import SentenceTransformer

from council.schemas import ModelResponsePayload, ConsensusMetrics

logger = logging.getLogger(__name__)


class ConsensusEngine:
    """Engine for computing pairwise embedding similarity matrices and statistical consensus scores."""

    def __init__(self, embedding_model_name: str = "all-MiniLM-L6-v2"):
        self.embedding_model_name = embedding_model_name
        self.model = SentenceTransformer(embedding_model_name)

    def compute_consensus(
        self,
        responses: List[ModelResponsePayload],
        outlier_threshold: float = 0.65,
    ) -> ConsensusMetrics:
        """
        Calculate pairwise cosine embedding similarities, average consensus percentage (0-100%),
        and identify statistical outlier models using relative ensemble distance.
        """
        # Filter for successful responses with non-empty text
        valid_responses = [r for r in responses if r.status == "success" and r.response_text.strip()]

        if not valid_responses:
            logger.warning("No successful model responses to compute consensus.")
            return ConsensusMetrics(
                consensus_score=0.0,
                outlier_models=[],
                pairwise_similarity={},
            )

        if len(valid_responses) == 1:
            model_name = valid_responses[0].model_name
            return ConsensusMetrics(
                consensus_score=100.0,
                outlier_models=[],
                pairwise_similarity={model_name: {model_name: 1.0}},
            )

        # Generate embeddings for valid responses
        texts = [r.response_text for r in valid_responses]
        model_names = [r.model_name for r in valid_responses]

        embeddings = self.model.encode(texts, convert_to_numpy=True)

        # Compute normalized cosine similarity matrix
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1e-10
        normalized_embeddings = embeddings / norms
        similarity_matrix = np.dot(normalized_embeddings, normalized_embeddings.T)
        similarity_matrix = np.clip(similarity_matrix, 0.0, 1.0)

        n = len(model_names)
        pairwise_dict: Dict[str, Dict[str, float]] = {}

        for i in range(n):
            model_i = model_names[i]
            pairwise_dict[model_i] = {}
            for j in range(n):
                model_j = model_names[j]
                pairwise_dict[model_i][model_j] = round(float(similarity_matrix[i, j]), 4)

        # Calculate average off-diagonal similarity score
        off_diagonal_indices = np.triu_indices(n, k=1)
        if len(off_diagonal_indices[0]) > 0:
            avg_similarity = float(np.mean(similarity_matrix[off_diagonal_indices]))
        else:
            avg_similarity = 1.0

        consensus_score = round(avg_similarity * 100.0, 2)

        # Detect outlier models using relative ensemble distance
        mean_similarities = []
        for i in range(n):
            other_sims = [similarity_matrix[i, j] for j in range(n) if i != j]
            mean_similarities.append(float(np.mean(other_sims)) if other_sims else 1.0)

        max_mean_sim = max(mean_similarities)
        median_mean_sim = float(np.median(mean_similarities))

        outlier_models: List[str] = []
        for i in range(n):
            m_sim = mean_similarities[i]
            # A model is an outlier if its average similarity to peers is significantly lower
            # than the ensemble median or configured threshold and max peer similarity
            is_relative_outlier = (m_sim < (median_mean_sim - 0.15)) or (m_sim < outlier_threshold and (max_mean_sim - m_sim) >= 0.15)
            if is_relative_outlier:
                outlier_models.append(model_names[i])

        return ConsensusMetrics(
            consensus_score=consensus_score,
            outlier_models=outlier_models,
            pairwise_similarity=pairwise_dict,
        )
