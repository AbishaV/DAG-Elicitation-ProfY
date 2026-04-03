# Ground Truth Reference DAG — Edge-by-Edge Citations
## Supply Chain Disruption Domain | Chapter 12

---

## Source Key

| Code | Full Citation |
|------|--------------|
| **CS04** | Chopra, S. & Sodhi, M.S. (2004). "Managing Risk to Avoid Supply-Chain Breakdown." *MIT Sloan Management Review*, 46(1), 53–61. |
| **T06** | Tang, C.S. (2006). "Perspectives in Supply Chain Risk Management." *International Journal of Production Economics*, 103(2), 451–488. |
| **KS05** | Kleindorfer, P.R. & Saad, G.H. (2005). "Managing Disruption Risks in Supply Chains." *Production and Operations Management*, 14(1), 53–68. |
| **Ho15** | Ho, W., Zheng, T., Yildiz, H. & Talluri, S. (2015). "Supply Chain Risk Management: A Literature Review." *International Journal of Production Research*, 53(16), 5031–5069. |
| **BFZ24** | Bai, X., Fernandez-Villaverde, J., Li, Y. & Zanetti, F. (2024). "The Causal Effects of Global Supply Chain Disruptions." CEPR Discussion Paper / VoxEU. |
| **LTS25** | Lucker, F., Timonina-Farkas, A. & Seifert, R.W. (2025). "Balancing Resilience and Efficiency: A Literature Review on Overcoming Supply Chain Disruptions." *Production and Operations Management*. |
| **CML24** | Syntetos, A.A. et al. (2024/2025). "Causal Machine Learning for Supply Chain Risk Prediction and Intervention Planning." *International Journal of Production Research*. |
| **SC22** | Chopra, S. & Meindl, P. (2022). *Supply Chain Management: Strategy, Planning, and Operations*, 7th ed. Pearson. |
| **FTI22** | FTI Consulting (2022). "Supply Chain Disruption — the Risk to Global Economic Recovery." Industry report. |

---

## DAG Summary

- **Nodes**: 12
- **Edges**: 19
- **Target outcomes**: delivery_delays, shipping_cost
- **Exogenous roots** (no parents): geopolitical_risk, demand_volatility, labor_shortages

---

## Edge-by-Edge Justification

### E01: geopolitical_risk → fuel_prices

**Mechanism**: Geopolitical conflicts (wars, sanctions, trade disputes) disrupt energy markets, causing fuel price spikes. The Russia-Ukraine conflict directly caused European energy price surges and restructured fuel supply chains.

**Sources**: CS04 (disruption risk category); FTI22 (fuel price increases from conflict-driven supply restructuring); BFZ24 (supply chain disturbances affecting transportation costs).

---

### E02: geopolitical_risk → port_congestion

**Mechanism**: Geopolitical instability leads to port closures, vessel rerouting through alternate (often more congested) routes, and trade restriction bottlenecks. Houthi attacks in the Red Sea forced rerouting around the Cape of Good Hope, causing congestion at alternate ports.

**Sources**: BFZ24 (port congestion as primary measure of supply chain disruption); FTI22 (port congestion from conflict-driven rerouting).

---

### E03: geopolitical_risk → raw_material_availability

**Mechanism**: Sanctions, embargoes, and trade restrictions limit access to raw materials. Export controls on rare earths, semiconductor materials, or energy commodities directly reduce material availability for downstream manufacturers.

**Sources**: Ho15 (macro risk factors including political instability affecting supply); T06 (geopolitical disruption as supply risk driver); CS04 (disruption risk to procurement).

---

### E04: geopolitical_risk → supplier_reliability

**Mechanism**: Political instability in supplier regions reduces supplier ability to deliver consistently. Conflict, regime change, or sanctions can shut down supplier operations entirely.

**Sources**: Ho15 (supplier failure driven by macro factors including geopolitical instability); KS05 (disruption risks to supplier base); T06 (supplier reliability affected by external disruption events).

---

### E05: fuel_prices → shipping_cost

**Mechanism**: Fuel (bunker fuel) is a primary direct cost component of maritime and overland freight. Fuel price increases pass through to shipping rates via fuel surcharges.

**Sources**: FTI22 (freight rate increases driven by fuel cost recovery); BFZ24 (transportation costs as proximate cause of supply chain cost increases); SC22 (transportation cost structure).

---

### E06: fuel_prices → production_capacity

**Mechanism**: Energy costs are a major input to manufacturing. Sustained fuel/energy price increases raise production costs, making some production lines uneconomical and reducing effective capacity.

**Sources**: CS04 (capacity risk driven by cost pressures); SC22 (production economics); T06 (manufacturing risk factors include input cost variability).

---

### E07: port_congestion → shipping_cost

**Mechanism**: Port congestion imposes demurrage charges, detention fees, and congestion surcharges. Shippers pay premiums to access capacity at congested ports or reroute to costlier alternatives.

**Sources**: BFZ24 (congestion as direct driver of shipping cost increases); FTI22 (cost escalation from port congestion).

---

### E08: port_congestion → delivery_delays

**Mechanism**: Ships waiting at congested ports cannot unload on schedule. The delay propagates downstream through the supply chain to final delivery timelines.

**Sources**: BFZ24 (port congestion measured in ship-hours of delay); FTI22 (port congestion as cause of delivery delays); CS04 (delays driven by infrastructure bottlenecks).

---

### E09: labor_shortages → port_congestion

**Mechanism**: Dockworker and logistics labor shortages reduce port throughput. Fewer workers means slower loading/unloading, creating backlogs that manifest as congestion.

