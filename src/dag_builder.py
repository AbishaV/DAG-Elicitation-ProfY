"""
DAG Builder — Construct and Validate Causal Graphs from Elicitation Output
===========================================================================
Chapter 12: LLMs as DAG Elicitation Engines

Takes the raw output from ProfY (variables and edges) and builds a
validated networkx DiGraph. Handles structural validation, cycle
detection, and produces a graph ready for SHD evaluation and visualization.

Usage:
    from dag_builder import build_dag_from_result, build_dag_from_transcript

    # From an ElicitationResult object (after running ProfY)
    dag, report = build_dag_from_result(result)

    # From a saved transcript JSON file
    dag, report = build_dag_from_transcript("transcripts/supply_chain_socratic.json")

    # From a manually curated edge list (after Human Decision Node)
    dag, report = build_dag_from_edges(validated_edges)
"""

import json
import networkx as nx
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Validation report
# ---------------------------------------------------------------------------

@dataclass
class DAGValidationReport:
    """Results of structural validation on a built DAG."""
    is_valid: bool = True
    is_acyclic: bool = True
    node_count: int = 0
    edge_count: int = 0
    orphan_nodes: list = field(default_factory=list)
    disconnected_components: int = 0
    cycles_found: list = field(default_factory=list)
    rejected_edges: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    def print_report(self) -> None:
        """Print a human-readable validation summary."""
        print("=" * 60)
        print("DAG VALIDATION REPORT")
        print("=" * 60)
        status = "PASSED" if self.is_valid else "FAILED"
        print(f"Status: {status}")
        print(f"Nodes: {self.node_count}")
        print(f"Edges: {self.edge_count}")
        print(f"Acyclic: {self.is_acyclic}")
        print(f"Disconnected components: {self.disconnected_components}")

        if self.orphan_nodes:
            print(f"\nOrphan nodes (no connections): {self.orphan_nodes}")

        if self.cycles_found:
            print(f"\nCycles detected (edges rejected):")
            for cycle in self.cycles_found:
                print(f"  {cycle}")

        if self.rejected_edges:
            print(f"\nRejected edges:")
            for edge, reason in self.rejected_edges:
                print(f"  {edge[0]} -> {edge[1]}: {reason}")

        if self.warnings:
            print(f"\nWarnings:")
            for w in self.warnings:
                print(f"  {w}")

        print()


# ---------------------------------------------------------------------------
# Core builder
# ---------------------------------------------------------------------------

def build_dag(
    nodes: list[str],
    edges: list[tuple],
    strict: bool = False
) -> tuple[nx.DiGraph, DAGValidationReport]:
    """
    Build a DAG from a list of nodes and edges with full validation.

    Parameters
    ----------
    nodes : list[str]
        Variable names to include as nodes
    edges : list[tuple]
        Each tuple is (cause, effect) or (cause, effect, metadata_dict).
        Metadata (mechanism, source, etc.) gets stored as edge attributes.
    strict : bool
        If True, raise an error on any validation failure.
        If False, skip bad edges and report them.

    Returns
    -------
    G : nx.DiGraph
        The constructed DAG (may have fewer edges than input if cycles were caught)
    report : DAGValidationReport
        Full validation results
    """
    report = DAGValidationReport()
    G = nx.DiGraph()

    # Add all nodes
    G.add_nodes_from(nodes)

    # Add edges one at a time, checking for cycles after each
    for edge in edges:
        if len(edge) == 2:
            cause, effect = edge
            attrs = {}
        elif len(edge) == 3:
            cause, effect = edge[0], edge[1]
            attrs = edge[2] if isinstance(edge[2], dict) else {"mechanism": edge[2]}
        else:
            report.warnings.append(f"Malformed edge skipped: {edge}")
            continue

        # Check that both nodes exist
        if cause not in G.nodes:
            report.warnings.append(
                f"Node '{cause}' not in node list, adding automatically"
            )
            G.add_node(cause)

        if effect not in G.nodes:
            report.warnings.append(
                f"Node '{effect}' not in node list, adding automatically"
            )
            G.add_node(effect)

        # Check for self-loops
        if cause == effect:
            report.rejected_edges.append(
                ((cause, effect), "Self-loop: a variable cannot cause itself")
            )
            continue

        # Check for duplicate edges
        if G.has_edge(cause, effect):
            report.warnings.append(
                f"Duplicate edge skipped: {cause} -> {effect}"
            )
            continue

        # Add the edge tentatively
        G.add_edge(cause, effect, **attrs)

        # Check if this created a cycle
        if not nx.is_directed_acyclic_graph(G):
            G.remove_edge(cause, effect)
            report.cycles_found.append(
                f"{cause} -> {effect} (would create cycle)"
            )
            report.rejected_edges.append(
                ((cause, effect), "Creates a cycle in the graph")
            )

            if strict:
                raise ValueError(
                    f"Edge {cause} -> {effect} creates a cycle. "
                    f"Aborting in strict mode."
                )

    # Run validation checks
    report.is_acyclic = nx.is_directed_acyclic_graph(G)
    report.node_count = G.number_of_nodes()
    report.edge_count = G.number_of_edges()

    # Check for orphan nodes
    for n in G.nodes:
        if G.in_degree(n) == 0 and G.out_degree(n) == 0:
            report.orphan_nodes.append(n)

    if report.orphan_nodes:
        report.warnings.append(
            f"Orphan nodes found: {report.orphan_nodes}. "
            f"These have no incoming or outgoing edges."
        )

    # Check for disconnected components
    undirected = G.to_undirected()
    components = list(nx.connected_components(undirected))
    report.disconnected_components = len(components)

    if len(components) > 1:
        report.warnings.append(
            f"Graph has {len(components)} disconnected components: "
            f"{[list(c) for c in components]}"
        )

    # Overall validity
    report.is_valid = (
        report.is_acyclic
        and len(report.orphan_nodes) == 0
        and report.disconnected_components <= 1
    )

    return G, report


