# Author's Note
## Chapter 12: LLMs as DAG Elicitation Engines

**Author:** Abisha Vadukoot

---

## Page 1: Design Choices

The first challenge wasn't building anything. It was understanding what the chapter needed to accomplish. The project plan described a system that uses LLMs to help domain experts build causal graphs. That sounds straightforward in a sentence, but the gap between "LLM-assisted DAG elicitation" as a concept and a working notebook with estimation results is enormous. Before writing a single line of code, I had to answer a series of questions that shaped every decision downstream.

**Why supply chain disruption?** The domain needed to satisfy competing requirements. It had to be intuitive enough that a reader without industry experience could follow the logic (everyone understands "ships stuck at port means packages arrive late"). It had to be complex enough to produce a non-trivial DAG, something with 10 or more nodes, multiple causal pathways, and confounders that actually matter for estimation. And it had to have published academic literature establishing causal relationships, because the ground truth DAG needs citations, not opinions. Supply chain risk management checked all three. The literature is deep (Chopra and Sodhi 2004, Ho et al. 2015, Tang 2006), the mechanisms are well-studied, and the domain has enough moving parts to make evaluation meaningful without being intractable.

**Why 12 nodes and not 16?** The candidate variable list started at 16. Four were cut during the design phase, each for a specific reason. Warehouse capacity was merged into inventory levels because at this DAG's granularity, separating storage capacity from actual inventory position adds a node without adding structural insight. Transportation mode choice was dropped because it's a decision variable, something the system responds with, not a cause within it. Customer satisfaction would have dangled at the bottom of the graph as a leaf with a single parent, which is pedagogically thin. Quality control failures had the weakest connections to the rest of the graph, but it turned out to be more valuable as an excluded variable: it's exactly the kind of edge an LLM would hallucinate ("fuel prices cause quality control failures"), making it a better test case for the failure mode analysis than a node in the ground truth.

