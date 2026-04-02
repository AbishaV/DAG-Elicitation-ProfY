"""
Estimator — Backdoor Adjustment Sets and Doubly Robust Estimation
==================================================================
Chapter 12: LLMs as DAG Elicitation Engines

This module does three things:
  1. Computes backdoor adjustment sets from a validated DAG (Component 9)
  2. Generates simulated supply chain data consistent with the DAG (Component 11)
  3. Runs a Doubly Robust / AIPW estimator on the simulated data (Component 10)

The point: once you have a validated DAG, you can identify which variables
to control for and estimate causal effects. The DAG is not decoration.
It drives the entire estimation strategy.

Usage:
    from estimator import (
        find_backdoor_sets,
        generate_supply_chain_data,
        doubly_robust_estimate,
        run_full_pipeline
    )

    # Full pipeline
    results = run_full_pipeline(
        dag_edges=validated_edges,
        treatment="port_congestion",
        outcome="delivery_delays"
    )
"""

import numpy as np
import pandas as pd
import networkx as nx
from typing import Optional


# ---------------------------------------------------------------------------
# Component 9: Backdoor Adjustment Sets
# ---------------------------------------------------------------------------

def find_backdoor_sets(
    edges: list[tuple],
    treatment: str,
    outcome: str
) -> dict:
    """
    Find the backdoor adjustment set for a treatment-outcome pair.

    Uses pgmpy to compute the minimal adjustment set via the
    backdoor criterion. Falls back to a networkx-based implementation
    if pgmpy is unavailable.

    Parameters
    ----------
    edges : list[tuple]
        Edge list defining the DAG, each tuple is (cause, effect)
    treatment : str
        The treatment/intervention variable
    outcome : str
        The outcome variable

    Returns
    -------
    dict with keys:
        adjustment_set: list of variable names to condition on
        all_backdoor_paths: list of paths from treatment to outcome
            through non-causal routes
        method: which method was used ("pgmpy" or "networkx")
    """
    result = {
        "treatment": treatment,
        "outcome": outcome,
        "adjustment_set": [],
        "method": "",
        "details": ""
    }

    # Try pgmpy first
    try:
        from pgmpy.models import BayesianNetwork
        from pgmpy.inference.CausalInference import CausalInference

        model = BayesianNetwork(edges)
        inference = CausalInference(model)

        adj_set = inference.get_minimal_adjustment_set(treatment, outcome)
        result["adjustment_set"] = sorted(adj_set)
        result["method"] = "pgmpy"
        result["details"] = "Minimal adjustment set via pgmpy CausalInference"
        return result

    except ImportError:
        pass
    except Exception as e:
        result["details"] = f"pgmpy failed: {e}, falling back to networkx"

    # Fallback: networkx-based backdoor identification
    G = nx.DiGraph(edges)

    # Find all non-descendants of treatment that are ancestors of
    # treatment or outcome (simplified backdoor criterion)
    descendants_of_treatment = nx.descendants(G, treatment)
    ancestors_of_treatment = nx.ancestors(G, treatment)
    ancestors_of_outcome = nx.ancestors(G, outcome)

    # Candidate confounders: ancestors of both treatment and outcome
    # that are not descendants of treatment
    candidates = (ancestors_of_treatment & ancestors_of_outcome) - descendants_of_treatment
    # Also include direct parents of treatment that aren't on the causal path
    parents_of_treatment = set(G.predecessors(treatment))
    candidates = candidates | (parents_of_treatment - descendants_of_treatment)

    result["adjustment_set"] = sorted(candidates)
    result["method"] = "networkx"
    result["details"] = "Approximate adjustment set via ancestor analysis"

    return result


def print_backdoor_result(result: dict) -> None:
    """Print the backdoor adjustment set result."""
    print("=" * 60)
    print("BACKDOOR ADJUSTMENT SET")
    print("=" * 60)
    print(f"Treatment: {result['treatment']}")
    print(f"Outcome:   {result['outcome']}")
    print(f"Method:    {result['method']}")
    print(f"Details:   {result['details']}")
    print(f"\nAdjustment set ({len(result['adjustment_set'])} variables):")
    for v in result["adjustment_set"]:
        print(f"  {v}")
    print()


