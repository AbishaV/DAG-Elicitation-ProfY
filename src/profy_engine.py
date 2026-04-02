"""
ProfY — Socratic DAG Elicitation Engine
========================================
Chapter 12: LLMs as DAG Elicitation Engines

ProfY is the analyst's copilot. It coaches a human through a structured
causal interview, suggests questions to surface variables, edges, mediators,
and confounders, and incrementally builds a proposed DAG in the background.

Two modes:
  - Live mode:  Calls the Anthropic API (requires ANTHROPIC_API_KEY)
  - Replay mode: Reads from a saved transcript JSON file

The phase loop is identical in both modes. Only the response source changes.

Usage:
    # Live mode
    engine = ProfYEngine(mode="live")
    result = engine.run(domain="supply chain disruption",
                        target="delivery delays")

    # Replay mode
    engine = ProfYEngine(mode="replay",
                         transcript_path="transcripts/supply_chain_socratic.json")
    result = engine.run(domain="supply chain disruption",
                        target="delivery delays")
"""

import json
import os
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class ProposedVariable:
    """A variable surfaced during elicitation."""
    name: str
    description: str
    phase_discovered: str
    source: str
    status: str = "confirmed"


@dataclass
class ProposedEdge:
    """A causal edge proposed during elicitation."""
    cause: str
    effect: str
    mechanism: str
    phase_discovered: str
    source: str
    status: str = "proposed"
    rejection_reason: str = ""


@dataclass
class PhaseRecord:
    """Log entry for one phase of the elicitation."""
    phase_name: str
    profy_prompt: str
    ally_response: str
    variables_surfaced: list = field(default_factory=list)
    edges_surfaced: list = field(default_factory=list)
    timestamp: str = ""


@dataclass
class ElicitationResult:
    """Complete output of one elicitation session."""
    domain: str
    target_outcome: str
    mode: str
    variables: list = field(default_factory=list)
    edges: list = field(default_factory=list)
    phase_log: list = field(default_factory=list)
    started_at: str = ""
    completed_at: str = ""


# ---------------------------------------------------------------------------
# System prompts for each phase
# ---------------------------------------------------------------------------

SYSTEM_PROMPT_BASE = """You are ProfY, a causal graph elicitation copilot. Your job is to 
coach an analyst through a structured interview that builds a causal DAG 
for a specific domain.

Rules you follow:
- You are a FACILITATOR, not a source of causal knowledge. The analyst 
  and their domain expert are the authorities on what causes what.
- When you suggest a variable or edge, frame it as a question, not a fact.
- Push for mechanisms: "Why does X cause Y? Through what intermediate step?"
- Flag when an edge might be correlation rather than causation.
- Keep your responses focused and structured. No filler.
- Output structured JSON when asked for summaries.

Domain: {domain}
Target outcome: {target}
"""

