# Chapter 12: LLMs as DAG Elicitation Engines

*Chapter 12 of "Causal Machine Learning: A Case Study Guide to Modern Causal Analysis" by Nik Bear Brown.*

---

Before you can estimate a causal effect, you need a map of what causes what. In causal inference, that map is called a DAG (Directed Acyclic Graph): nodes for variables, arrows for causal relationships. The problem is that building one requires sitting down with a domain expert and extracting the structure from their head. That process is slow, messy, and almost never documented.

This project builds **ProfY**, an AI copilot that makes that process structured and repeatable. ProfY doesn't decide what causes what. It coaches a human analyst through a Socratic interview: asking about variables, probing for causal direction, challenging weak edges, and surfacing hidden confounders. The expert provides the knowledge. ProfY provides the structure. The output is a validated causal graph, ready for estimation.

**The core argument:** LLMs are not reliable causal reasoners on their own. But paired with the right methodology and a human in the loop, they become powerful facilitators of human causal reasoning.

---

## The Pipeline

```
Expert Knowledge → Socratic Interview → Validated DAG → Causal Estimation
```

1. **ProfY Elicitation**: five-phase Socratic interview (variable discovery, edge probing, mechanism questioning, confounder probing, checkpoint validation)
2. **DAG Construction**: build a networkx graph from the elicitation output with structural validation (acyclicity, no orphans, connectivity)
3. **Human Decision Node**: analyst reviews and explicitly accepts or rejects every proposed edge with reasoning. The notebook stops until this step is complete.
4. **Evaluation**: Structural Hamming Distance (SHD), precision, recall, F1 against a literature-grounded reference DAG
5. **Visualization**: color-coded side-by-side DAG comparison (green = correct, red = missing, orange = hallucinated, blue = reversed)
6. **Estimation**: backdoor adjustment sets from the validated DAG, doubly robust causal effect estimation on simulated and real data

---

## Case Study: Supply Chain Disruption

The domain is supply chain disruption, focused on delivery delays and shipping costs. The ground truth DAG has 12 nodes and 19 edges, grounded in published supply chain risk management literature.

**Key Results:**

The ideal elicitation recovered the ground truth exactly: SHD = 0, F1 = 1.0. A deliberately imperfect DAG with 4 errors (2 missing edges, 1 hallucinated, 1 reversed) scored SHD = 4, F1 = 0.865.

The naive causal estimate for port congestion on delivery delays was 0.95. After adjusting for confounders the DAG identified (geopolitical risk, labor shortages), the doubly robust estimate dropped to 0.45. Nearly half the naive difference was confounding.

When tested on 180,000 real supply chain orders (DataCo dataset), the adjustment barely moved the estimate because the true confounders weren't in the dataset. The propensity model accuracy was 0.60, barely better than a coin flip. The DAG didn't fix the data problem. It made the data problem visible.

---

## Setup

```bash
git clone https://github.com/AbishaV/DAG-Elicitation-ProfY.git
cd DAG-Elicitation-ProfY

python -m venv .venv

# Windows
.venv\Scripts\activate

# Mac/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## Quick Start

**Validate the ground truth DAG:**

```bash
python src/ground_truth_dag.py
```

**Run ProfY in replay mode (no API key needed):**

```bash
python src/profy_engine.py
```

**Run ProfY in live mode (requires Anthropic API key):**

```bash
# Windows
set ANTHROPIC_API_KEY=your-key-here

# Mac/Linux
export ANTHROPIC_API_KEY=your-key-here

