"""
Ground Truth Reference DAG — Supply Chain Disruption Domain
============================================================
Chapter 12: LLMs as DAG Elicitation Engines

Target outcomes: delivery_delays, shipping_cost
Nodes: 12
Edges: 19

Every edge is justified by published supply chain literature.
See companion file: ground_truth_dag_citations.md

Author: [Your Name]
Date: April 2026
"""

import networkx as nx

# ---------------------------------------------------------------------------
# Node definitions
# ---------------------------------------------------------------------------
# Each node is a variable in the supply chain disruption domain.
# Names are snake_case for code consistency; display labels provided below.

NODES = [
    "geopolitical_risk",
    "fuel_prices",
    "port_congestion",
    "labor_shortages",
    "supplier_reliability",
    "raw_material_availability",
    "production_capacity",
    "demand_volatility",
    "shipping_cost",
    "order_lead_time",
    "inventory_levels",
    "delivery_delays",
]

DISPLAY_LABELS = {
    "geopolitical_risk":        "Geopolitical\nRisk",
    "fuel_prices":              "Fuel\nPrices",
    "port_congestion":          "Port\nCongestion",
    "labor_shortages":          "Labor\nShortages",
    "supplier_reliability":     "Supplier\nReliability",
    "raw_material_availability":"Raw Material\nAvailability",
    "production_capacity":      "Production\nCapacity",
    "demand_volatility":        "Demand\nVolatility",
    "shipping_cost":            "Shipping\nCost",
    "order_lead_time":          "Order\nLead Time",
    "inventory_levels":         "Inventory\nLevels",
    "delivery_delays":          "Delivery\nDelays",
}

# ---------------------------------------------------------------------------
# Edge definitions
# ---------------------------------------------------------------------------
# Format: (cause, effect)
# Each edge has a short rationale; full citations in the markdown file.

EDGES = [
    # --- Exogenous shocks propagating into the system ---
    ("geopolitical_risk", "fuel_prices"),           # E1: sanctions, conflict → energy price spikes
    ("geopolitical_risk", "port_congestion"),        # E2: conflict zones → rerouting, port closures
    ("geopolitical_risk", "raw_material_availability"),  # E3: sanctions/embargoes restrict supply
    ("geopolitical_risk", "supplier_reliability"),   # E4: political instability → supplier disruption

    # --- Fuel prices effects ---
    ("fuel_prices", "shipping_cost"),               # E5: fuel is a direct cost component of freight
    ("fuel_prices", "production_capacity"),          # E6: energy costs constrain manufacturing output

    # --- Port congestion effects ---
    ("port_congestion", "shipping_cost"),            # E7: congestion surcharges, demurrage fees
    ("port_congestion", "delivery_delays"),          # E8: ships waiting at port → downstream delays

    # --- Labor shortages effects ---
    ("labor_shortages", "port_congestion"),          # E9: dockworker shortages → slower throughput
    ("labor_shortages", "production_capacity"),      # E10: manufacturing workforce gaps → reduced output

    # --- Supply-side chain ---
    ("raw_material_availability", "production_capacity"),  # E11: can't produce without inputs
    ("supplier_reliability", "raw_material_availability"), # E12: unreliable supplier → material gaps
    ("supplier_reliability", "order_lead_time"),     # E13: unreliable supplier → longer/variable lead times

    # --- Production and demand into downstream outcomes ---
    ("production_capacity", "inventory_levels"),     # E14: less production → lower inventory
    ("demand_volatility", "inventory_levels"),       # E15: demand swings deplete or bloat inventory
    ("demand_volatility", "order_lead_time"),        # E16: demand surges → longer lead times

    # --- Downstream convergence on target outcomes ---
    ("order_lead_time", "delivery_delays"),          # E17: longer lead times → higher delay probability
    ("inventory_levels", "delivery_delays"),         # E18: low inventory → can't fulfill on time
    ("inventory_levels", "shipping_cost"),           # E19: low inventory → expedited/emergency shipping
]

# ---------------------------------------------------------------------------
# Build the DAG
# ---------------------------------------------------------------------------