# ---------------------------------------------------------------------------
# Build from ElicitationResult
# ---------------------------------------------------------------------------

def build_dag_from_result(result) -> tuple[nx.DiGraph, DAGValidationReport]:
    """
    Build a DAG from a ProfY ElicitationResult object.

    Parameters
    ----------
    result : ElicitationResult
        Output from profy_engine.run()

    Returns
    -------
    G : nx.DiGraph
    report : DAGValidationReport
    """
    # Extract variable names
    nodes = [v["name"] for v in result.variables]

    # Extract edges with metadata
    edges = []
    for e in result.edges:
        attrs = {
            "mechanism": e.get("mechanism", ""),
            "phase_discovered": e.get("phase_discovered", ""),
            "source": e.get("source", ""),
            "status": e.get("status", "proposed"),
        }
        edges.append((e["cause"], e["effect"], attrs))

    return build_dag(nodes, edges)


# ---------------------------------------------------------------------------
# Build from saved transcript JSON
# ---------------------------------------------------------------------------

def build_dag_from_transcript(
    transcript_path: str
) -> tuple[nx.DiGraph, DAGValidationReport]:
    """
    Build a DAG from a saved ProfY transcript file.

    Parameters
    ----------
    transcript_path : str
        Path to the JSON transcript file

    Returns
    -------
    G : nx.DiGraph
    report : DAGValidationReport
    """
    with open(transcript_path, "r") as f:
        transcript = json.load(f)

    nodes = [v["name"] for v in transcript["final_variables"]]

    edges = []
    for e in transcript["final_edges"]:
        attrs = {
            "mechanism": e.get("mechanism", ""),
            "phase_discovered": e.get("phase_discovered", ""),
            "source": e.get("source", ""),
            "status": e.get("status", "proposed"),
        }
        edges.append((e["cause"], e["effect"], attrs))

    return build_dag(nodes, edges)


# ---------------------------------------------------------------------------
# Build from a manual edge list (post Human Decision Node)
# ---------------------------------------------------------------------------

def build_dag_from_edges(
    edges: list[tuple],
    nodes: Optional[list[str]] = None
) -> tuple[nx.DiGraph, DAGValidationReport]:
    """
    Build a DAG from a manually curated edge list.

    This is what the notebook uses after the Human Decision Node,
    where the analyst has reviewed and accepted/rejected edges.

    Parameters
    ----------
    edges : list[tuple]
        Each tuple is (cause, effect) or (cause, effect, mechanism_str)
    nodes : list[str], optional
        If provided, use this node list. If not, infer from edges.

    Returns
    -------
    G : nx.DiGraph
    report : DAGValidationReport
    """
    if nodes is None:
        node_set = set()
        for e in edges:
            node_set.add(e[0])
            node_set.add(e[1])
        nodes = sorted(node_set)

    return build_dag(nodes, edges)