**Sources**: CS04 (labor disputes as disruption risk driver); Ho15 (infrastructural risk factors include labor availability); LTS25 (recurrent risks from coordination problems including labor constraints).

---

### E10: labor_shortages → production_capacity

**Mechanism**: Manufacturing workforce shortages directly limit production output. Factories cannot run at full capacity without adequate staffing.

**Sources**: CS04 (capacity risk from labor constraints); KS05 (disruption risk to production capacity); Ho15 (manufacturing risk factors include labor availability).

---

### E11: raw_material_availability → production_capacity

**Mechanism**: Production requires raw material inputs. Material shortages force production slowdowns, line stoppages, or reduced output.

**Sources**: T06 (material unavailability reduces production); SC22 (production planning depends on material supply); CS04 (procurement risk category).

---

### E12: supplier_reliability → raw_material_availability

**Mechanism**: Unreliable suppliers deliver late, deliver defective materials, or fail to deliver entirely. This directly reduces the availability of raw materials for the buyer's production.

**Sources**: Ho15 (supplier evaluation considers quality, on-time delivery, and capacity); T06 (supplier disruption as driver of material shortage); CML24 (supplier node as direct causal influence on downstream variables).

---

### E13: supplier_reliability → order_lead_time

**Mechanism**: Unreliable suppliers have variable and longer lead times. Buyers face uncertainty in when orders will arrive, extending effective lead times for planning purposes.

**Sources**: CML24 (supplier characteristics as causal drivers of lead time and delay); Ho15 (late delivery as consequence of poor supplier reliability); LTS25 (lead time variability from supply uncertainty).

---

### E14: production_capacity → inventory_levels

**Mechanism**: Reduced production capacity means fewer finished goods produced, which directly lowers inventory available for distribution and sale.

**Sources**: SC22 (inventory as function of production output and demand); CS04 (inventory risk driven by supply-side constraints); T06 (manufacturing disruption affects downstream inventory).

---

### E15: demand_volatility → inventory_levels

**Mechanism**: Volatile demand creates mismatches between stock and consumption. Demand surges deplete inventory; demand drops create overstock. The depletion pathway is more relevant for delivery delays.

**Sources**: CS04 (demand/forecast risk directly affects inventory levels); SC22 (demand uncertainty drives safety stock decisions and stockout risk); T06 (demand risk as primary category affecting inventory management).

---

### E16: demand_volatility → order_lead_time

**Mechanism**: Demand surges overload the order processing and fulfillment pipeline, extending lead times. When everyone orders simultaneously, the queue lengthens.

**Sources**: CS04 (delay risk driven by demand surges overwhelming capacity); LTS25 (demand uncertainty contributes to lead time variability); SC22 (lead time as function of system load).

---

### E17: order_lead_time → delivery_delays

**Mechanism**: Longer order lead times increase the probability and magnitude of delivery delays. With more time between order placement and expected delivery, more can go wrong and compressed timelines become harder to meet.

**Sources**: CML24 (lead time as causal antecedent of delivery delay); CS04 (delays driven by long and variable lead times); LTS25 (lead time variability as driver of delivery risk).

---

### E18: inventory_levels → delivery_delays

**Mechanism**: Low inventory means orders cannot be fulfilled from stock. When inventory is depleted, customers must wait for replenishment, causing delays. This is the classic stockout-to-delay pathway.

**Sources**: CS04 (insufficient inventory leads to inability to meet demand); SC22 (service level depends on inventory position); LTS25 (safety inventory as mitigation for delivery delays, implying the causal link).

---

### E19: inventory_levels → shipping_cost

**Mechanism**: When inventory is low and demand is present, firms resort to expedited or emergency shipping (air freight instead of sea, express courier instead of standard) to avoid stockouts. These expedited modes cost significantly more.

**Sources**: LTS25 (emergency sourcing and expedited shipping as costly alternatives triggered by low inventory); CS04 (trade-off between inventory costs and expediting costs); SC22 (transportation mode choice driven by urgency).

---

## Edges Explicitly Excluded

These are relationships a reader or an LLM might expect but that were deliberately left out of the ground truth. They serve as test cases for the elicitation agent.

| Proposed Edge | Why Excluded |
|---------------|-------------|
| fuel_prices → delivery_delays | Mediated, not direct. Fuel prices affect delays only through shipping cost and port congestion. Carriers charge more but don't slow down. |
| demand_volatility → shipping_cost | Mediated through inventory_levels. Demand affects shipping cost only when it depletes inventory, triggering expedited shipping. |
| geopolitical_risk → delivery_delays | Mediated through multiple pathways. Geopolitical risk operates on delays through port congestion, supplier reliability, and raw material availability. No defensible direct mechanism. |
| fuel_prices → order_lead_time | Weak and indirect. Fuel prices might theoretically affect transportation speed, but carriers adjust surcharges rather than transit times. |
| shipping_cost → delivery_delays | Reverse causation risk. High shipping costs do not cause delays; they are co-effects of the same upstream causes. |
| production_capacity → delivery_delays | Mediated through inventory_levels. Reduced production capacity affects delays only by depleting inventory. |

---

## Notes on Ground Truth Limitations

1. This is a pedagogical reference DAG, not a claim about the true causal structure of global supply chains. The real structure is far more complex, involves latent variables, feedback loops, and context-dependent mechanisms.

2. All edges are simplified to binary present/absent. Real causal relationships vary in strength, may be nonlinear, and may operate on different time scales.

3. The variable granularity is deliberately chosen for a 10-20 node teaching DAG. In a production causal model, many of these nodes would decompose into sub-graphs.

4. The excluded edges are judgment calls. A domain expert could reasonably argue for including some of them. This is precisely the kind of disagreement the elicitation agent should surface.