PHASE_PROMPTS = {

    "variable_discovery": """PHASE: Variable Discovery

Your task: Help the analyst identify the key causal variables in the 
{domain} domain that could influence {target}.

Ask the analyst to think about:
1. What are the major factors that directly affect {target}?
2. What external shocks or conditions set off disruptions?
3. What intermediate factors sit between those shocks and the outcome?
4. Are there any factors that influence multiple variables at once?

Start with an open-ended question. After the analyst responds, probe 
for anything they might have missed. Suggest 1-2 variables they may 
not have considered, framed as questions ("Have you thought about 
whether X plays a role here?").

Respond with your coaching prompt for the analyst.""",

    "edge_probing": """PHASE: Edge Probing

Current variables discovered: {variables}
Target outcome: {target}

Your task: For each plausible variable pair, help the analyst determine 
whether a direct causal relationship exists, and in which direction.

Work through the variables systematically:
1. Start with variables most likely to directly affect {target}
2. For each pair, ask: "Does [A] directly cause [B], or is this 
   relationship mediated through something else?"
3. Ask about direction: "If we intervened on [A], would [B] change? 
   What about the reverse?"
4. Flag any pair where the direction is ambiguous

Do NOT propose edges yourself. Ask the analyst to reason through each one.
If the analyst proposes an edge that seems like a shortcut (skipping a 
mediator), ask "Is this direct, or does it go through something?"

Respond with your coaching prompt for the analyst.""",

    "mechanism_questioning": """PHASE: Mechanism Questioning

Current proposed edges: {edges}
Target outcome: {target}

Your task: For each proposed edge, push the analyst to articulate the 
causal mechanism. This is the most important phase, it catches:
- Shortcut edges that should be mediated
- Spurious edges based on correlation
- Reversed causation

For each edge, ask:
1. "WHY does [cause] affect [effect]? What is the mechanism?"
2. "Could this relationship be explained by a common cause instead?"
3. "If we could experimentally control [cause], would [effect] change?"
4. "Is this direct, or does the effect pass through an intermediate variable?"

If the analyst cannot articulate a clear mechanism, flag the edge as 
uncertain. One follow-up challenge per edge. If the analyst confirms 
after the challenge, accept it and log the reasoning.

Respond with your coaching prompt for the analyst.""",

    "confounder_probing": """PHASE: Confounder Probing

Current variables: {variables}
Current edges: {edges}
Target outcome: {target}

Your task: Help the analyst identify common causes (confounders) that 
might create spurious associations between variables.

For each pair of variables that are NOT currently connected by an edge:
1. "Is there a variable that affects BOTH [X] and [Y]?"
2. "Could the apparent relationship between [X] and [Y] be explained 
   by something upstream affecting both?"

Also check existing edges:
3. "For the edge [A] -> [B], is there a common cause we haven't 
   accounted for that might make this relationship appear stronger 
   or weaker than it really is?"

This phase often surfaces variables that were missed in Phase 1. 
If a new variable emerges, add it to the list.

Respond with your coaching prompt for the analyst.""",

    "checkpoint": """PHASE: Checkpoint Snapshot

Current variables: {variables}
Current edges: {edges}
Target outcome: {target}

Your task: Produce a plain-language summary of the current graph state 
that the analyst can show to the domain expert for validation.

Format the summary as:
1. A list of all variables with one-line descriptions
2. A list of all proposed causal relationships in plain English 
   (e.g., "Port congestion causes delivery delays because ships 
   waiting to unload push back the entire downstream timeline")
3. Any edges flagged as uncertain, with the reason
4. Any areas where you think the graph might be incomplete

Use zero jargon. The domain expert (Nora) is an ops manager with 
18 years of experience, not a statistician. She should be able to 
read this summary and say "yes, that's right" or "no, you're missing X."

Respond with the checkpoint summary."""
}


# ---------------------------------------------------------------------------
# LLM interface (live mode)
# ---------------------------------------------------------------------------

class LiveLLM:
    """Handles API calls to Claude for live elicitation."""

    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        try:
            from anthropic import Anthropic
        except ImportError:
            raise ImportError(
                "The anthropic package is required for live mode. "
                "Install with: pip install anthropic"
            )

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable not set. "
                "Set it with: export ANTHROPIC_API_KEY='your-key-here'"
            )

        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.conversation_history = []

    def send(self, system_prompt: str, user_message: str) -> str:
        """Send a message and get ProfY's response."""
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            system=system_prompt,
            messages=self.conversation_history
        )

        assistant_message = response.content[0].text
        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_message
        })

        return assistant_message


# ---------------------------------------------------------------------------
# Replay interface (saved transcript mode)
# ---------------------------------------------------------------------------

class ReplayLLM:
    """Reads responses from a saved transcript file."""

    def __init__(self, transcript_path: str):
        if not os.path.exists(transcript_path):
            raise FileNotFoundError(
                f"Transcript not found: {transcript_path}\n"
                f"Run in live mode first to generate a transcript, "
                f"or check the file path."
            )

        with open(transcript_path, "r") as f:
            self.transcript = json.load(f)

        self.phase_index = 0

    def get_phase_data(self, phase_name: str) -> dict:
        """Get the saved data for a specific phase."""
        for phase in self.transcript["phases"]:
            if phase["phase_name"] == phase_name:
                return phase
        raise ValueError(f"Phase '{phase_name}' not found in transcript")

    def get_profy_prompt(self, phase_name: str) -> str:
        """Get ProfY's saved coaching prompt for this phase."""
        phase = self.get_phase_data(phase_name)
        return phase["profy_prompt"]

    def get_ally_response(self, phase_name: str) -> str:
        """Get the saved analyst response for this phase."""
        phase = self.get_phase_data(phase_name)
        return phase["ally_response"]


# ---------------------------------------------------------------------------
# The engine
# ---------------------------------------------------------------------------