python src/profy_engine.py live
```

See `docs/demo_session_guide.md` for example inputs when running live.

**Run the evaluation pipeline:**

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

**Run the full notebook:**

Open in Jupyter:
```bash
jupyter notebook notebooks/ch12_dag_elicitation.ipynb
```

Or open in VS Code: navigate to `notebooks/ch12_dag_elicitation.ipynb` and select the Python kernel from your `.venv`.

The notebook runs top to bottom. Select "Run All" or step through cell by cell. It will:
1. Build and validate the ground truth DAG
2. Replay the ProfY elicitation transcript
3. Construct the elicited DAG and run structural validation
4. Present the Human Decision Node (edges are pre-validated for replay)
5. Evaluate against ground truth (SHD, precision, recall, F1)
6. Show color-coded DAG comparison plots
7. Run the doubly robust estimation pipeline
8. Run sensitivity analysis
9. Analyze the DataCo real-world dataset (requires the Kaggle download in `data/`)
10. Save all figures and print final summary

No API key is needed for the default run. Everything uses the saved transcript.

---

## Data

The simulated supply chain dataset is included in `data/simulated_supply_chain.csv`.

For the real data analysis (Part 9 of the notebook), download the DataCo Smart Supply Chain dataset from Kaggle:

1. Go to https://www.kaggle.com/datasets/shashwatwork/dataco-smart-supply-chain-for-big-data-analysis
2. Download `DataCoSupplyChainDataset.csv`
3. Save it to the `data/` folder

---

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
│   ├── ground_truth_dag.py         # Reference DAG (12 nodes, 19 edges, every edge cited)
│   ├── profy_engine.py             # Socratic elicitation agent (replay + live modes)
│   ├── dag_builder.py              # Build and validate DAGs from elicitation output
│   ├── human_decision_node.py      # Edge review, validation, and decision logging
│   ├── evaluation.py               # SHD, precision, recall, F1 computation
│   ├── estimator.py                # Backdoor sets + doubly robust estimation
│   └── visualization.py            # Color-coded DAG comparison plots
│
├── notebooks/
│   └── ch12_dag_elicitation.ipynb  # Main deliverable: complete book-ready notebook
│
├── transcripts/
│   └── supply_chain_socratic.json  # Saved elicitation transcript (5 phases, 19 edges)
│
├── docs/
│   ├── chapter_draft.md            # Full chapter prose (7 sections, reviewed and revised)
│   ├── chapter_draft.pdf           # PDF version of the chapter
│   ├── ground_truth_dag_citations.md   # Edge-by-edge literature citations
│   ├── ground_truth_dag_walkthrough.md # Beginner's guide to the DAG code
│   └── demo_session_guide.md       # Example inputs for live elicitation mode
│
├── figures/
│   ├── ground_truth_dag.png        # Reference DAG visualization
│   └── dag_comparison.png          # Side-by-side color-coded comparison
│
├── data/
│   ├── simulated_supply_chain.csv  # Simulated dataset (2,000 observations, 12 variables)
│   └── dataco_processed.csv        # Processed real data subset
│
└── my notes/
    └── authors_note.md             # 3-page pedagogical report
```

---

## The Human Decision Node

The notebook includes a mandatory hard stop where every proposed edge must be explicitly accepted or rejected before the pipeline continues:

```python
validated_edges = [
    # ("geopolitical_risk", "fuel_prices"),    # VALIDATE: mechanism?
    # ("fuel_prices", "shipping_cost"),        # VALIDATE: direct or mediated?
    # ...
]

assert len(validated_edges) > 0, "No edges validated. Review before proceeding."
```

The analyst uncomments only the edges they can defend. Rejected edges are logged with reasoning. The notebook does not proceed until this cell is edited.

---

## References

- Chopra, S. & Sodhi, M.S. (2004). "Managing Risk to Avoid Supply-Chain Breakdown." *MIT Sloan Management Review*, 46(1), 53-61.
- Ho, W. et al. (2015). "Supply Chain Risk Management: A Literature Review." *International Journal of Production Research*, 53(16), 5031-5069.
- Bai, X. et al. (2024). "The Causal Effects of Global Supply Chain Disruptions." CEPR/VoxEU.
- Tang, C.S. (2006). "Perspectives in Supply Chain Risk Management." *International Journal of Production Economics*, 103(2), 451-488.
- Kleindorfer, P.R. & Saad, G.H. (2005). "Managing Disruption Risks in Supply Chains." *Production and Operations Management*, 14(1), 53-68.
- Pearl, J. (2009). *Causality: Models, Reasoning, and Inference.* Cambridge University Press.
- Constante, F. et al. (2019). "DataCo SMART SUPPLY CHAIN FOR BIG DATA ANALYSIS." Mendeley Data, V5.

Full edge-by-edge citations: `docs/ground_truth_dag_citations.md`

---

## Dependencies

```
anthropic
pgmpy
networkx
matplotlib
numpy
pandas
scikit-learn
```

---

*Built by Abisha Vadukoot | Northeastern University | April 2026*