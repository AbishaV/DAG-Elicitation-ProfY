"""
Evaluation — Structural Hamming Distance and Edge-Level Metrics
================================================================
Chapter 12: LLMs as DAG Elicitation Engines

Computes formal evaluation metrics comparing an elicited DAG against
the ground truth reference DAG.

Primary metric: Structural Hamming Distance (SHD)
    Counts three types of errors:
    - Missing edges (in ground truth but not in elicited)
    - Extra edges (in elicited but not in ground truth)
    - Reversed edges (present in both but wrong direction)
    Lower SHD = better structural recovery.

Secondary metrics:
    - Precision: of edges the agent proposed, how many are correct?
    - Recall: of edges in ground truth, how many did the agent find?
    - F1: harmonic mean of precision and recall
    - Adjacency accuracy: ignoring direction, did the agent find the right pairs?

Usage:
    from evaluation import evaluate_dag, print_evaluation_report

    report = evaluate_dag(elicited_dag, ground_truth_dag)
    print_evaluation_report(report)
"""

import networkx as nx
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Evaluation report
# ---------------------------------------------------------------------------

@dataclass
class EvaluationReport:
    """Complete evaluation of an elicited DAG against ground truth."""

    # SHD components
    missing_edges: list = field(default_factory=list)
    extra_edges: list = field(default_factory=list)
    reversed_edges: list = field(default_factory=list)
    correct_edges: list = field(default_factory=list)

    # SHD score
    shd: int = 0

    # Edge-level metrics (directed)
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0

    # Adjacency metrics (ignoring direction)
    adjacency_precision: float = 0.0
    adjacency_recall: float = 0.0
    adjacency_f1: float = 0.0

    # Counts
    total_in_ground_truth: int = 0
    total_in_elicited: int = 0
    total_correct: int = 0
    total_missing: int = 0
    total_extra: int = 0
    total_reversed: int = 0


# ---------------------------------------------------------------------------
# Core evaluation function
# ---------------------------------------------------------------------------

def evaluate_dag(
    elicited: nx.DiGraph,
    ground_truth: nx.DiGraph
) -> EvaluationReport:
    """
    Evaluate an elicited DAG against the ground truth reference.

    Parameters
    ----------
    elicited : nx.DiGraph
        The DAG produced by the elicitation process
    ground_truth : nx.DiGraph
        The reference DAG to evaluate against

    Returns
    -------
    EvaluationReport
        Complete evaluation with SHD, precision, recall, F1,
        and adjacency metrics
    """
    report = EvaluationReport()

    edges_elicited = set(elicited.edges())
    edges_truth = set(ground_truth.edges())

    # Correct: in both, same direction
    correct = edges_elicited & edges_truth

    # Extra: in elicited but not in ground truth
    extra_candidates = edges_elicited - edges_truth

    # Missing: in ground truth but not in elicited
    missing_candidates = edges_truth - edges_elicited

    # Reversed: an "extra" edge whose reverse exists in ground truth
    reversed_edges = set()
    truly_extra = set()
    for u, v in extra_candidates:
        if (v, u) in edges_truth:
            reversed_edges.add((u, v))
        else:
            truly_extra.add((u, v))

    # Remove reversed from missing (they're accounted for)
    truly_missing = set()
    for u, v in missing_candidates:
        if (v, u) not in edges_elicited:
            truly_missing.add((u, v))

    # Store in report
    report.correct_edges = sorted(correct)
    report.missing_edges = sorted(truly_missing)
    report.extra_edges = sorted(truly_extra)
    report.reversed_edges = sorted(reversed_edges)

    report.total_correct = len(correct)
    report.total_missing = len(truly_missing)
    report.total_extra = len(truly_extra)
    report.total_reversed = len(reversed_edges)
    report.total_in_ground_truth = len(edges_truth)
    report.total_in_elicited = len(edges_elicited)

    # SHD = missing + extra + reversed
    report.shd = report.total_missing + report.total_extra + report.total_reversed

    # Directed edge precision and recall
    if len(edges_elicited) > 0:
        report.precision = len(correct) / len(edges_elicited)
    else:
        report.precision = 0.0

    if len(edges_truth) > 0:
        report.recall = len(correct) / len(edges_truth)
    else:
        report.recall = 0.0

    if report.precision + report.recall > 0:
        report.f1 = (
            2 * report.precision * report.recall
            / (report.precision + report.recall)
        )
    else:
        report.f1 = 0.0

    # Adjacency metrics (ignoring direction)
    adj_elicited = set()
    for u, v in edges_elicited:
        adj_elicited.add(frozenset({u, v}))

    adj_truth = set()
    for u, v in edges_truth:
        adj_truth.add(frozenset({u, v}))

    adj_correct = adj_elicited & adj_truth

    if len(adj_elicited) > 0:
        report.adjacency_precision = len(adj_correct) / len(adj_elicited)
    else:
        report.adjacency_precision = 0.0

    if len(adj_truth) > 0:
        report.adjacency_recall = len(adj_correct) / len(adj_truth)
    else:
        report.adjacency_recall = 0.0

    if report.adjacency_precision + report.adjacency_recall > 0:
        report.adjacency_f1 = (
            2 * report.adjacency_precision * report.adjacency_recall
            / (report.adjacency_precision + report.adjacency_recall)
        )
    else:
        report.adjacency_f1 = 0.0

    return report