class ProfYEngine:
    """
    Main elicitation engine. Runs the phase loop in either live or replay mode.
    
    Parameters
    ----------
    mode : str
        "live" for API calls, "replay" for saved transcript
    transcript_path : str, optional
        Path to saved transcript JSON (required for replay mode)
    model : str
        Claude model to use in live mode
    """

    PHASES = [
        "variable_discovery",
        "edge_probing",
        "mechanism_questioning",
        "confounder_probing",
        "checkpoint",
    ]

    def __init__(
        self,
        mode: str = "replay",
        transcript_path: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514"
    ):
        if mode not in ("live", "replay"):
            raise ValueError(f"Mode must be 'live' or 'replay', got '{mode}'")

        self.mode = mode

        if mode == "live":
            self.llm = LiveLLM(model=model)
        else:
            if not transcript_path:
                raise ValueError("transcript_path required for replay mode")
            self.replay = ReplayLLM(transcript_path)

        # State accumulated across phases
        self.variables: list[ProposedVariable] = []
        self.edges: list[ProposedEdge] = []
        self.phase_log: list[PhaseRecord] = []

    def run(self, domain: str, target: str) -> ElicitationResult:
        """
        Run the full elicitation loop.
        
        In live mode: ProfY generates prompts, waits for analyst input,
        processes responses, and builds the graph incrementally.
        
        In replay mode: reads both sides of the conversation from the
        saved transcript and reconstructs the same state.
        """
        result = ElicitationResult(
            domain=domain,
            target_outcome=target,
            mode=self.mode,
            started_at=datetime.now().isoformat()
        )

        system_prompt = SYSTEM_PROMPT_BASE.format(
            domain=domain,
            target=target
        )

        for phase_name in self.PHASES:
            print(f"\n{'='*60}")
            print(f"PHASE: {phase_name.replace('_', ' ').title()}")
            print(f"{'='*60}\n")

            record = self._run_phase(
                phase_name=phase_name,
                domain=domain,
                target=target,
                system_prompt=system_prompt
            )

            self.phase_log.append(record)

            # Update accumulated state from this phase
            for v in record.variables_surfaced:
                if v not in [x.name for x in self.variables]:
                    self.variables.append(ProposedVariable(
                        name=v,
                        description="",
                        phase_discovered=phase_name,
                        source="expert"
                    ))

            for e in record.edges_surfaced:
                self.edges.append(ProposedEdge(
                    cause=e[0],
                    effect=e[1],
                    mechanism=e[2] if len(e) > 2 else "",
                    phase_discovered=phase_name,
                    source="expert"
                ))

        result.variables = [asdict(v) for v in self.variables]
        result.edges = [asdict(e) for e in self.edges]
        result.phase_log = [asdict(p) for p in self.phase_log]
        result.completed_at = datetime.now().isoformat()

        return result

    def _run_phase(
        self,
        phase_name: str,
        domain: str,
        target: str,
        system_prompt: str
    ) -> PhaseRecord:
        """Run a single phase of the elicitation."""

        # Build the phase-specific prompt with current state
        var_names = [v.name for v in self.variables]
        edge_strs = [f"{e.cause} -> {e.effect}" for e in self.edges]

        phase_prompt = PHASE_PROMPTS[phase_name].format(
            domain=domain,
            target=target,
            variables=var_names if var_names else "[none yet]",
            edges=edge_strs if edge_strs else "[none yet]"
        )

        if self.mode == "live":
            profy_response = self.llm.send(system_prompt, phase_prompt)
            print(f"ProfY:\n{profy_response}\n")
            print("-" * 40)
            ally_input = input("Ally (your response): ")

            # Send Ally's response back to ProfY for processing
            processing_prompt = (
                f"The analyst responded:\n\n{ally_input}\n\n"
                f"Extract from this response:\n"
                f"1. Any NEW variables mentioned (as a JSON list of strings)\n"
                f"2. Any causal edges stated or implied "
                f"(as a JSON list of [cause, effect, mechanism] triples)\n\n"
                f"Respond with ONLY a JSON object with keys "
                f"'variables' and 'edges'. No other text."
            )

            extraction = self.llm.send(system_prompt, processing_prompt)
            variables_found, edges_found = self._parse_extraction(extraction)

        else:
            profy_response = self.replay.get_profy_prompt(phase_name)
            ally_input = self.replay.get_ally_response(phase_name)

            print(f"ProfY:\n{profy_response}\n")
            print(f"Ally:\n{ally_input}\n")

            # In replay mode, the transcript stores pre-extracted data
            phase_data = self.replay.get_phase_data(phase_name)
            variables_found = phase_data.get("variables_extracted", [])
            edges_found = phase_data.get("edges_extracted", [])

        record = PhaseRecord(
            phase_name=phase_name,
            profy_prompt=profy_response,
            ally_response=ally_input,
            variables_surfaced=variables_found,
            edges_surfaced=edges_found,
            timestamp=datetime.now().isoformat()
        )

        # Print phase summary
        if variables_found:
            print(f"\n  Variables surfaced: {variables_found}")
        if edges_found:
            print(f"  Edges surfaced: {edges_found}")

        return record

    def _parse_extraction(self, raw: str) -> tuple[list, list]:
        """Parse the LLM's JSON extraction of variables and edges."""
        try:
            # Strip markdown code fences if present
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1]
                cleaned = cleaned.rsplit("```", 1)[0]

            data = json.loads(cleaned)
            variables = data.get("variables", [])
            edges = data.get("edges", [])
            return variables, edges

        except (json.JSONDecodeError, KeyError, IndexError) as e:
            print(f"  [Warning] Could not parse LLM extraction: {e}")
            print(f"  Raw output: {raw[:200]}")
            return [], []

    def save_transcript(self, result: ElicitationResult, path: str) -> None:
        """
        Save the elicitation result as a transcript JSON file.
        
        This saved file can be loaded in replay mode later, so the
        session is fully reproducible without an API key.
        """
        # Reshape into the format ReplayLLM expects
        transcript = {
            "domain": result.domain,
            "target_outcome": result.target_outcome,
            "mode": result.mode,
            "started_at": result.started_at,
            "completed_at": result.completed_at,
            "phases": []
        }

        for phase in result.phase_log:
            transcript["phases"].append({
                "phase_name": phase["phase_name"],
                "profy_prompt": phase["profy_prompt"],
                "ally_response": phase["ally_response"],
                "variables_extracted": phase["variables_surfaced"],
                "edges_extracted": phase["edges_surfaced"],
                "timestamp": phase["timestamp"]
            })

        transcript["final_variables"] = result.variables
        transcript["final_edges"] = result.edges

        with open(path, "w") as f:
            json.dump(transcript, f, indent=2)

        print(f"Transcript saved to: {path}")


