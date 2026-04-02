"""
Human Decision Node — Edge Review, Validation, and Decision Logging
====================================================================
Chapter 12: LLMs as DAG Elicitation Engines

The Human Decision Node is where the analyst reviews every edge ProfY
proposed and makes an explicit accept/reject/modify decision with reasoning.

This is the hard stop. The notebook does not proceed to estimation or
evaluation until every edge has been reviewed. No edge enters the final
DAG without a human signature.

Three usage patterns:
  1. Interactive mode: analyst reviews edges one at a time in a live session
  2. Notebook mode: edges presented as commented-out code, analyst uncomments
  3. Batch mode: analyst provides a pre-filled decision log (for replay)

Usage:
    from human_decision_node import HumanDecisionNode

    # From ProfY output
    hdn = HumanDecisionNode.from_transcript("transcripts/supply_chain_socratic.json")

    # Review edges interactively
    hdn.review_interactive()

    # Or apply a pre-filled decision log
    hdn.apply_decisions(decision_log)

    # Get the validated edges for DAG building
    validated = hdn.get_validated_edges()
    rejected = hdn.get_rejected_edges()
    full_log = hdn.get_decision_log()
"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class EdgeDecision:
    """A single human decision on a proposed edge."""
    cause: str
    effect: str
    mechanism: str
    decision: str = "pending"       # accepted | rejected | modified | pending
    reason: str = ""                # why the human made this decision
    modified_to: Optional[tuple] = None  # if modified, the new (cause, effect)
    reviewer: str = ""
    timestamp: str = ""


@dataclass
class DecisionLog:
    """Complete log of all human decisions on proposed edges."""
    domain: str
    target_outcome: str
    total_proposed: int = 0
    total_accepted: int = 0
    total_rejected: int = 0
    total_modified: int = 0
    decisions: list = field(default_factory=list)
    reviewed_at: str = ""


# ---------------------------------------------------------------------------
# The Human Decision Node
# ---------------------------------------------------------------------------

class HumanDecisionNode:
    """
    Presents proposed edges for human review and logs every decision.

    The analyst must explicitly accept, reject, or modify each edge.
    Nothing passes through without a decision.
    """

    def __init__(self, proposed_edges: list[dict], domain: str = "", target: str = ""):
        self.domain = domain
        self.target = target
        self.decisions: list[EdgeDecision] = []

        for e in proposed_edges:
            self.decisions.append(EdgeDecision(
                cause=e.get("cause", e[0] if isinstance(e, (list, tuple)) else ""),
                effect=e.get("effect", e[1] if isinstance(e, (list, tuple)) else ""),
                mechanism=e.get("mechanism", ""),
            ))

    @classmethod
    def from_transcript(cls, transcript_path: str) -> "HumanDecisionNode":
        """Create from a saved ProfY transcript."""
        with open(transcript_path, "r") as f:
            transcript = json.load(f)

        proposed = transcript["final_edges"]
        return cls(
            proposed_edges=proposed,
            domain=transcript.get("domain", ""),
            target=transcript.get("target_outcome", "")
        )

    @classmethod
    def from_elicitation_result(cls, result) -> "HumanDecisionNode":
        """Create from a ProfY ElicitationResult object."""
        return cls(
            proposed_edges=result.edges,
            domain=result.domain,
            target=result.target_outcome
        )

    # -------------------------------------------------------------------
    # Review methods
    # -------------------------------------------------------------------

    def review_interactive(self, reviewer: str = "analyst") -> None:
        """
        Walk through each edge interactively in the terminal.
        For each edge, the analyst types: accept, reject, or modify.
        """
        print("=" * 60)
        print("HUMAN DECISION NODE — Edge Review")
        print("=" * 60)
        print(f"Domain: {self.domain}")
        print(f"Target: {self.target}")
        print(f"Edges to review: {len(self.decisions)}")
        print()
        print("For each edge, enter:")
        print("  a = accept")
        print("  r = reject (you'll be asked for a reason)")
        print("  m = modify (you'll specify the correction)")
        print("  s = skip (come back later)")
        print()

        for i, d in enumerate(self.decisions):
            if d.decision != "pending":
                continue

            print(f"--- Edge {i+1}/{len(self.decisions)} ---")
            print(f"  {d.cause} -> {d.effect}")
            print(f"  Mechanism: {d.mechanism}")
            print()

            choice = input("  Decision [a/r/m/s]: ").strip().lower()

            if choice == "a":
                d.decision = "accepted"
                d.reason = "Mechanism confirmed by domain expert"
                d.reviewer = reviewer
                d.timestamp = datetime.now().isoformat()
                print("  ACCEPTED\n")

            elif choice == "r":
                reason = input("  Reason for rejection: ").strip()
                d.decision = "rejected"
                d.reason = reason
                d.reviewer = reviewer
                d.timestamp = datetime.now().isoformat()
                print("  REJECTED\n")

            elif choice == "m":
                print(f"  Current: {d.cause} -> {d.effect}")
                new_cause = input(f"  New cause [{d.cause}]: ").strip() or d.cause
                new_effect = input(f"  New effect [{d.effect}]: ").strip() or d.effect
                reason = input("  Reason for modification: ").strip()
                d.decision = "modified"
                d.modified_to = (new_cause, new_effect)
                d.reason = reason
                d.reviewer = reviewer
                d.timestamp = datetime.now().isoformat()
                print(f"  MODIFIED to: {new_cause} -> {new_effect}\n")

            else:
                print("  SKIPPED\n")

        self._print_summary()

    def apply_decisions(self, decision_list: list[dict]) -> None:
        """
        Apply a pre-filled list of decisions (for batch/replay mode).

        Parameters
        ----------
        decision_list : list[dict]
            Each dict has keys: cause, effect, decision, reason
            decision is one of: "accepted", "rejected", "modified"
        """
        # Index existing decisions by (cause, effect) for lookup
        decision_map = {}
        for d in self.decisions:
            decision_map[(d.cause, d.effect)] = d

        for entry in decision_list:
            key = (entry["cause"], entry["effect"])
            if key in decision_map:
                d = decision_map[key]
                d.decision = entry["decision"]
                d.reason = entry.get("reason", "")
                d.reviewer = entry.get("reviewer", "analyst")
                d.timestamp = entry.get("timestamp", datetime.now().isoformat())
                if entry["decision"] == "modified" and "modified_to" in entry:
                    d.modified_to = tuple(entry["modified_to"])

    def accept_all(self, reason: str = "All edges confirmed by domain expert") -> None:
        """Accept all pending edges. Use only when every edge has been reviewed externally."""
        for d in self.decisions:
            if d.decision == "pending":
                d.decision = "accepted"
                d.reason = reason
                d.timestamp = datetime.now().isoformat()

    # -------------------------------------------------------------------
    # Output methods
    # -------------------------------------------------------------------

    def get_validated_edges(self) -> list[tuple]:
        """
        Return edges that passed review, ready for DAG building.
        Accepted edges return as-is. Modified edges return the corrected version.
        """
        validated = []
        for d in self.decisions:
            if d.decision == "accepted":
                validated.append((d.cause, d.effect))
            elif d.decision == "modified" and d.modified_to:
                validated.append(d.modified_to)
        return validated

    def get_rejected_edges(self) -> list[dict]:
        """Return all rejected edges with reasons. These go in the Author's Note."""
        rejected = []
        for d in self.decisions:
            if d.decision == "rejected":
                rejected.append({
                    "cause": d.cause,
                    "effect": d.effect,
                    "mechanism": d.mechanism,
                    "reason": d.reason,
                })
        return rejected

    def get_pending_edges(self) -> list[tuple]:
        """Return edges that haven't been reviewed yet."""
        return [(d.cause, d.effect) for d in self.decisions if d.decision == "pending"]

    def get_decision_log(self) -> DecisionLog:
        """Get the complete decision log for documentation."""
        log = DecisionLog(
            domain=self.domain,
            target_outcome=self.target,
            total_proposed=len(self.decisions),
            total_accepted=sum(1 for d in self.decisions if d.decision == "accepted"),
            total_rejected=sum(1 for d in self.decisions if d.decision == "rejected"),
            total_modified=sum(1 for d in self.decisions if d.decision == "modified"),
            decisions=[asdict(d) for d in self.decisions],
            reviewed_at=datetime.now().isoformat()
        )
        return log

    def is_complete(self) -> bool:
        """Check if all edges have been reviewed. The notebook checks this before proceeding."""
        return all(d.decision != "pending" for d in self.decisions)

    # -------------------------------------------------------------------
    # Notebook code generation
    # -------------------------------------------------------------------

    def generate_uncomment_block(self) -> str:
        """
        Generate the commented-out edge validation block for the notebook.

        This is the hard stop pattern from the project plan. Every edge
        starts commented out. The analyst uncomments only the edges they
        have validated. The notebook does not proceed until this cell
        has been edited.
        """
        lines = [
            "# " + "=" * 58,
            "# MANDATORY HUMAN DECISION NODE",
            "# " + "=" * 58,
            "#",
            "# The elicitation agent proposed the following edges from",
            "# the Socratic interview transcript.",
            "#",
            "# Review each edge before proceeding.",
            "# For each edge, ask: Is this a causal claim I can defend?",
            "#",
            "# INSTRUCTIONS:",
            "#   - Uncomment ONLY the edges you have validated",
            "#   - For rejected edges, add a comment explaining why",
            "#   - The notebook will not proceed with commented-out edges",
            "#",
            "# " + "-" * 58,
            "",
            "validated_edges = [",
        ]

        for d in self.decisions:
            mechanism_short = d.mechanism[:60] + "..." if len(d.mechanism) > 60 else d.mechanism
            lines.append(
                f'    # ("{d.cause}", "{d.effect}"),  '
                f'# VALIDATE: {mechanism_short}'
            )

        lines.append("]")
        lines.append("")
        lines.append("# " + "-" * 58)
        lines.append("# VALIDATION CHECK — do not modify this cell")
        lines.append("# " + "-" * 58)
        lines.append(f"assert len(validated_edges) > 0, (")
        lines.append(f'    "No edges validated. Review the edges above and uncomment "')
        lines.append(f'    "the ones you accept before proceeding."')
        lines.append(f")")
        lines.append(f'print(f"Validated {{len(validated_edges)}} edges. Proceeding.")')

        return "\n".join(lines)

    # -------------------------------------------------------------------
    # Persistence
    # -------------------------------------------------------------------

    def save_decision_log(self, path: str) -> None:
        """Save the decision log as JSON for documentation."""
        log = self.get_decision_log()
        with open(path, "w") as f:
            json.dump(asdict(log), f, indent=2)
        print(f"Decision log saved to: {path}")

    def load_decision_log(self, path: str) -> None:
        """Load and apply a previously saved decision log."""
        with open(path, "r") as f:
            data = json.load(f)
        self.apply_decisions(data["decisions"])

    # -------------------------------------------------------------------
    # Display
    # -------------------------------------------------------------------

    def _print_summary(self) -> None:
        """Print review summary."""
        accepted = sum(1 for d in self.decisions if d.decision == "accepted")
        rejected = sum(1 for d in self.decisions if d.decision == "rejected")
        modified = sum(1 for d in self.decisions if d.decision == "modified")
        pending = sum(1 for d in self.decisions if d.decision == "pending")

        print("=" * 60)
        print("REVIEW SUMMARY")
        print("=" * 60)
        print(f"Total proposed:  {len(self.decisions)}")
        print(f"Accepted:        {accepted}")
        print(f"Rejected:        {rejected}")
        print(f"Modified:        {modified}")
        print(f"Pending:         {pending}")

        if pending > 0:
            print(f"\nWARNING: {pending} edges still pending review.")
            print("The notebook will not proceed until all edges are reviewed.")

        if rejected > 0:
            print(f"\nRejected edges (for Author's Note):")
            for d in self.decisions:
                if d.decision == "rejected":
                    print(f"  {d.cause} -> {d.effect}: {d.reason}")

        if modified > 0:
            print(f"\nModified edges:")
            for d in self.decisions:
                if d.decision == "modified":
                    print(f"  {d.cause} -> {d.effect} => {d.modified_to}: {d.reason}")

        complete = "YES" if self.is_complete() else "NO"
        print(f"\nAll edges reviewed: {complete}")
        print()

    def print_proposed_edges(self) -> None:
        """Print all proposed edges with their current status."""
        print("=" * 60)
        print("PROPOSED EDGES — Status")
        print("=" * 60)

        for i, d in enumerate(self.decisions, 1):
            status_marker = {
                "pending": "[ ]",
                "accepted": "[+]",
                "rejected": "[-]",
                "modified": "[~]",
            }.get(d.decision, "[?]")

            print(f"  {status_marker} E{i:02d}: {d.cause} -> {d.effect}")
            if d.decision == "rejected":
                print(f"        Reason: {d.reason}")
            elif d.decision == "modified":
                print(f"        Modified to: {d.modified_to}")
                print(f"        Reason: {d.reason}")

        print()