# ---------------------------------------------------------------------------
# Print report
# ---------------------------------------------------------------------------

def print_evaluation_report(report: EvaluationReport) -> None:
    """Print a formatted evaluation report."""
    print("=" * 60)
    print("EVALUATION REPORT")
    print("=" * 60)

    print(f"\nStructural Hamming Distance (SHD): {report.shd}")
    print(f"  Missing edges:  {report.total_missing}")
    print(f"  Extra edges:    {report.total_extra}")
    print(f"  Reversed edges: {report.total_reversed}")

    print(f"\nDirected Edge Metrics:")
    print(f"  Precision: {report.precision:.3f}")
    print(f"  Recall:    {report.recall:.3f}")
    print(f"  F1:        {report.f1:.3f}")

    print(f"\nAdjacency Metrics (ignoring direction):")
    print(f"  Precision: {report.adjacency_precision:.3f}")
    print(f"  Recall:    {report.adjacency_recall:.3f}")
    print(f"  F1:        {report.adjacency_f1:.3f}")

    print(f"\nEdge Counts:")
    print(f"  Ground truth: {report.total_in_ground_truth}")
    print(f"  Elicited:     {report.total_in_elicited}")
    print(f"  Correct:      {report.total_correct}")

    if report.correct_edges:
        print(f"\nCorrect edges:")
        for u, v in report.correct_edges:
            print(f"  {u} -> {v}")

    if report.missing_edges:
        print(f"\nMissing edges:")
        for u, v in report.missing_edges:
            print(f"  {u} -> {v}")

    if report.extra_edges:
        print(f"\nExtra (hallucinated) edges:")
        for u, v in report.extra_edges:
            print(f"  {u} -> {v}")

    if report.reversed_edges:
        print(f"\nReversed edges:")
        for u, v in report.reversed_edges:
            print(f"  {u} -> {v}  (should be {v} -> {u})")

    print()


# ---------------------------------------------------------------------------
# Convenience: evaluate from transcript
# ---------------------------------------------------------------------------

def evaluate_transcript(
    transcript_path: str,
    ground_truth: nx.DiGraph
) -> EvaluationReport:
    """
    Build a DAG from a saved transcript and evaluate it against ground truth.

    Parameters
    ----------
    transcript_path : str
        Path to the saved ProfY transcript JSON
    ground_truth : nx.DiGraph
        The reference DAG

    Returns
    -------
    EvaluationReport
    """
    from dag_builder import build_dag_from_transcript

    elicited, validation = build_dag_from_transcript(transcript_path)
    return evaluate_dag(elicited, ground_truth)


# ---------------------------------------------------------------------------
# Stress test: what happens when we deliberately break the DAG
# ---------------------------------------------------------------------------