**Why SHD as the primary metric?** Structural Hamming Distance counts three types of errors (missing edges, extra edges, reversed edges) in a single number. That makes it immediately interpretable: an SHD of 4 means four structural mistakes. The alternative metrics I considered, like the Bayesian Information Criterion score or normalized edit distance, either require fitted probability distributions (which we don't have at the structural comparison stage) or don't distinguish between edge types (a reversal is fundamentally different from a missing edge, and the metric should reflect that). SHD also decomposes cleanly into precision and recall over edges, which lets you separate "did the agent find too many edges" from "did it miss real ones."

**Why one prompting strategy built, others discussed?** The project plan called for comparing three prompting strategies: open-ended Socratic, structured pairwise, and a hybrid. I built the Socratic approach because it best demonstrates ProfY's coaching role, the back-and-forth that surfaces mechanisms and catches shortcuts. The structured pairwise approach (systematically asking about every variable pair) would be more exhaustive but also more mechanical, and the risk of leading the expert toward yes-answers is higher. Rather than building three mediocre implementations, I built one thorough one and discussed the tradeoffs of the others in the chapter prose. The comparison is described conceptually rather than run experimentally.

**What was cut for scope?** Multi-snapshot checkpoints (showing the DAG at each phase, not just the end), a deployed web application version of ProfY, and a full prompt sensitivity experiment with statistical comparison across strategies. All of these would strengthen the chapter but none were achievable at the quality level I wanted within the timeline.

---

## Page 2: Tool Usage

AI tools were used extensively in this project, but always as assistants, never as decision-makers. Every structural choice, every edge in the DAG, every architectural decision went through deliberation before it was accepted.

**Ground truth DAG construction.** The reference DAG was built through an iterative process. I started with the candidate variable list from the project plan and researched published supply chain literature to identify which causal relationships had empirical or theoretical support. The initial graph had too many nodes. Through multiple rounds of discussion and pressure-testing, variables were merged, cut, or reclassified. Every edge in the final 12-node, 19-edge graph has a cited source, and every excluded edge has a documented reason for exclusion. The exclusion list turned out to be as valuable as the inclusion list, because it defines what the elicitation agent should not propose.

**ProfY engine design.** The five-phase structure (variable discovery, edge probing, mechanism questioning, confounder probing, checkpoint) emerged from thinking through what kinds of errors each phase needs to catch. Variable discovery catches incompleteness. Edge probing catches missing connections. Mechanism questioning catches shortcuts and spurious correlations. Confounder probing catches hidden common causes. The checkpoint catches miscommunication between the analyst and the expert. The phase order matters: you can't probe edges before you have variables, and you can't question mechanisms before you have proposed edges.

**Human Decision Node.** The uncomment-to-validate pattern was a deliberate design choice. It creates a physical barrier in the notebook: the code will not run past that cell until the analyst has edited it. This is more robust than a confirmation dialog or a boolean flag because it requires the analyst to read each edge and make an affirmative choice. The decision log captures every acceptance and rejection with reasoning, which feeds directly into this Author's Note.

**Where AI output was corrected.** The most significant correction was in the DAG structure itself. Early drafts included a direct edge from fuel prices to delivery delays, which sounds plausible but has no defensible mechanism (carriers charge more when fuel is expensive, they don't slow down). This edge was removed after pressure-testing the mechanism: "If we could experimentally set fuel prices to zero, would delivery timelines change? No, only costs would change." The same scrutiny was applied to a proposed direct edge from geopolitical risk to delivery delays, which was replaced by four mediated pathways (through fuel prices, port congestion, supplier reliability, and raw material availability).

The visualization module went through color scheme revisions. The initial node coloring used teal and coral, which were too similar on screen and made the DAG hard to read. This was caught during notebook testing and replaced with blue, yellow, and red, three clearly distinct colors for exogenous roots, mediators, and outcomes respectively.

The real data analysis with the DataCo dataset produced an unexpected finding: the doubly robust estimate barely moved from the naive difference. The initial reaction was that something was wrong with the code. After investigation, the finding was correct: the available confounders (order quantity, product price, market, customer segment) simply don't predict shipping mode assignment well enough for the adjustment to matter. This became one of the chapter's most honest and valuable findings rather than a bug to fix.

---

## Page 3: Self-Assessment

**Rubric scoring (self-assessed):**

*Causal Rigor (35 pts): 30/35.* The DAG is literature-grounded and every edge is cited. Backdoor adjustment sets are computed correctly via pgmpy. The identification strategy is stated formally. The gap: the do-calculus application is implicit (using the backdoor criterion) rather than explicitly walking through the full do-calculus derivation. A more rigorous treatment would show the algebraic steps.

*Technical Implementation (25 pts): 22/25.* The code runs end to end, handles malformed input (cycle detection, orphan nodes), and includes sensitivity analysis. The Human Decision Node is explicit and logged. The gap: the live API mode was not tested in the final submission. The replay mode works perfectly, but the live mode remains validated only in isolation, not as part of the full notebook flow.

*Pedagogical Clarity (20 pts): 18/20.* The notebook opens with intuition before formalism. SHD is introduced through a visual example (the color-coded comparison plot) before the formula. The prose is direct and uses concrete examples. The gap: some of the mechanism explanations in the elicitation transcript could be more detailed for readers completely new to supply chain operations.

*Relative Quality (20 pts): 16/20.* The notebook is complete and runnable. The failure analysis is honest. The real data section adds credibility. The gap: the project builds one prompting strategy rather than comparing multiple strategies experimentally. A top-tier submission would include saved transcripts from at least two different approaches with SHD comparison.

**Known weaknesses:**

The sensitivity analysis uses simulated data, not real observational data. The simulated data was generated to be consistent with the ground truth DAG, which means the backdoor adjustment is guaranteed to work. Real data, as the DataCo section demonstrates, doesn't come with that guarantee. The simulated results look better than real-world performance would be.

The prompt sensitivity comparison is discussed in prose but not demonstrated experimentally. Different prompting strategies would produce different DAGs with different SHD scores. Showing this empirically would strengthen the chapter's argument about the role of methodology in elicitation quality.

The elicitation transcript represents an ideal session where the expert is cooperative, knowledgeable, and articulate. Real expert interviews involve uncertainty ("I'm not sure about that relationship"), disagreement ("I think the direction is the opposite"), and incomplete knowledge ("I don't know what happens upstream of my department"). ProfY handles some of these through the uncertainty tagging mechanism, but the saved transcript doesn't demonstrate this.

**What I'd do with more time:**

Run the elicitation live with an actual domain expert (not a simulated transcript) and document where ProfY's coaching helped vs. where it anchored the expert toward a wrong answer. Compare at least two prompting strategies experimentally with SHD scores. Integrate a causal discovery algorithm (PC or FCI) to test the elicited DAG against the DataCo data, bridging into Chapter 13's territory. Build a lightweight web interface for ProfY so domain experts could use it without touching a Jupyter notebook.