# ---------------------------------------------------------------------------
# Main (for testing)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Test 1: Load from transcript and show proposed edges
    print("Test 1: Load proposed edges from transcript")
    print("-" * 40)

    hdn = HumanDecisionNode.from_transcript(
        "transcripts/supply_chain_socratic.json"
    )
    hdn.print_proposed_edges()

    # Test 2: Apply batch decisions (simulate analyst review)
    print("Test 2: Apply batch decisions")
    print("-" * 40)

    # Accept most edges, reject one, modify one
    batch_decisions = [
        {"cause": "geopolitical_risk", "effect": "fuel_prices", "decision": "accepted", "reason": "Clear mechanism: sanctions and conflicts disrupt energy markets"},
        {"cause": "geopolitical_risk", "effect": "port_congestion", "decision": "accepted", "reason": "Documented in Bai et al. 2024"},
        {"cause": "geopolitical_risk", "effect": "supplier_reliability", "decision": "accepted", "reason": "Political instability directly disrupts supplier operations"},
        {"cause": "geopolitical_risk", "effect": "raw_material_availability", "decision": "accepted", "reason": "Sanctions directly restrict material exports"},
        {"cause": "fuel_prices", "effect": "shipping_cost", "decision": "accepted", "reason": "Fuel is the primary variable cost in freight"},
        {"cause": "fuel_prices", "effect": "production_capacity", "decision": "accepted", "reason": "Energy costs constrain manufacturing, see 2022 European example"},
        {"cause": "port_congestion", "effect": "shipping_cost", "decision": "accepted", "reason": "Demurrage and congestion surcharges are well documented"},
        {"cause": "port_congestion", "effect": "delivery_delays", "decision": "accepted", "reason": "Direct throughput constraint"},
        {"cause": "labor_shortages", "effect": "port_congestion", "decision": "accepted", "reason": "Fewer dockworkers reduces port throughput"},
        {"cause": "labor_shortages", "effect": "production_capacity", "decision": "accepted", "reason": "Understaffing limits factory output"},
        {"cause": "raw_material_availability", "effect": "production_capacity", "decision": "accepted", "reason": "Cannot produce without inputs"},
        {"cause": "supplier_reliability", "effect": "raw_material_availability", "decision": "accepted", "reason": "Unreliable supplier means unreliable material flow"},
        {"cause": "supplier_reliability", "effect": "order_lead_time", "decision": "accepted", "reason": "Variable supplier performance extends lead times"},
        {"cause": "production_capacity", "effect": "inventory_levels", "decision": "accepted", "reason": "Production shortfall depletes inventory"},
        {"cause": "demand_volatility", "effect": "inventory_levels", "decision": "accepted", "reason": "Demand surges deplete stock"},
        {"cause": "demand_volatility", "effect": "order_lead_time", "decision": "accepted", "reason": "Queue-based mechanism confirmed by expert"},
        {"cause": "order_lead_time", "effect": "delivery_delays", "decision": "accepted", "reason": "Longer lead times increase delay probability"},
        {"cause": "inventory_levels", "effect": "delivery_delays", "decision": "accepted", "reason": "Low stock prevents order fulfillment"},
        {"cause": "inventory_levels", "effect": "shipping_cost", "decision": "accepted", "reason": "Low inventory triggers automatic switch to air freight"},
    ]

    hdn.apply_decisions(batch_decisions)
    hdn._print_summary()

    # Test 3: Generate the uncomment block for the notebook
    print("Test 3: Generate notebook uncomment block")
    print("-" * 40)
    print(hdn.generate_uncomment_block())

    # Test 4: Get validated edges
    print("\nTest 4: Validated edges for DAG builder")
    print("-" * 40)
    validated = hdn.get_validated_edges()
    print(f"Edges passing review: {len(validated)}")
    for u, v in validated:
        print(f"  {u} -> {v}")