def sensitivity_test(
    base_dag: nx.DiGraph,
    ground_truth: nx.DiGraph,
    edges_to_remove: list[tuple] = None,
    edges_to_add: list[tuple] = None,
    edges_to_reverse: list[tuple] = None,
) -> dict:
    """
    Run a sensitivity test by modifying the elicited DAG and re-evaluating.

    This shows how SHD changes when specific edges are added, removed,
    or reversed. Useful for demonstrating the impact of individual
    edge decisions.

    Parameters
    ----------
    base_dag : nx.DiGraph
        The starting DAG to modify
    ground_truth : nx.DiGraph
        The reference DAG
    edges_to_remove : list[tuple], optional
        Edges to remove from base_dag
    edges_to_add : list[tuple], optional
        Edges to add to base_dag
    edges_to_reverse : list[tuple], optional
        Edges to reverse in base_dag (remove u->v, add v->u)

    Returns
    -------
    dict with keys: baseline_report, modified_report, changes
    """
    # Baseline
    baseline_report = evaluate_dag(base_dag, ground_truth)

    # Create modified copy
    modified = base_dag.copy()

    changes = []

    if edges_to_remove:
        for u, v in edges_to_remove:
            if modified.has_edge(u, v):
                modified.remove_edge(u, v)
                changes.append(f"Removed: {u} -> {v}")

    if edges_to_add:
        for u, v in edges_to_add:
            modified.add_edge(u, v)
            if not nx.is_directed_acyclic_graph(modified):
                modified.remove_edge(u, v)
                changes.append(f"Skipped (cycle): {u} -> {v}")
            else:
                changes.append(f"Added: {u} -> {v}")

    if edges_to_reverse:
        for u, v in edges_to_reverse:
            if modified.has_edge(u, v):
                modified.remove_edge(u, v)
                modified.add_edge(v, u)
                if not nx.is_directed_acyclic_graph(modified):
                    modified.remove_edge(v, u)
                    modified.add_edge(u, v)
                    changes.append(f"Skipped (cycle): reverse {u} -> {v}")
                else:
                    changes.append(f"Reversed: {u} -> {v} to {v} -> {u}")

    modified_report = evaluate_dag(modified, ground_truth)

    return {
        "baseline_report": baseline_report,
        "modified_report": modified_report,
        "changes": changes,
        "shd_change": modified_report.shd - baseline_report.shd,
    }


def print_sensitivity_test(result: dict) -> None:
    """Print a sensitivity test comparison."""
    print("=" * 60)
    print("SENSITIVITY TEST")
    print("=" * 60)

    print(f"\nChanges applied:")
    for c in result["changes"]:
        print(f"  {c}")

    print(f"\nBaseline SHD: {result['baseline_report'].shd}")
    print(f"Modified SHD: {result['modified_report'].shd}")
    print(f"SHD change:   {result['shd_change']:+d}")

    print(f"\nBaseline F1:  {result['baseline_report'].f1:.3f}")
    print(f"Modified F1:  {result['modified_report'].f1:.3f}")

    print()


# ---------------------------------------------------------------------------
# Main (for testing)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    sys.path.insert(0, "src")

    from ground_truth_dag import build_ground_truth_dag
    from dag_builder import build_dag_from_transcript

    ground_truth = build_ground_truth_dag()

    # Test 1: Perfect match (transcript matches ground truth exactly)
    print("Test 1: Evaluate transcript against ground truth (perfect match)")
    print("-" * 40)

    elicited, _ = build_dag_from_transcript("transcripts/supply_chain_socratic.json")
    report = evaluate_dag(elicited, ground_truth)
    print_evaluation_report(report)

    # Test 2: Imperfect DAG (remove 2 edges, add 1 wrong, reverse 1)
    print("Test 2: Evaluate a deliberately imperfect DAG")
    print("-" * 40)

    imperfect = ground_truth.copy()
    # Remove two edges
    imperfect.remove_edge("fuel_prices", "production_capacity")
    imperfect.remove_edge("supplier_reliability", "order_lead_time")
    # Add a hallucinated edge
    imperfect.add_edge("fuel_prices", "delivery_delays")
    # Reverse an edge
    imperfect.remove_edge("demand_volatility", "order_lead_time")
    imperfect.add_edge("order_lead_time", "demand_volatility")

    report_bad = evaluate_dag(imperfect, ground_truth)
    print_evaluation_report(report_bad)

    # Test 3: Sensitivity test
    print("Test 3: Sensitivity test (remove one contested edge)")
    print("-" * 40)

    sens = sensitivity_test(
        base_dag=elicited,
        ground_truth=ground_truth,
        edges_to_remove=[("fuel_prices", "production_capacity")],
    )
    print_sensitivity_test(sens)

    # Test 4: Sensitivity test (reverse an edge)
    print("Test 4: Sensitivity test (reverse one edge)")
    print("-" * 40)

    sens2 = sensitivity_test(
        base_dag=elicited,
        ground_truth=ground_truth,
        edges_to_reverse=[("inventory_levels", "delivery_delays")],
    )
    print_sensitivity_test(sens2)