# ---------------------------------------------------------------------------
# Component 11: Simulated Supply Chain Data
# ---------------------------------------------------------------------------

def generate_supply_chain_data(
    n_samples: int = 2000,
    seed: int = 42
) -> pd.DataFrame:
    """
    Generate simulated supply chain data consistent with the ground truth DAG.

    Each variable is generated as a linear function of its parents plus noise,
    following the topological order of the DAG. This ensures the data respects
    the causal structure.

    The coefficients are chosen to produce realistic-looking relationships
    (positive where causes increase effects, negative where they decrease).

    Parameters
    ----------
    n_samples : int
        Number of observations to generate
    seed : int
        Random seed for reproducibility

    Returns
    -------
    pd.DataFrame
        Simulated dataset with one column per DAG variable
    """
    rng = np.random.default_rng(seed)

    # Exogenous variables (root nodes, no parents)
    geopolitical_risk = rng.normal(0, 1, n_samples)
    labor_shortages = rng.normal(0, 1, n_samples)
    demand_volatility = rng.normal(0, 1, n_samples)

    # Layer 1: direct children of exogenous
    fuel_prices = (
        0.6 * geopolitical_risk
        + rng.normal(0, 0.5, n_samples)
    )

    supplier_reliability = (
        -0.5 * geopolitical_risk  # negative: instability reduces reliability
        + rng.normal(0, 0.5, n_samples)
    )

    port_congestion = (
        0.5 * geopolitical_risk
        + 0.4 * labor_shortages
        + rng.normal(0, 0.5, n_samples)
    )

    # Layer 2
    raw_material_availability = (
        -0.4 * geopolitical_risk  # sanctions reduce availability
        + 0.5 * supplier_reliability  # reliable suppliers improve availability
        + rng.normal(0, 0.5, n_samples)
    )

    order_lead_time = (
        -0.4 * supplier_reliability  # unreliable suppliers extend lead times
        + 0.3 * demand_volatility  # demand surges extend lead times
        + rng.normal(0, 0.5, n_samples)
    )

    production_capacity = (
        -0.3 * fuel_prices  # high energy costs reduce capacity
        - 0.4 * labor_shortages  # understaffing reduces output
        + 0.5 * raw_material_availability  # materials enable production
        + rng.normal(0, 0.5, n_samples)
    )

    # Layer 3
    inventory_levels = (
        0.6 * production_capacity  # more production fills inventory
        - 0.4 * demand_volatility  # demand surges deplete stock
        + rng.normal(0, 0.5, n_samples)
    )

    # Layer 4: target outcomes
    shipping_cost = (
        0.5 * fuel_prices
        + 0.4 * port_congestion
        - 0.3 * inventory_levels  # low inventory triggers expensive shipping
        + rng.normal(0, 0.5, n_samples)
    )

    delivery_delays = (
        0.5 * port_congestion
        + 0.4 * order_lead_time
        - 0.5 * inventory_levels  # low inventory causes delays
        + rng.normal(0, 0.5, n_samples)
    )

    df = pd.DataFrame({
        "geopolitical_risk": geopolitical_risk,
        "fuel_prices": fuel_prices,
        "port_congestion": port_congestion,
        "labor_shortages": labor_shortages,
        "supplier_reliability": supplier_reliability,
        "raw_material_availability": raw_material_availability,
        "production_capacity": production_capacity,
        "demand_volatility": demand_volatility,
        "shipping_cost": shipping_cost,
        "order_lead_time": order_lead_time,
        "inventory_levels": inventory_levels,
        "delivery_delays": delivery_delays,
    })

    return df


# ---------------------------------------------------------------------------
# Component 10: Doubly Robust / AIPW Estimator
# ---------------------------------------------------------------------------