# ---------------------------------------------------------------------------
# Utility: compare two DAGs structurally
# ---------------------------------------------------------------------------

def compare_dag_structure(
    dag_a: nx.DiGraph,
    dag_b: nx.DiGraph,
    name_a: str = "DAG A",
    name_b: str = "DAG B"
) -> dict:
    """
    Compare the structure of two DAGs and categorize edges.

    Returns a dict with edge sets categorized as:
    - correct: in both graphs, same direction
    - missing: in dag_b but not dag_a
    - extra: in dag_a but not dag_b
    - reversed: present in both but pointing opposite directions

    Parameters
    ----------
    dag_a : nx.DiGraph
        The DAG to evaluate (e.g., elicited DAG)
    dag_b : nx.DiGraph
        The reference DAG (e.g., ground truth)

    Returns
    -------
    dict with keys: correct, missing, extra, reversed, summary
    """
    edges_a = set(dag_a.edges())
    edges_b = set(dag_b.edges())

    # Correct: in both
    correct = edges_a & edges_b

    # Extra: in A but not in B
    extra = edges_a - edges_b

    # Missing: in B but not in A
    missing = edges_b - edges_a

    # Reversed: check if any "extra" edge exists in reverse in B
    reversed_edges = set()
    truly_extra = set()
    for u, v in extra:
        if (v, u) in edges_b:
            reversed_edges.add((u, v))
        else:
            truly_extra.add((u, v))

    # Also remove reversed from missing (they're accounted for)
    truly_missing = set()
    for u, v in missing:
        if (v, u) not in edges_a:
            truly_missing.add((u, v))

    result = {
        "correct": sorted(correct),
        "missing": sorted(truly_missing),
        "extra": sorted(truly_extra),
        "reversed": sorted(reversed_edges),
    }

    result["summary"] = {
        "correct_count": len(correct),
        "missing_count": len(truly_missing),
        "extra_count": len(truly_extra),
        "reversed_count": len(reversed_edges),
        "total_in_reference": len(edges_b),
        "total_in_evaluated": len(edges_a),
    }

    return result


def print_comparison(comparison: dict, name_a: str = "Elicited", name_b: str = "Ground Truth") -> None:
    """Print a readable summary of a DAG comparison."""
    s = comparison["summary"]

    print("=" * 60)
    print(f"DAG COMPARISON: {name_a} vs {name_b}")
    print("=" * 60)
    print(f"Reference edges:  {s['total_in_reference']}")
    print(f"Evaluated edges:  {s['total_in_evaluated']}")
    print(f"Correct:          {s['correct_count']}")
    print(f"Missing:          {s['missing_count']}")
    print(f"Extra:            {s['extra_count']}")
    print(f"Reversed:         {s['reversed_count']}")

    if comparison["correct"]:
        print(f"\nCorrect edges (green):")
        for u, v in comparison["correct"]:
            print(f"  {u} -> {v}")

    if comparison["missing"]:
        print(f"\nMissing edges (red dashed):")
        for u, v in comparison["missing"]:
            print(f"  {u} -> {v}")

    if comparison["extra"]:
        print(f"\nExtra edges (orange):")
        for u, v in comparison["extra"]:
            print(f"  {u} -> {v}")

    if comparison["reversed"]:
        print(f"\nReversed edges (blue):")
        for u, v in comparison["reversed"]:
            print(f"  {u} -> {v} (should be {v} -> {u})")

    print()


# ---------------------------------------------------------------------------
# Main (for testing)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Test 1: Build from transcript
    print("Test 1: Build DAG from saved transcript")
    print("-" * 40)

    dag, report = build_dag_from_transcript(
        "transcripts/supply_chain_socratic.json"
    )
    report.print_report()

    # Test 2: Compare against ground truth
    print("Test 2: Compare elicited DAG against ground truth")
    print("-" * 40)

    from ground_truth_dag import build_ground_truth_dag
    ground_truth = build_ground_truth_dag()

    comparison = compare_dag_structure(dag, ground_truth)
    print_comparison(comparison, "Elicited", "Ground Truth")

    # Test 3: Build from manual edge list with a bad edge
    print("Test 3: Build from edges with a cycle")
    print("-" * 40)

    bad_edges = [
        ("A", "B"),
        ("B", "C"),
        ("C", "A"),  # this creates a cycle
        ("C", "D"),
    ]

    dag_bad, report_bad = build_dag_from_edges(bad_edges)
    report_bad.print_report()