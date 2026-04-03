# Understanding the Ground Truth DAG Code
## A beginner-friendly guide to what's happening and why

---

## The Big Picture

Before we build any AI agent or run any experiment, we need an answer key: a causal graph that represents our best understanding of how supply chain disruptions actually work, backed by published research.

This Python file is that answer key. Everything else in Chapter 12 gets graded against it. The elicitation agent tries to reconstruct this graph through conversation, and we measure how close it gets using a metric called Structural Hamming Distance (basically: count the mistakes).

If the answer key is wrong, every evaluation downstream is meaningless. That's why every arrow in this graph has a citation behind it.

---

## What's a DAG, in plain terms?

A DAG (Directed Acyclic Graph) is a map of cause and effect. It has two ingredients:

- **Nodes**: the things you care about (variables like "fuel prices" or "delivery delays")
- **Edges**: arrows connecting them, where each arrow means "this causes that"

The "acyclic" part means no loops. You can't follow the arrows and end up back where you started. This matters because causal reasoning breaks down when causes loop back on themselves. That's feedback, and it requires different math.

---

## Walking Through the Code

### Defining the variables: `NODES`

```python
NODES = [
    "geopolitical_risk",
    "fuel_prices",
    "port_congestion",
    ...
]
```

These are the 12 supply chain variables in our DAG. Each one becomes a dot on the graph.

The project started with 16 candidates. Four got cut during design: warehouse capacity (merged into inventory levels at this zoom level), transportation mode choice (a decision someone makes in response to the system, not a cause within it), customer satisfaction (would just dangle at the bottom with one arrow pointing in), and quality control failures (weak connections to everything else, but great as a trap the LLM is likely to hallucinate).

The point isn't to model every supply chain variable that exists. It's to model enough of them that the DAG is non-trivial (interesting to evaluate) but not so many that evaluation becomes noisy.

---

### Defining the arrows: `EDGES`

```python
EDGES = [
    ("geopolitical_risk", "fuel_prices"),
    ("geopolitical_risk", "port_congestion"),
    ("fuel_prices", "shipping_cost"),
    ("port_congestion", "delivery_delays"),
    ...
]
```

This is the heart of the file. 19 directed edges, each one a claim that says "X causes Y." Every one of these arrows has a published source behind it in the companion citations file.

Some are intuitive: fuel prices drive shipping costs because fuel is a direct cost component of freight. Some are less obvious: low inventory levels drive up shipping costs, because when you're out of stock you pay for emergency air freight instead of slow sea freight.

Just as important: some arrows that sound reasonable were deliberately left out. There's no direct arrow from fuel prices to delivery delays, because fuel prices only affect delays through other variables like shipping cost and port congestion. That missing shortcut is intentional, and it's exactly the kind of plausible-sounding edge an LLM will propose. When ProfY suggests "fuel prices cause delivery delays" and the human catches it, that's the chapter working as designed.

---

### Building and validating: `build_ground_truth_dag()`

```python
def build_ground_truth_dag() -> nx.DiGraph:
    G = nx.DiGraph()
    G.add_nodes_from(NODES)
    G.add_edges_from(EDGES)

    assert nx.is_directed_acyclic_graph(G), "Graph contains a cycle!"
    assert len(G.nodes) == 12
    assert len(G.edges) == 19
    ...
```

This function does two things: it builds the graph, then it refuses to let you proceed if the graph is broken.

The acyclicity check catches the most dangerous structural error. A cycle would mean "A causes B causes A," which violates the definition of a DAG and would make every downstream computation invalid. Think of it like a spreadsheet formula that references itself: the math breaks.

The orphan check catches nodes that got defined but never connected to anything. Dead weight that would inflate the node count without contributing to the structure.

The target check confirms that delivery delays and shipping cost actually have causal parents pointing into them. An outcome with no parents is an outcome we can't explain, which defeats the entire purpose.

If any of these checks fail, the file crashes with a clear error message instead of silently producing a broken graph. Better to crash here than to discover the problem three days into evaluation.

---

### Printing the summary: `print_dag_summary()`

```python
roots = [n for n in G.nodes if G.in_degree(n) == 0]
leaves = [n for n in G.nodes if G.out_degree(n) == 0]
```

When you run the file, this prints the structural fingerprint of the DAG.

Root nodes are variables with no parents. Nothing in this graph causes them. These are the exogenous shocks: geopolitical risk, demand volatility, and labor shortages. They're where disruptions enter the system. Think of them as the weather: the model doesn't explain why it rains, it explains what happens when it does.

Leaf nodes are variables with no children. They don't cause anything else downstream. These are the target outcomes: delivery delays and shipping cost. They're where disruptions land.

Everything in between is a mediator. It has parents and children, it receives causal influence and passes it along. The topological ordering shows you the sequence: which variables must be determined before others, following the direction of the arrows.

---

### pgmpy compatibility: `build_pgmpy_model()`

```python
def build_pgmpy_model():
    from pgmpy.models import BayesianNetwork
    model = BayesianNetwork(EDGES)
    return model
```

This wraps the same 19 edges into a pgmpy Bayesian Network object. We need this later for two specific jobs: finding the backdoor adjustment set (which confounders to control for when estimating a causal effect) and running d-separation queries (testing which variables are conditionally independent given the graph structure).

The function builds structure only, no probability distributions attached. At this stage we're working with the graph's qualitative skeleton, not fitting a statistical model. The probabilities come later when we simulate data.

---

### Layout positions: `get_layout_positions()`

```python
def get_layout_positions() -> dict:
    return {
        "geopolitical_risk": (-2.0, 4.0),
        ...
        "delivery_delays": (1.0, -2.0),
    }
```

Hand-tuned coordinates for plotting the DAG. The layout follows the causal flow: exogenous shocks at the top, intermediate mechanisms in the middle, target outcomes at the bottom. This top-to-bottom arrangement means arrows generally point downward, which makes the graph immediately readable. Causes above, effects below.

Automated layout algorithms tend to produce tangled graphs for DAGs this size. Hand-tuning takes ten minutes and saves the reader from squinting at crossed arrows for the rest of the chapter.

---

### Running the file

```python
if __name__ == "__main__":
    G = build_ground_truth_dag()
    print_dag_summary(G)
```

When you run `python ground_truth_dag.py`, this builds the graph, runs all validations, and prints the summary. If everything is correct, you see 12 nodes, 19 edges, Acyclic: True, the three root nodes, the two leaf nodes, and the full topological ordering.

If anything is wrong, the file crashes before printing anything. The ground truth must be structurally valid before any downstream work begins, and this file enforces that contract every time it runs.