def doubly_robust_estimate(
    data: pd.DataFrame,
    treatment: str,
    outcome: str,
    adjustment_set: list[str],
    n_bootstrap: int = 200,
    seed: int = 42
) -> dict:
    """
    Estimate the Average Treatment Effect using a Doubly Robust (AIPW) estimator.

    Since our simulated data has continuous treatment, we binarize it at the
    median to create treated/control groups. This is a simplification for
    pedagogical purposes.

    The doubly robust estimator combines:
    1. An outcome model (regression of Y on covariates)
    2. A propensity model (probability of treatment given covariates)

    It is "doubly robust" because the estimate is consistent if EITHER
    the outcome model OR the propensity model is correctly specified.

    Parameters
    ----------
    data : pd.DataFrame
        The dataset
    treatment : str
        Treatment variable name
    outcome : str
        Outcome variable name
    adjustment_set : list[str]
        Variables to condition on (from backdoor criterion)
    n_bootstrap : int
        Number of bootstrap resamples for confidence intervals
    seed : int
        Random seed

    Returns
    -------
    dict with keys: ate, ci_lower, ci_upper, naive_difference,
        outcome_model_coef, propensity_accuracy
    """
    from sklearn.linear_model import LogisticRegression, LinearRegression

    rng = np.random.default_rng(seed)

    # Binarize treatment at median
    treatment_binary = (data[treatment] > data[treatment].median()).astype(int)

    Y = data[outcome].values
    T = treatment_binary.values

    # Covariates (adjustment set)
    if len(adjustment_set) > 0:
        X = data[adjustment_set].values
    else:
        X = np.ones((len(data), 1))

    def compute_dr_estimate(Y, T, X):
        """Single DR estimate on one sample."""
        n = len(Y)

        # Propensity model: P(T=1 | X)
        prop_model = LogisticRegression(max_iter=1000, random_state=42)
        prop_model.fit(X, T)
        e_hat = prop_model.predict_proba(X)[:, 1]
        e_hat = np.clip(e_hat, 0.01, 0.99)  # avoid division by zero

        # Outcome models: E[Y | X, T=t] for t in {0, 1}
        treated_idx = T == 1
        control_idx = T == 0

        mu1_model = LinearRegression()
        mu0_model = LinearRegression()

        if treated_idx.sum() > 0 and control_idx.sum() > 0:
            mu1_model.fit(X[treated_idx], Y[treated_idx])
            mu0_model.fit(X[control_idx], Y[control_idx])
        else:
            return np.nan

        mu1_hat = mu1_model.predict(X)
        mu0_hat = mu0_model.predict(X)

        # Doubly robust formula
        dr1 = mu1_hat + T * (Y - mu1_hat) / e_hat
        dr0 = mu0_hat + (1 - T) * (Y - mu0_hat) / (1 - e_hat)

        ate = np.mean(dr1 - dr0)
        return ate

    # Point estimate
    ate = compute_dr_estimate(Y, T, X)

    # Bootstrap confidence interval
    bootstrap_ates = []
    for _ in range(n_bootstrap):
        idx = rng.choice(len(Y), size=len(Y), replace=True)
        boot_ate = compute_dr_estimate(Y[idx], T[idx], X[idx])
        if not np.isnan(boot_ate):
            bootstrap_ates.append(boot_ate)

    bootstrap_ates = np.array(bootstrap_ates)
    ci_lower = np.percentile(bootstrap_ates, 2.5)
    ci_upper = np.percentile(bootstrap_ates, 97.5)

    # Naive difference (no adjustment) for comparison
    naive = Y[T == 1].mean() - Y[T == 0].mean()

    # Propensity model accuracy
    prop_model = LogisticRegression(max_iter=1000, random_state=42)
    prop_model.fit(X, T)
    prop_accuracy = prop_model.score(X, T)

    return {
        "treatment": treatment,
        "outcome": outcome,
        "adjustment_set": adjustment_set,
        "ate": ate,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "naive_difference": naive,
        "propensity_accuracy": prop_accuracy,
        "n_bootstrap": n_bootstrap,
        "n_treated": int(T.sum()),
        "n_control": int((1 - T).sum()),
    }


