# Chapter 12: The Specification Bottleneck

## How to Use an LLM That Can't Reason Causally to Help You Build the Causal Graph You Need

---

### Section 1: Core Claim

In March 2000, a lightning strike caused a fire at a Philips semiconductor plant in Albuquerque, New Mexico. The plant supplied radio frequency chips to two major customers: Nokia and Ericsson. Both companies lost their chip supply overnight.

Nokia had mapped its supply chain dependencies. It knew the Philips plant was a single point of failure. Within days, Nokia activated backup suppliers and secured remaining Philips inventory from other facilities. Ericsson had not mapped its dependencies. The causal structure was simple — single-source supplier → total dependency → catastrophic production halt — and everyone at Ericsson knew it informally. But nobody had documented it in a formal structure that would have triggered a risk mitigation strategy before the fire. If someone had run even a basic variable discovery exercise — "what are the single points of failure in our supply chain?" — the node *single-source supplier* would have appeared, the edge to *production halt* would have been drawn, and the contingency plan would have existed before it was needed. Instead, Ericsson lost $400 million in revenue and exited the mobile phone handset market within a year.

Twenty years later, the failure repeated at scale. When COVID-19 disrupted global supply chains in 2020–2021, the naive analysis was straightforward: demand surges caused port congestion caused delivery delays. That's the edge everyone drew. But the actual causal structure had multiple confounded pathways operating simultaneously. Labor shortages reduced port throughput at LA/Long Beach. Pandemic vessel rerouting created congestion at alternate ports. Inventory depletion forced emergency shipping that further clogged the system. Each pathway contributed to delays, but they were entangled — correlated with demand surges but not caused by them. Without a structured elicitation to separate the pathways, the intervention targeted the wrong cause. You cannot fix port labor shortages by telling people to order less.

These are supply chain examples because that's this chapter's domain. But the specification bottleneck is universal. Replace "single-source supplier" with "single funding source" and you have the same vulnerability in nonprofit operations. Replace "confounded port congestion pathways" with "confounded treatment pathways" and you have the same misattribution problem in clinical trials. The failure mode is always the same: the causal structure was either unknown or undocumented, and the cost was paid in dollars, in delayed treatments, or in policies that targeted the wrong cause.

The hardest step in causal inference is not estimation. It's specification.

You can have the cleanest doubly robust estimator in the literature, the most elegant inverse probability weights, the tightest confidence intervals. None of it matters if your causal graph is wrong. If you've drawn an arrow from A to B when the world runs from B to A, your adjustment set is wrong, your estimates are biased, and your conclusions are confident in the wrong direction. The math will be beautiful. The answer will be false.

And yet — look at where the field spends its energy. Open any causal inference textbook. The estimation chapters are long, detailed, and full of worked examples. The chapter on how to actually build the DAG is short, hand-wavy, and often reduced to a single instruction: "consult domain experts." As if that were a method rather than a wish.

The Ericsson fire was a variable discovery failure — the relevant node existed in the world but not in any formal structure. The COVID port crisis was a confounder separation failure — the pathways existed but nobody disentangled them from the obvious direct cause. Both would have been caught by the method this chapter teaches.

This chapter turns the wish into a method. Not by replacing domain experts with machines — Chapter 11 established that LLMs are unreliable causal reasoners, and nothing here contradicts that finding. Instead, by using LLMs for what they are actually good at: running a structured conversation. The LLM doesn't decide what causes what. It asks the right questions in the right order. The expert provides the causal knowledge. The LLM provides the scaffolding that keeps the conversation complete, documented, and auditable.

---

### Section 2: Logical Method

The method is Socratic knowledge elicitation with iterative graph refinement.

Imagine you're trying to draw a map of a city you've never visited. You can't go there — but you can talk to someone who's lived there for twenty years. The question is how to run that conversation so you don't miss neighborhoods, don't draw roads that don't exist, and don't put the hospital on the wrong side of the river.

You could ask "tell me about your city" and hope for the best. That's how most DAG elicitation works today: an unstructured conversation producing a graph that reflects whatever the expert happened to remember that day.