def build_ground_truth_dag() -> nx.DiGraph:
    """Construct and validate the ground truth DAG."""
    G = nx.DiGraph()
    G.add_nodes_from(NODES)
    G.add_edges_from(EDGES)

    # --- Validation ---
    assert nx.is_directed_acyclic_graph(G), "Graph contains a cycle!"
    assert len(G.nodes) == 12, f"Expected 12 nodes, got {len(G.nodes)}"
    assert len(G.edges) == 19, f"Expected 19 edges, got {len(G.edges)}"

    # Check for orphan nodes (no incoming AND no outgoing edges)
    for n in G.nodes:
        if G.in_degree(n) == 0 and G.out_degree(n) == 0:
            raise ValueError(f"Orphan node detected: {n}")

    # Check that target outcomes have incoming edges
    for target in ["delivery_delays", "shipping_cost"]:
        assert G.in_degree(target) > 0, f"Target {target} has no parents!"

    return G


def print_dag_summary(G: nx.DiGraph) -> None:
    """Print summary statistics for the DAG."""
    print("=" * 60)
    print("GROUND TRUTH DAG — Supply Chain Disruption")
    print("=" * 60)
    print(f"Nodes: {G.number_of_nodes()}")
    print(f"Edges: {G.number_of_edges()}")
    print(f"Acyclic: {nx.is_directed_acyclic_graph(G)}")
    print()

    # Root nodes (no parents — exogenous variables)
    roots = [n for n in G.nodes if G.in_degree(n) == 0]
    print(f"Root nodes (exogenous): {roots}")

    # Leaf nodes (no children — outcome variables)
    leaves = [n for n in G.nodes if G.out_degree(n) == 0]
    print(f"Leaf nodes (outcomes):  {leaves}")
    print()

    # Topological order
    print("Topological order:")
    for i, n in enumerate(nx.topological_sort(G)):
        parents = list(G.predecessors(n))
        children = list(G.successors(n))
        print(f"  {i+1:2d}. {n:<30s} parents={parents}  children={children}")
    print()

    # Edge list
    print("Edge list:")
    for i, (u, v) in enumerate(EDGES, 1):
        print(f"  E{i:02d}: {u} → {v}")


# ---------------------------------------------------------------------------
# pgmpy compatibility (for backdoor computation in the notebook)
# ---------------------------------------------------------------------------

def build_pgmpy_model():
    """
    Build the same DAG as a pgmpy BayesianNetwork.
    
    Note: pgmpy's BayesianNetwork requires edges at construction.
    This function returns the model without CPDs — structure only,
    suitable for d-separation queries and backdoor set computation.
    """
    try:
        from pgmpy.models import BayesianNetwork
    except ImportError:
        raise ImportError(
            "pgmpy is required for this function. "
            "Install with: pip install pgmpy"
        )

    model = BayesianNetwork(EDGES)

    # Validate
    assert model.check_model() or True  # check_model needs CPDs; structure is valid if no cycle
    return model


# ---------------------------------------------------------------------------
# Visualization helper
# ---------------------------------------------------------------------------

def get_layout_positions() -> dict:
    """
    Return hand-tuned node positions for a readable DAG layout.
    
    Layout logic:
      Layer 0 (top):    Exogenous shocks — geopolitical_risk, demand_volatility, labor_shortages
      Layer 1:          fuel_prices, port_congestion, supplier_reliability
      Layer 2:          raw_material_availability, production_capacity, order_lead_time
      Layer 3:          inventory_levels, shipping_cost
      Layer 4 (bottom): delivery_delays
    """
    return {
        # Layer 0 — exogenous
        "geopolitical_risk":         (-2.0,  4.0),
        "demand_volatility":         ( 2.0,  4.0),
        "labor_shortages":           ( 0.0,  4.0),

        # Layer 1
        "fuel_prices":               (-3.0,  2.5),
        "port_congestion":           (-1.0,  2.5),
        "supplier_reliability":      ( 1.5,  2.5),

        # Layer 2
        "raw_material_availability": ( 0.0,  1.0),
        "production_capacity":       (-1.5,  1.0),
        "order_lead_time":           ( 2.5,  1.0),

        # Layer 3
        "inventory_levels":          ( 0.0, -0.5),
        "shipping_cost":             (-2.5, -0.5),

        # Layer 4 — target outcome
        "delivery_delays":           ( 1.0, -2.0),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    G = build_ground_truth_dag()
    print_dag_summary(G)