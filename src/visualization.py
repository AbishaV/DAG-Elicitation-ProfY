"""
Visualization — Color-Coded DAG Comparison Plots
==================================================
Chapter 12: LLMs as DAG Elicitation Engines

Produces publication-quality DAG visualizations:
  1. Single DAG plot with layered layout
  2. Side-by-side comparison (ground truth vs elicited)
  3. Color-coded edges showing correct, missing, extra, and reversed

Color scheme:
  Green:      correct edges (in both DAGs, same direction)
  Red dashed: missing edges (in ground truth but not elicited)
  Orange:     extra/hallucinated edges (in elicited but not ground truth)
  Blue:       reversed edges (present in both, wrong direction)

Usage:
    from visualization import plot_dag, plot_comparison, plot_ground_truth

    # Single DAG
    plot_dag(dag, title="My DAG")

    # Side-by-side comparison
    plot_comparison(elicited_dag, ground_truth_dag)

    # Just the ground truth
    plot_ground_truth()
"""

import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from typing import Optional


# ---------------------------------------------------------------------------
# Layout positions (shared across all plots for consistency)
# ---------------------------------------------------------------------------

def get_layout() -> dict:
    """
    Hand-tuned node positions for a readable DAG layout.

    Layers follow causal flow top to bottom:
      Layer 0: exogenous shocks
      Layer 1: direct children of shocks
      Layer 2: intermediate mechanisms
      Layer 3: proximate causes of outcomes
      Layer 4: target outcomes
    """
    return {
        "geopolitical_risk":         (-2.0,  4.0),
        "demand_volatility":         ( 2.0,  4.0),
        "labor_shortages":           ( 0.0,  4.0),
        "fuel_prices":               (-3.0,  2.5),
        "port_congestion":           (-1.0,  2.5),
        "supplier_reliability":      ( 1.5,  2.5),
        "raw_material_availability": ( 0.0,  1.0),
        "production_capacity":       (-1.5,  1.0),
        "order_lead_time":           ( 2.5,  1.0),
        "inventory_levels":          ( 0.0, -0.5),
        "shipping_cost":             (-2.5, -0.5),
        "delivery_delays":           ( 1.0, -2.0),
    }


DISPLAY_LABELS = {
    "geopolitical_risk":         "Geopolitical\nRisk",
    "fuel_prices":               "Fuel\nPrices",
    "port_congestion":           "Port\nCongestion",
    "labor_shortages":           "Labor\nShortages",
    "supplier_reliability":      "Supplier\nReliability",
    "raw_material_availability": "Raw Material\nAvailability",
    "production_capacity":       "Production\nCapacity",
    "demand_volatility":         "Demand\nVolatility",
    "shipping_cost":             "Shipping\nCost",
    "order_lead_time":           "Order\nLead Time",
    "inventory_levels":          "Inventory\nLevels",
    "delivery_delays":           "Delivery\nDelays",
}


# ---------------------------------------------------------------------------
# Node styling
# ---------------------------------------------------------------------------

def get_node_colors(G: nx.DiGraph) -> list:
    """Color nodes by role: root (exogenous), leaf (outcome), or mediator."""
    colors = []
    for n in G.nodes:
        if G.in_degree(n) == 0:
            colors.append("#3498DB")   # blue for exogenous
        elif G.out_degree(n) == 0:
            colors.append("#E74C3C")   # red for outcomes
        else:
            colors.append("#F9E79F")   # soft yellow for mediators
    return colors


# ---------------------------------------------------------------------------
# Single DAG plot
# ---------------------------------------------------------------------------

def plot_dag(
    G: nx.DiGraph,
    title: str = "Causal DAG",
    ax: Optional[plt.Axes] = None,
    save_path: Optional[str] = None,
    figsize: tuple = (12, 10),
    edge_color: str = "#555555",
    show_labels: bool = True
) -> Optional[plt.Figure]:
    """
    Plot a single DAG with the standard layered layout.

    Parameters
    ----------
    G : nx.DiGraph
        The DAG to plot
    title : str
        Plot title
    ax : plt.Axes, optional
        Axes to plot on. If None, creates a new figure.
    save_path : str, optional
        If provided, save the figure to this path
    figsize : tuple
        Figure size if creating a new figure
    edge_color : str
        Default edge color
    show_labels : bool
        Whether to show node labels
    """
    pos = get_layout()
    created_fig = False

    if ax is None:
        fig, ax = plt.subplots(1, 1, figsize=figsize)
        created_fig = True

    # Filter positions to only include nodes in this graph
    pos_filtered = {n: pos[n] for n in G.nodes if n in pos}

    # For nodes not in our layout, use spring layout as fallback
    missing = [n for n in G.nodes if n not in pos]
    if missing:
        extra_pos = nx.spring_layout(G.subgraph(missing), seed=42)
        pos_filtered.update(extra_pos)

    node_colors = get_node_colors(G)

    # Draw nodes
    nx.draw_networkx_nodes(
        G, pos_filtered, ax=ax,
        node_color=node_colors,
        node_size=2000,
        edgecolors="#333333",
        linewidths=1.5
    )

    # Draw edges
    nx.draw_networkx_edges(
        G, pos_filtered, ax=ax,
        edge_color=edge_color,
        arrows=True,
        arrowsize=20,
        arrowstyle="-|>",
        connectionstyle="arc3,rad=0.1",
        width=1.5
    )

    # Draw labels
    if show_labels:
        labels = {n: DISPLAY_LABELS.get(n, n) for n in G.nodes}
        nx.draw_networkx_labels(
            G, pos_filtered, labels, ax=ax,
            font_size=7,
            font_weight="bold"
        )

    ax.set_title(title, fontsize=14, fontweight="bold", pad=20)
    ax.axis("off")

    if save_path and created_fig:
        fig.tight_layout()
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"Saved to {save_path}")

    if created_fig:
        return fig
    return None