Or you could ask in five structured phases, each designed to catch a different kind of error:

**Phase 1 — Variable Discovery.** "What are the main factors that affect delivery delays and shipping costs in your supply chain?" This catches incompleteness. If you don't ask about a neighborhood, it won't appear on your map.

**Phase 2 — Edge Probing.** "Does geopolitical risk affect supplier reliability? Directly, or through something else?" This catches missing connections between variables you've already named.

**Phase 3 — Mechanism Questioning.** "You said fuel prices affect delivery delays. Walk me through the mechanism — what's the chain of events?" This is the most valuable phase. When someone says A causes C, mechanism questioning often reveals that A causes B, and B causes C, and the direct arrow is a shortcut. It also catches arrows that shouldn't exist at all — a point the case study will demonstrate in detail.

**Phase 4 — Confounder Probing.** "Is there something that might be driving both fuel prices and shipping costs at the same time?" This catches hidden common causes — the summers in the ice cream and drowning example from earlier chapters.

**Phase 5 — Checkpoint Validation.** "Here's the graph we've built so far. Does this match your understanding?" This catches miscommunication between analyst and expert.

Each phase adds variables and edges to a running graph. After each phase, the graph is validated for structure: no cycles, no orphan nodes, and basic connectivity. The LLM maintains state across phases, accumulating what it's learned.

The key architectural decision: the LLM operates as a coaching agent called ProfY. It talks to the analyst, not to the domain expert. ProfY generates the next Socratic prompt. The analyst relays it to the expert. The analyst relays the expert's answer back. ProfY extracts structured variable-edge pairs from the conversation. At no point does the LLM propose a causal relationship on its own authority.

---

### Section 3: Methodological Soundness

A method that feels rigorous is not the same as a method that is rigorous.

The validation approach compares the elicited DAG against a reference DAG built from published supply chain literature. Every edge in the reference graph is cited from at least one peer-reviewed source. The comparison metric is **Structural Hamming Distance**, or SHD — counting mistakes on the map from Section 2. You drew a road that doesn't exist? That's one. Missed one that does? That's one. Drew it going the wrong way? That's one. SHD adds them up.

Secondary metrics — precision, recall, and F1 over edges — decompose this further. Precision asks: of the edges you drew, how many are real? Recall asks: of the real edges, how many did you find? F1 balances the two.

#### Why Five Phases and Not Some Other Number

The five-phase structure is not a design preference. It maps directly to what the backdoor criterion needs to compute a valid adjustment set.

Phase 1 determines the **node set** of the DAG. If a variable isn't named here, it cannot appear in any adjustment set. Phase 2 determines the **edge set** — the skeleton. Phase 3 determines **edge directionality** and catches **false edges** — this is where the DAG separates from an undirected association map. The backdoor criterion requires knowing which way the arrows point, because direction determines which variables are confounders and which are mediators. Phase 4 identifies **common causes** — exactly the variables the backdoor criterion tells you to condition on. Phase 5 catches **translation errors** between what the expert said and what the graph encodes.

Skip any phase and the identification strategy breaks in a specific, predictable way. Skip Phase 1 and the graph is missing nodes. Skip Phase 3 and the arrows may point the wrong way. Skip Phase 4 and the confounders hide.

#### What Skipping Phase 3 Actually Costs

Here is the traceable path from one skipped question to one biased estimate.

Suppose Phase 3 is omitted. Nobody asks "how does expensive fuel slow down a delivery?" The edge fuel_prices → delivery_delays survives because it sounds plausible. Fuel and delays co-occur in every supply chain article, every dataset where both are measured.

Now the analyst asks: what is the causal effect of port congestion on delivery delays? The backdoor criterion computes the adjustment set. With the false edge in the graph, fuel_prices appears in that set. It shouldn't be there. Fuel prices affect costs, not timing.