def print_estimate(result: dict) -> None:
    """Print the causal estimate."""
    print("=" * 60)
    print("CAUSAL EFFECT ESTIMATE (Doubly Robust)")
    print("=" * 60)
    print(f"Treatment:      {result['treatment']} (binarized at median)")
    print(f"Outcome:        {result['outcome']}")
    print(f"Adjustment set: {result['adjustment_set']}")
    print(f"N treated:      {result['n_treated']}")
    print(f"N control:      {result['n_control']}")
    print()
    print(f"Naive difference (no adjustment):  {result['naive_difference']:.4f}")
    print(f"Doubly Robust ATE:                 {result['ate']:.4f}")
    print(f"95% CI: [{result['ci_lower']:.4f}, {result['ci_upper']:.4f}]")
    print(f"Propensity model accuracy:         {result['propensity_accuracy']:.3f}")
    print()


# ---------------------------------------------------------------------------
# Full pipeline
# ---------------------------------------------------------------------------

def run_full_pipeline(
    dag_edges: list[tuple],
    treatment: str = "port_congestion",
    outcome: str = "delivery_delays",
    n_samples: int = 2000,
    seed: int = 42,
    verbose: bool = True
) -> dict:
    """
    Run the complete estimation pipeline:
    1. Find backdoor adjustment set from the DAG
    2. Generate simulated data
    3. Estimate causal effect using doubly robust estimator

    Parameters
    ----------
    dag_edges : list[tuple]
        Validated edge list from the Human Decision Node
    treatment : str
        Treatment variable
    outcome : str
        Outcome variable
    n_samples : int
        Simulated data size
    seed : int
        Random seed
    verbose : bool
        Print results as we go

    Returns
    -------
    dict with keys: backdoor_result, data, estimate
    """
    # Step 1: Backdoor adjustment set
    if verbose:
        print("STEP 1: Finding backdoor adjustment set")
        print("-" * 40)

    backdoor = find_backdoor_sets(dag_edges, treatment, outcome)

    if verbose:
        print_backdoor_result(backdoor)

    # Step 2: Generate data
    if verbose:
        print("STEP 2: Generating simulated supply chain data")
        print("-" * 40)

    data = generate_supply_chain_data(n_samples=n_samples, seed=seed)

    if verbose:
        print(f"Generated {len(data)} observations, {len(data.columns)} variables")
        print(f"Columns: {list(data.columns)}")
        print()

    # Step 3: Estimate
    if verbose:
        print("STEP 3: Doubly robust estimation")
        print("-" * 40)

    estimate = doubly_robust_estimate(
        data=data,
        treatment=treatment,
        outcome=outcome,
        adjustment_set=backdoor["adjustment_set"],
        seed=seed
    )

    if verbose:
        print_estimate(estimate)

    return {
        "backdoor_result": backdoor,
        "data": data,
        "estimate": estimate,
    }


# ---------------------------------------------------------------------------
# Main (for testing)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    sys.path.insert(0, "src")

    from ground_truth_dag import EDGES

    # Test 1: Full pipeline with default treatment/outcome
    print("Test 1: Full pipeline (port_congestion -> delivery_delays)")
    print("=" * 60)
    print()

    result1 = run_full_pipeline(
        dag_edges=EDGES,
        treatment="port_congestion",
        outcome="delivery_delays"
    )

    # Test 2: Different treatment/outcome pair
    print("\nTest 2: Full pipeline (fuel_prices -> shipping_cost)")
    print("=" * 60)
    print()

    result2 = run_full_pipeline(
        dag_edges=EDGES,
        treatment="fuel_prices",
        outcome="shipping_cost"
    )

    # Test 3: Save simulated data
    print("\nTest 3: Save simulated data to CSV")
    print("-" * 40)

    result1["data"].to_csv("data/simulated_supply_chain.csv", index=False)
    print("Saved to data/simulated_supply_chain.csv")
    print(f"Shape: {result1['data'].shape}")
    print()