import pytest
from evaluate_retrieval import calculate_hit_rate, calculate_mrr, run_benchmark_eval


def test_hit_rate_and_mrr_calculations():
    results = [
        [{"id": "doc1"}, {"id": "doc2"}],  # expected doc1 -> rank 1
        [{"id": "doc3"}, {"id": "doc2"}],  # expected doc2 -> rank 2
        [{"id": "doc4"}, {"id": "doc5"}],  # expected doc6 -> not found (rank infinity)
    ]
    targets = ["doc1", "doc2", "doc6"]

    # Hit Rate = 2 / 3 = 66.67%
    hit_rate = calculate_hit_rate(results, targets)
    assert hit_rate == 66.67

    # MRR = (1/1 + 1/2 + 0) / 3 = (1.5) / 3 = 0.5000
    mrr = calculate_mrr(results, targets)
    assert mrr == 0.5000


def test_run_benchmark_eval():
    metrics = run_benchmark_eval(top_k=3)
    assert metrics["total_test_cases"] == 5
    assert metrics["hit_rate_percentage"] >= 80.0
    assert metrics["mrr_score"] > 0.70