The damage compounds. Fuel_prices is entangled with geopolitical_risk, which is a real confounder. Conditioning on fuel_prices partially blocks the variation in geopolitical_risk the analyst needs to adjust for. The correct doubly robust estimate for port congestion's effect on delivery delays is 0.45. With fuel_prices incorrectly in the adjustment set, that number shifts — not because of noise, but because the adjustment set is structurally wrong.

One skipped question. One surviving false edge. One corrupted adjustment set. One biased estimate. The domain expert in our case study killed this edge in one sentence during Phase 3: "Carriers charge more when fuel is expensive. They don't slow down." Phase 3 exists to force that sentence into the conversation before the graph is finalized.

#### The Limitation the Five Phases Cannot Fix

All five phases depend on the expert being able to name every causally relevant variable. But some confounders operate in domains the expert never observes.

Consider credit terms — the financial agreements a procurement department negotiates with shipping carriers. Credit terms affect which carriers accept the company's business (constraining shipping mode availability) and how quickly carriers prioritize shipments (affecting delivery timing). Credit terms are a common cause of both shipping mode and delivery delays. They belong in the DAG.

But the domain expert is an operations manager. She has never seen a carrier contract. No amount of Socratic questioning will surface a variable the expert doesn't know exists. Phase 1 won't catch it. Phase 4 won't catch it. The student can run all five phases perfectly and the adjustment set will still be wrong.

This is the formal limitation: the backdoor criterion computes correct adjustment sets *given the graph you provide*. It cannot tell you the graph is missing a node. The five-phase method reduces this risk but cannot eliminate it. The method is bounded by the expert's observational horizon.

This is why Chapter 13 matters. Data-driven structure learning algorithms can sometimes detect that the data is inconsistent with the assumed graph — a signal that something is missing. The expert builds the map from knowledge. The algorithm checks it against the data. Neither is complete alone.

---

### Section 4: How the LLM Operates

Chapter 11 established that LLMs are unreliable causal reasoners. Nothing here walks that finding back.

The LLM (Claude, via the Anthropic API) operates as ProfY — a coaching agent that generates structured Socratic prompts. It asks: "What are the main factors affecting your outcome variables?" It asks: "What mechanism connects A to B?" It does NOT say: "I think A causes B." It does NOT validate edges. The boundary is non-negotiable.

ProfY runs a five-phase loop, each phase with its own system prompt tuned to the specific failure mode that phase targets. The agent maintains state — accumulated variables, proposed edges, the growing graph — across all phases. The system runs in two modes: **Replay mode** reads from saved transcripts (no API key required), and **Live mode** calls the Anthropic API in real time.

What the LLM contributes is facilitation, not reasoning. It keeps the conversation on track. It translates free-form expert knowledge into structured variable-edge pairs. It remembers what's been said across a long conversation — something humans are inconsistent at during hour-long sessions. Think of it as a court reporter who also knows which questions to ask next, but who has no opinion about the testimony.

**The Human Decision Node.** After elicitation completes, every proposed edge is presented as commented-out Python code:

```python
# dag.add_edge("fuel_prices", "shipping_cost")  # Expert: direct cost driver
```

The analyst must uncomment each edge they accept. The notebook will not proceed until this cell is edited. Every rejection is logged with reasoning. This is not a soft suggestion. The code literally stops. Passive acceptance is eliminated by design.

The tools: `anthropic` for API calls, `pgmpy` for DAG structure and backdoor adjustment sets, `networkx` for graph manipulation, `matplotlib` for visualization, and `scikit-learn` for doubly robust estimation.

---

### Section 5: Case Study

#### The Setup