# ---------------------------------------------------------------------------
# Convenience function for notebook usage
# ---------------------------------------------------------------------------

def run_elicitation(
    domain: str = "supply chain disruption",
    target: str = "delivery delays",
    mode: str = "replay",
    transcript_path: str = "transcripts/supply_chain_socratic.json",
    save_path: Optional[str] = None
) -> ElicitationResult:
    """
    One-call entry point for running ProfY in a notebook.
    
    Parameters
    ----------
    domain : str
        The domain to elicit causal structure for
    target : str
        The target outcome variable
    mode : str
        "live" for API calls, "replay" for saved transcript
    transcript_path : str
        Path to saved transcript (used in replay mode)
    save_path : str, optional
        If provided, save the session transcript to this path
        (useful in live mode to capture the session for later replay)
    
    Returns
    -------
    ElicitationResult
        Complete session output with variables, edges, and phase log
    """
    engine = ProfYEngine(
        mode=mode,
        transcript_path=transcript_path if mode == "replay" else None
    )

    result = engine.run(domain=domain, target=target)

    if save_path:
        engine.save_transcript(result, save_path)

    return result


# ---------------------------------------------------------------------------
# Main (for testing)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "live":
        print("Starting ProfY in LIVE mode...")
        print("Make sure ANTHROPIC_API_KEY is set.\n")
        result = run_elicitation(
            mode="live",
            save_path="transcripts/supply_chain_socratic.json"
        )
    else:
        print("Starting ProfY in REPLAY mode...")
        print("Reading from saved transcript.\n")
        result = run_elicitation(mode="replay")

    print(f"\n{'='*60}")
    print("ELICITATION COMPLETE")
    print(f"{'='*60}")
    print(f"Variables discovered: {len(result.variables)}")
    print(f"Edges proposed: {len(result.edges)}")
    print(f"Phases completed: {len(result.phase_log)}")