# ---------------------------------------------------------------------------
# Color-coded comparison plot
# ---------------------------------------------------------------------------

def plot_comparison(
    elicited: nx.DiGraph,
    ground_truth: nx.DiGraph,
    title_elicited: str = "Elicited DAG",
    title_truth: str = "Ground Truth DAG",
    save_path: Optional[str] = None,
    figsize: tuple = (22, 10)
) -> plt.Figure:
    """
    Side-by-side DAG comparison with color-coded edges.

    The elicited DAG shows edges colored by correctness.
    The ground truth shows all edges in a neutral color.

    Parameters
    ----------
    elicited : nx.DiGraph
        The DAG produced by elicitation
    ground_truth : nx.DiGraph
        The reference DAG
    save_path : str, optional
        If provided, save the figure
    figsize : tuple
        Figure size

    Returns
    -------
    plt.Figure
    """
    fig, (ax_truth, ax_elicited) = plt.subplots(1, 2, figsize=figsize)

    pos = get_layout()

    # Categorize edges
    edges_elicited = set(elicited.edges())
    edges_truth = set(ground_truth.edges())

    correct = edges_elicited & edges_truth
    extra = edges_elicited - edges_truth
    missing = edges_truth - edges_elicited

    reversed_edges = set()
    truly_extra = set()
    for u, v in extra:
        if (v, u) in edges_truth:
            reversed_edges.add((u, v))
        else:
            truly_extra.add((u, v))

    truly_missing = set()
    for u, v in missing:
        if (v, u) not in edges_elicited:
            truly_missing.add((u, v))

    # --- Plot ground truth (left) ---
    pos_truth = {n: pos[n] for n in ground_truth.nodes if n in pos}
    node_colors_truth = get_node_colors(ground_truth)

    nx.draw_networkx_nodes(
        ground_truth, pos_truth, ax=ax_truth,
        node_color=node_colors_truth,
        node_size=2000,
        edgecolors="#333333",
        linewidths=1.5
    )

    nx.draw_networkx_edges(
        ground_truth, pos_truth, ax=ax_truth,
        edge_color="#555555",
        arrows=True,
        arrowsize=20,
        arrowstyle="-|>",
        connectionstyle="arc3,rad=0.1",
        width=1.5
    )

    labels_truth = {n: DISPLAY_LABELS.get(n, n) for n in ground_truth.nodes}
    nx.draw_networkx_labels(
        ground_truth, pos_truth, labels_truth, ax=ax_truth,
        font_size=7,
        font_weight="bold"
    )

    ax_truth.set_title(title_truth, fontsize=14, fontweight="bold", pad=20)
    ax_truth.axis("off")

    # --- Plot elicited DAG (right) with color-coded edges ---

    # Use the union of nodes from both graphs for positioning
    all_nodes = set(elicited.nodes()) | set(ground_truth.nodes())
    combined = nx.DiGraph()
    combined.add_nodes_from(all_nodes)
    combined.add_edges_from(elicited.edges())
    # Add missing edges as dashed so they show up
    for u, v in truly_missing:
        if not combined.has_edge(u, v):
            combined.add_edge(u, v)

    pos_elicited = {n: pos[n] for n in combined.nodes if n in pos}
    node_colors_elicited = []
    for n in combined.nodes:
        if combined.in_degree(n) == 0 and combined.out_degree(n) == 0:
            node_colors_elicited.append("#DDDDDD")
        elif n in elicited.nodes:
            if elicited.in_degree(n) == 0:
                node_colors_elicited.append("#3498DB")
            elif elicited.out_degree(n) == 0:
                node_colors_elicited.append("#E74C3C")
            else:
                node_colors_elicited.append("#F9E79F")
        else:
            node_colors_elicited.append("#DDDDDD")

    nx.draw_networkx_nodes(
        combined, pos_elicited, ax=ax_elicited,
        node_color=node_colors_elicited,
        node_size=2000,
        edgecolors="#333333",
        linewidths=1.5
    )

    # Draw correct edges (green)
    if correct:
        nx.draw_networkx_edges(
            combined, pos_elicited, ax=ax_elicited,
            edgelist=list(correct),
            edge_color="#2ECC71",
            arrows=True,
            arrowsize=20,
            arrowstyle="-|>",
            connectionstyle="arc3,rad=0.1",
            width=2.0
        )

    # Draw extra/hallucinated edges (orange)
    if truly_extra:
        nx.draw_networkx_edges(
            combined, pos_elicited, ax=ax_elicited,
            edgelist=list(truly_extra),
            edge_color="#E67E22",
            arrows=True,
            arrowsize=20,
            arrowstyle="-|>",
            connectionstyle="arc3,rad=0.1",
            width=2.5
        )

    # Draw missing edges (red dashed)
    if truly_missing:
        nx.draw_networkx_edges(
            combined, pos_elicited, ax=ax_elicited,
            edgelist=list(truly_missing),
            edge_color="#E74C3C",
            arrows=True,
            arrowsize=20,
            arrowstyle="-|>",
            connectionstyle="arc3,rad=0.1",
            width=2.0,
            style="dashed"
        )

    # Draw reversed edges (blue)
    if reversed_edges:
        nx.draw_networkx_edges(
            combined, pos_elicited, ax=ax_elicited,
            edgelist=list(reversed_edges),
            edge_color="#3498DB",
            arrows=True,
            arrowsize=20,
            arrowstyle="-|>",
            connectionstyle="arc3,rad=0.1",
            width=2.5
        )

    labels_elicited = {n: DISPLAY_LABELS.get(n, n) for n in combined.nodes}
    nx.draw_networkx_labels(
        combined, pos_elicited, labels_elicited, ax=ax_elicited,
        font_size=7,
        font_weight="bold"
    )

    ax_elicited.set_title(title_elicited, fontsize=14, fontweight="bold", pad=20)
    ax_elicited.axis("off")

    # Legend
    legend_patches = [
        mpatches.Patch(color="#2ECC71", label="Correct"),
        mpatches.Patch(color="#E74C3C", label="Missing"),
        mpatches.Patch(color="#E67E22", label="Extra (hallucinated)"),
        mpatches.Patch(color="#3498DB", label="Reversed"),
    ]
    ax_elicited.legend(
        handles=legend_patches,
        loc="lower right",
        fontsize=9,
        framealpha=0.9
    )

    fig.suptitle(
        "DAG Comparison: Elicited vs Ground Truth",
        fontsize=16, fontweight="bold", y=1.02
    )

    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"Saved to {save_path}")

    return fig