The domain is supply chain disruption. The target outcomes are delivery delays and shipping costs. Three characters: **Ally** (data modeler and analyst, uses ProfY as copilot), **Nora** (domain expert, operations manager with 18 years of experience), and **ProfY** (Ally's coaching agent — talks to Ally, not to Nora directly).

The ground truth DAG has 12 nodes and 19 edges. Three exogenous roots — geopolitical_risk, labor_shortages, demand_volatility — drive the system. Two target outcomes sit at the end of multiple causal pathways. Every edge is cited from published supply chain literature: Chopra and Sodhi (2004), Ho et al. (2015), Tang (2006), and others.

#### The Ideal Run

ProfY walks Ally through all five phases with Nora's input. Result: 12 variables surfaced, 19 edges proposed, SHD = 0, Precision = 1.0, Recall = 1.0, F1 = 1.0. A perfect map.

This is not the interesting result.

#### The Imperfect DAG

Four deliberate mistakes were introduced: two missing edges (fuel_prices → production_capacity, supplier_reliability → order_lead_time), one hallucinated edge (fuel_prices → delivery_delays — the edge Phase 3 would have killed), and one reversed edge (order_lead_time → demand_volatility, drawn backwards — like saying the long line at the coffee shop caused everyone to want coffee).

Result: SHD = 4, F1 = 0.865. Four mistakes that propagate into every downstream estimate.

#### What the Estimates Show

With the correct DAG, the system computes adjustment sets using the backdoor criterion, then runs doubly robust estimation.

**Port congestion → delivery delays.** Naive difference: 0.95. Doubly robust estimate, adjusting for geopolitical_risk and labor_shortages: 0.45. Nearly half of what looked like port congestion was actually geopolitical instability and labor shortages driving both congestion and delays simultaneously.

**Fuel prices → shipping cost.** Naive difference: 0.98. Doubly robust ATE: 0.51. Geopolitical risk was inflating the naive estimate through route disruptions, insurance premiums, and port delays.

Think of it like rain and traffic. The naive comparison says traffic is 0.98 worse when it rains. The adjusted estimate says rain itself accounts for 0.51. The rest is more cars on the road — a confounder correlated with rain but with its own effect on traffic.

#### Sensitivity Analysis

Removing one edge (fuel_prices → production_capacity): SHD increased by 1, F1 dropped to 0.973. A minor error, but the adjustment set is now incomplete for estimates involving production capacity.

Reversing one edge (inventory_levels → delivery_delays): SHD increased by 1, F1 dropped to 0.947. A direction error changes which variables are confounders and which are mediators. Control for a mediator and you block the causal pathway you're trying to measure. The math still runs. The answer is wrong in a way that's invisible without the correct graph.

#### The Real Data Test

The system was applied to the DataCo Smart Supply Chain dataset — 180,000 real orders with shipping mode, delivery status, order characteristics, and cost data.

Late delivery rates by shipping mode: Standard Class at 38%, First Class at 95%. First Class shipping is late almost every time — likely reflecting how "late" is defined relative to promised windows and the types of orders routed to premium shipping.

The doubly robust estimate barely moved from the naive difference. The propensity model achieved only 0.60 accuracy — barely better than a coin flip. The real confounders — inventory levels, order urgency, cost pressure from upstream disruptions — are not in the dataset.

This is the lesson simulated data cannot teach. A well-built DAG doesn't just tell you what to control for. It tells you what you're missing. The gap between what the DAG requires and what the data contains is where bias lives. No estimator, no matter how sophisticated, can adjust for variables that were never measured. The DAG is the diagnostic that tells you to stop.

#### When the Extraction Doesn't Match the Expert

The Human Decision Node catches causally wrong edges. But there is a quieter failure mode: edges that don't faithfully capture what the expert *said*.

During Phase 3, Nora described a causal chain: "When geopolitical instability hits, it disrupts suppliers, and that makes raw materials harder to get." That's a mediated pathway: geopolitical_risk → supplier_reliability → raw_material_availability. Two edges, one intermediate node.

ProfY extracted one edge: geopolitical_risk → raw_material_availability. Not wrong, exactly — but incomplete. It collapsed the pathway into a shortcut and dropped the mediator. At the Human Decision Node, the analyst sees the edge and thinks "yes, Nora said that." Because she did. The edge matches her words. It doesn't match her structure.

Similarly, when Nora said geopolitical risk "always goes through something else first" — disrupting ports, reducing supplier reliability, creating demand shocks — the faithful extraction is multiple mediated pathways, not one direct edge. The direct edge hides the causal structure and makes it impossible to identify which intermediate pathway to intervene on.

| Expert's raw statement | ProfY's extraction | Faithful extraction |
|---|---|---|
| "When geopolitical instability hits, it disrupts suppliers, and that makes raw materials harder to get." | geopolitical_risk → raw_material_availability | geopolitical_risk → supplier_reliability → raw_material_availability |

ProfY preserves both sides of this comparison — the transcript JSON stores full conversation text alongside extracted edges. The practice: before the Human Decision Node, read each raw expert statement next to its extracted edge and ask three questions. Did this compress a mediated pathway? Did the extraction infer a direction the expert never stated? Did it generalize a conditional claim into an unconditional edge?

These catch three extraction errors the Human Decision Node alone does not: **collapsed mediation** (A → B → C extracted as A → C), **direction inference** (association extracted as directed edge), and **scope shift** (conditional claim extracted as universal edge).

The limitation is honest: in a fast-moving live session, the analyst may not check every extraction in real time. The system preserves the data for post-session review. The method can make the comparison easy. It cannot make the analyst do it.

---

### Section 6: Discussion and Limitations

#### What Worked

The five-phase structure forces completeness in a way that unstructured elicitation does not. Mechanism questioning — Phase 3 — is where the system earns its value. The Human Decision Node creates a documented audit trail. Every accepted edge has a reason. Every rejected edge has a reason.

#### Failure Modes

Six failure modes recur in any LLM-assisted causal elicitation. Several are demonstrated in the case study; all deserve naming:

**Hallucinated edges** — plausible in language, wrong in the world (see the fuel_prices → delivery_delays trace in Section 3). **Reversed causation** — direction wrong (see the coffee shop line in the imperfect DAG). **Missing mediators** — direct shortcuts where the mechanism is mediated (see the extraction fidelity analysis above). **Prompt sensitivity** — different phrasings surface different variables; the five-phase structure mitigates this by asking from multiple angles. **Anchoring** — the LLM's first suggestion shapes what the expert considers; Phase 4 partially mitigates by explicitly asking "what are we missing?" **Correlation as causation** — observational text describes correlations, and the LLM may extract them as causal claims; the Human Decision Node is the backstop.

#### The Real Data Limitation

The DataCo analysis demonstrated what Section 3's latent variable discussion predicts: when the DAG requires variables the data doesn't contain, no estimator recovers the missing information. The DAG said to adjust for inventory_levels and demand_volatility. The dataset didn't have them. The propensity model barely beat chance.

A well-built DAG tells you what you need to measure. The data tells you what you have. The gap is where bias lives.

#### Student Deliverable

After completing the notebook, the student submits a DAG diagnostic report with three components. First: for each elicitation phase, identify what formal property of the DAG that phase determined and whether the property is complete — mapping Phase 1 output to the node set, Phase 2 to the edge set, Phase 3 to directionality, Phase 4 to common causes, and flagging any gaps. Second: pick one causal question from the DAG, compute the backdoor adjustment set, and for each variable in that set, state whether it is measurable in the available data. For any unmeasured variable, write one sentence explaining what bias its absence introduces and in which direction. Third: name one plausible latent confounder not in the DAG and explain why the five-phase elicitation would not have caught it — reasoning about the boundaries of the expert's observational horizon, not just the graph structure. The report is graded on whether the phase-to-formalism mapping is correct, whether the measurability audit is specific rather than vague, and whether the proposed latent confounder is genuinely outside the expert's domain of observation.

#### Bridge to Chapter 13

Chapter 11 showed that LLMs can't reason causally on their own. Chapter 12 showed that they can facilitate causal elicitation when paired with domain expertise and structured methodology. The resulting DAG is expert-driven, documented, and auditable — but bounded by the expert's observational horizon.

Chapter 13 adds the data-driven check. Given an expert-elicited DAG and imperfect observational data, can structure learning algorithms test whether the data agrees with the assumed structure? Can they suggest edges the expert missed? The expert builds the map. The algorithm checks it against the terrain.

---

**Tags:** causal graph elicitation, LLM-assisted specification, Socratic knowledge extraction, structural hamming distance, supply chain causal inference