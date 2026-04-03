# ProfY Demo Session Guide
## What to say when running the elicitation live

This file gives you example responses for each phase of the ProfY elicitation. Use these as a starting point when running in live mode. You don't need to copy them word for word. The goal is to show you what kind of input ProfY expects at each stage and what level of detail produces useful output.

The scenario: you're Ally, a data modeler. You've been interviewing Nora, an operations manager with 18 years of experience in supply chain logistics. You're relaying what Nora told you to ProfY, and ProfY is helping you turn that into a causal graph.

---

## Phase 1: Variable Discovery

ProfY will ask you to identify the main causal factors in supply chain disruption that could affect delivery delays.

**Example response (good detail):**

> From talking to Nora, the big drivers she keeps coming back to are port congestion, fuel prices, and geopolitical instability. Those are the external shocks. Internally, she says supplier reliability is a constant headache, and when raw materials are scarce, everything downstream slows down. Labor shortages at the docks have gotten worse since 2020 and she thinks that's a major factor in port backlogs. On the demand side, she says volatility in customer orders makes it hard to plan inventory. Production capacity gets squeezed when energy costs spike or when they can't get materials. The downstream effects she cares most about are delivery delays and shipping costs, and she sees order lead time and inventory levels as the key intermediaries.

**Example response (too vague, ProfY will push back):**

> Nora said there are a lot of things that cause delays. Supply issues, demand issues, external stuff. Costs go up when things break down.

If your response looks like the second example, ProfY will ask follow-up questions to get you to be more specific. That's working as intended.

---

## Phase 2: Edge Probing

ProfY will walk through variable pairs and ask about causal direction. You're reporting what Nora thinks about whether A causes B.

**Example responses for specific pairs:**

> **Port congestion and delivery delays**: Nora says this is direct and obvious. Ships sit at anchor waiting for berth space, containers stack up, and everything downstream gets pushed back. She's seen single port backlogs add 2-3 weeks to delivery timelines.

> **Fuel prices and shipping cost**: Direct relationship. Fuel is the single biggest variable cost component in freight. Carriers pass fuel increases through as surcharges, sometimes within days of a price spike.

> **Fuel prices and delivery delays**: Nora doesn't think fuel prices cause delays directly. Carriers don't slow down when fuel is expensive, they charge more. The cost goes up but the timeline doesn't change because of fuel alone. If anything affects timing, it's the congestion or the labor issues, not the fuel price itself.

> **Geopolitical risk and delivery delays**: Nora says this is real but indirect. When there's a conflict or sanctions, it shows up as port closures, rerouting, supplier shutdowns, material shortages. She wouldn't draw a direct arrow from geopolitics to delays. It always goes through something else first.

> **Inventory levels and shipping cost**: This one surprised me, but Nora was emphatic. When inventory drops below safety stock, the procurement team switches to air freight or expedited shipping to avoid stockouts. That costs 5-10x more than standard sea freight. Low inventory directly drives up shipping spend.

---

## Phase 3: Mechanism Questioning

ProfY will challenge specific edges and ask you to explain the mechanism. This is where weak edges get caught.

**Example of defending an edge:**

> **Why does labor shortage cause port congestion?** Nora explained that ports run on shift labor: crane operators, truck dispatchers, container handlers. When they're short-staffed, throughput drops. A port that can process 5,000 TEUs per day at full staff might only manage 3,500 short-staffed. The ships don't stop coming, so the queue builds. She said the LA/Long Beach backup in 2021 was partly a labor issue, not just volume.

**Example of catching a weak edge:**

> **Why does fuel price affect quality control?** Actually, I don't think it does. Nora didn't mention any connection between fuel costs and QC problems. That sounds like something that might show up together in the data because they both get worse during disruptions, but I can't point to a mechanism where expensive fuel causes defective products. I'd drop this one.

**Example of uncovering a mediator:**

> **Is geopolitical risk to raw material availability direct?** Nora said it depends. Sometimes it's direct, like when sanctions block a specific material export. But often it goes through supplier reliability first. A geopolitical event destabilizes a supplier's region, the supplier can't operate normally, and then material deliveries suffer. So there might be two paths here: a direct one for sanctions/embargoes and an indirect one through supplier disruption.

---

## Phase 4: Confounder Probing

ProfY will ask about common causes that might create false associations between variables.

**Example responses:**

> **Is there something driving both port congestion and shipping cost that we haven't captured?** Nora thought about this and said demand surges can do both. When everyone is ordering at once, ports get congested AND freight rates spike. But we already have demand volatility in the model. I think the question is whether demand should have a direct arrow to shipping cost, or whether that effect is fully captured through the inventory path we already have.

> **Could geopolitical risk be confounding the relationship between fuel prices and supplier reliability?** Yes, I think it is. A conflict can spike fuel prices and simultaneously disrupt suppliers in the affected region. If we didn't have geopolitical risk in the graph as a common parent of both, we might think fuel prices somehow cause supplier problems. But we do have it, so I think we're covered there.

> **Any variables missing that affect multiple things at once?** Nora mentioned regulatory changes a couple of times, like new customs inspection requirements or environmental regulations on shipping. Those could affect both port throughput and shipping costs simultaneously. But she said for the current model, the existing variables capture the main story. Regulation might be worth adding in a more detailed version.

---

## Phase 5: Checkpoint

ProfY will produce a plain-language summary of the graph. Your job here is to confirm or correct.

**Example response:**

> This looks right for the most part. Two things I'd flag: first, the summary says fuel prices "contribute to" delivery delays, but based on what Nora said, that relationship is fully mediated through shipping cost and port congestion. There shouldn't be a direct arrow. Second, the summary doesn't mention the inventory to shipping cost link, which Nora was very clear about. Low inventory triggers emergency shipping, and that's a direct cost driver. Add that in and I think we're good to take back to Nora for her review.

---

## Tips for Running Live

1. **Be specific.** ProfY can only extract structure from what you give it. "Things affect other things" produces nothing useful. Name the variables, state the direction, explain the mechanism.

2. **Disagree with ProfY.** If ProfY suggests an edge that doesn't match what your expert said, push back. The whole point of the system is that the human has final say. Your disagreements become the most valuable part of the transcript.

3. **Say "I don't know."** If you're unsure about a relationship, say so. ProfY will tag it as uncertain rather than forcing a decision. Honest uncertainty is better than a confident wrong edge.

4. **Report what the expert said, not what you think sounds right.** You're a conduit for Nora's domain knowledge. If Nora said something that surprises you, relay it faithfully and let the mechanism questioning phase test whether it holds up.