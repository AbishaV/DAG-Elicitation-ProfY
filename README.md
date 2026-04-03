# Chapter 12: LLMs as DAG Elicitation Engines

*Companion code for Chapter 12 of "Causal Machine Learning: A Case Study Guide to Modern Causal Analysis" by Nik Bear Brown.*

---

Before you can estimate a causal effect, you need a map of what causes what. In causal inference, that map is called a DAG (Directed Acyclic Graph): boxes for variables, arrows for causal relationships. The problem is that building one requires sitting down with a domain expert and pulling the structure out of their head. That process is slow, messy, and almost never documented.

This project builds **ProfY**, an AI copilot that makes that process structured and repeatable. ProfY doesn't decide what causes what. It coaches a human analyst through a Socratic interview: asking about variables, probing for causal direction, challenging weak edges, and surfacing hidden confounders. The expert provides the knowledge. ProfY provides the structure. The output is a validated causal graph, ready for estimation.

The core argument of this chapter: LLMs are not reliable causal reasoners on their own. But paired with the right methodology and a human in the loop, they become powerful facilitators of human causal reasoning.

## The Pipeline

1. **ProfY elicitation**: structured five-phase Socratic interview (variable discovery, edge probing, mechanism questioning, confounder probing, checkpoint)
2. **DAG construction**: build a networkx graph from the elicitation output with structural validation
3. **Human Decision Node**: analyst reviews and accepts/rejects every proposed edge with reasoning
4. **Evaluation**: Structural Hamming Distance, precision, recall, F1 against a literature-grounded reference DAG
5. **Visualization**: color-coded side-by-side DAG comparison (correct, missing, extra, reversed edges)
6. **Estimation**: backdoor adjustment sets via the validated DAG, doubly robust causal effect estimation on simulated data

## Case Study Domain

Supply chain disruption, focused on delivery delays and shipping costs. 12 variables, 19 edges, grounded in published supply chain risk management literature (Chopra & Sodhi 2004, Ho et al. 2015, Bai et al. 2024, and others). Full edge-by-edge citations in `docs/ground_truth_dag_citations.md`.

## Setup

```bash
# Clone the repo
git clone https://github.com/AbishaV/DAG-Elicitation-ProfY.git
cd DAG-Elicitation-ProfY

# Create and activate virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# Mac/Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

**Run the ground truth DAG validation:**

```bash
python src/ground_truth_dag.py
```

Expected output: 12 nodes, 19 edges, Acyclic: True.

**Run ProfY in replay mode (no API key needed):**

```bash
python src/profy_engine.py
```

Reads from the saved transcript and prints the full five-phase conversation.

**Run ProfY in live mode (requires Anthropic API key):**

```bash
# Windows
set ANTHROPIC_API_KEY=your-key-here

# Mac/Linux
export ANTHROPIC_API_KEY=your-key-here

python src/profy_engine.py live
```

Calls the Claude API. ProfY generates coaching prompts, you type the analyst responses. See `docs/demo_session_guide.md` for example inputs.

**Run the full evaluation pipeline:**

```bash
python src/evaluation.py
```

**Run the estimation pipeline:**

```bash
python src/estimator.py
```

**Generate DAG visualizations:**

```bash
python src/visualization.py
```

## Project Structure

```
DAG-Elicitation-ProfY/
│
├── README.md
├── requirements.txt
├── .gitignore
│
├── src/
│   ├── __init__.py
│   ├── ground_truth_dag.py        # Reference DAG with literature citations
│   ├── profy_engine.py            # Socratic elicitation agent
│   ├── dag_builder.py             # Build and validate DAGs from elicitation output
│   ├── human_decision_node.py     # Edge review, validation, and decision logging
│   ├── evaluation.py              # SHD, precision, recall, F1 computation
│   ├── estimator.py               # Backdoor sets + doubly robust estimation
│   └── visualization.py           # Color-coded DAG comparison plots
│
├── notebooks/
│   └── ch12_dag_elicitation.ipynb # Main deliverable: book-ready notebook
│
├── transcripts/
│   └── supply_chain_socratic.json # Saved elicitation transcript
│
├── docs/
│   ├── ground_truth_dag_citations.md  # Edge-by-edge literature citations
│   ├── ground_truth_dag_walkthrough.md # Beginner's guide to the DAG code
│   └── demo_session_guide.md          # Example inputs for live mode
│
├── figures/
│   ├── ground_truth_dag.png       # Reference DAG visualization
│   └── dag_comparison.png         # Side-by-side comparison plot
│
├── data/
│   └── simulated_supply_chain.csv # Simulated dataset for estimation
│
└── authors_note/
    └── authors_note.md            # 3-page pedagogical report
```

## Key Results

**Evaluation (ideal elicitation):** SHD = 0, Precision = 1.0, Recall = 1.0, F1 = 1.0

**Evaluation (imperfect elicitation with 4 deliberate errors):** SHD = 4, F1 = 0.865

**Causal estimation (port congestion on delivery delays):**
- Naive difference: 0.95
- Doubly robust ATE (adjusted for geopolitical risk and labor shortages): 0.45
- Nearly half the naive difference was confounding

**Causal estimation (fuel prices on shipping cost):**
- Naive difference: 0.98
- Doubly robust ATE (adjusted for geopolitical risk): 0.51
- Geopolitical risk inflated the naive estimate by driving both variables simultaneously

## Dependencies

- anthropic (for live mode API calls)
- pgmpy (DAG structure, d-separation queries)
- networkx (graph construction and manipulation)
- matplotlib (visualization)
- numpy, pandas (data handling)
- scikit-learn (doubly robust estimator)

## References

- Chopra, S. & Sodhi, M.S. (2004). "Managing Risk to Avoid Supply-Chain Breakdown." *MIT Sloan Management Review*, 46(1), 53-61.
- Ho, W. et al. (2015). "Supply Chain Risk Management: A Literature Review." *International Journal of Production Research*, 53(16), 5031-5069.
- Bai, X. et al. (2024). "The Causal Effects of Global Supply Chain Disruptions." CEPR/VoxEU.
- Tang, C.S. (2006). "Perspectives in Supply Chain Risk Management." *International Journal of Production Economics*, 103(2), 451-488.
- Pearl, J. (2009). *Causality: Models, Reasoning, and Inference.* Cambridge University Press.

Full citations for every DAG edge: `docs/ground_truth_dag_citations.md`