# ---------------------------------------------------------------------------
# Convenience: plot just the ground truth
# ---------------------------------------------------------------------------

def plot_ground_truth(save_path: Optional[str] = None) -> plt.Figure:
    """Plot the ground truth DAG by itself."""
    import sys
    sys.path.insert(0, "src")
    from ground_truth_dag import build_ground_truth_dag

    G = build_ground_truth_dag()
    return plot_dag(
        G,
        title="Ground Truth DAG: Supply Chain Disruption",
        save_path=save_path
    )


# ---------------------------------------------------------------------------
# Main (for testing)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    sys.path.insert(0, "src")

    from ground_truth_dag import build_ground_truth_dag, EDGES
    from dag_builder import build_dag_from_transcript

    ground_truth = build_ground_truth_dag()

    # Test 1: Plot ground truth alone
    print("Test 1: Plotting ground truth DAG")
    print("-" * 40)
    fig1 = plot_dag(
        ground_truth,
        title="Ground Truth DAG: Supply Chain Disruption",
        save_path="figures/ground_truth_dag.png"
    )
    plt.show()

    # Test 2: Perfect match comparison
    print("\nTest 2: Side-by-side comparison (perfect match)")
    print("-" * 40)
    elicited, _ = build_dag_from_transcript("transcripts/supply_chain_socratic.json")
    fig2 = plot_comparison(
        elicited, ground_truth,
        title_elicited="Elicited DAG (Socratic Strategy)",
        save_path="figures/dag_comparison_perfect.png"
    )
    plt.show()

    # Test 3: Imperfect comparison (the interesting one)
    print("\nTest 3: Side-by-side comparison (imperfect DAG)")
    print("-" * 40)
    imperfect = ground_truth.copy()
    imperfect.remove_edge("fuel_prices", "production_capacity")
    imperfect.remove_edge("supplier_reliability", "order_lead_time")
    imperfect.add_edge("fuel_prices", "delivery_delays")
    imperfect.remove_edge("demand_volatility", "order_lead_time")
    imperfect.add_edge("order_lead_time", "demand_volatility")

    fig3 = plot_comparison(
        imperfect, ground_truth,
        title_elicited="Imperfect Elicited DAG",
        save_path="figures/dag_comparison_imperfect.png"
    )
    plt.show()

    print("\nAll plots generated. Check the figures/ folder.")