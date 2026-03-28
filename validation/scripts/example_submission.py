"""
Example Submission Template
============================

This template shows how to submit a proposed unified equation
for validation. Contributors should:

1. Define their equation (growth function + division condition)
2. Specify parameter sets for each limiting regime
3. Provide cross-species fitting results
4. Describe molecular mechanism interpretation
5. Show disease connection results

Run with:
    python example_submission.py
"""

import numpy as np
from validate_equation import (
    ProposedEquation,
    CellCycleData,
    run_full_validation,
)


# ============================================================
# Step 1: Define your proposed equation
# ============================================================

def my_growth_function(V: float, mu: float, params: np.ndarray) -> float:
    """
    dV/dt = F(V, mu, params)

    Example placeholder: exponential growth with nonlinear feedback.
    Replace this with your actual equation.

    params[0] = alpha (control strength, 0=timer, 1=adder-like, >>1=sizer)
    params[1] = V_target (target size)
    params[2] = ... (additional parameters as needed)
    """
    alpha = params[0]
    V_target = params[1]

    # Placeholder: simple exponential growth
    # Replace with your actual unified equation
    dVdt = mu * V
    return dVdt


def my_division_condition(V: float, mu: float, params: np.ndarray) -> bool:
    """
    Returns True when the cell should divide.

    This encodes the core of the size control mechanism.
    Replace with your actual division rule derived from F(V).

    Example placeholder: divide when V exceeds a size-dependent threshold.
    """
    alpha = params[0]
    V_target = params[1]

    # Placeholder: simple threshold
    # Replace with your actual division condition
    return V >= V_target


# ============================================================
# Step 2: Specify parameter sets for limiting regimes
# ============================================================

# These parameter values should cause your equation to behave as:
# - Pure sizer (V_div ~ constant, independent of V_birth)
# - Pure adder (Delta_V ~ constant, independent of V_birth)
# - Pure timer (T ~ constant, independent of V_birth)

params_sizer = np.array([10.0, 2.0])   # Strong control -> sizer
params_adder = np.array([1.0, 2.0])    # Moderate control -> adder
params_timer = np.array([0.01, 2.0])   # Weak control -> timer


# ============================================================
# Step 3: Provide cross-species fitting results
# ============================================================

# After fitting your equation to real data, provide R^2 and
# best-fit parameters for each species.

fit_results = {
    "E. coli": {
        "r2": 0.0,  # Fill with actual R^2
        "params": None,
        "notes": "Adder-like behavior expected"
    },
    "B. subtilis": {
        "r2": 0.0,
        "params": None,
        "notes": "Adder-like behavior expected"
    },
    "S. pombe": {
        "r2": 0.0,
        "params": None,
        "notes": "Sizer-like behavior expected"
    },
    "mammalian": {
        "r2": 0.0,
        "params": None,
        "notes": "Mixed behavior expected"
    },
}


# ============================================================
# Step 4: Describe mechanism interpretation
# ============================================================

mechanism_mapping = {
    "supported_mechanisms": [
        # List which molecular mechanisms your equation supports
        # e.g., "concentration_dilution", "surface_volume_ratio"
    ],
    "excluded_mechanisms": [
        # List which mechanisms are excluded by your equation's form
    ],
    "explanation": (
        "Describe how the functional form of F(V) maps to specific "
        "molecular sensors and signaling pathways."
    ),
}


# ============================================================
# Step 5: Disease connection
# ============================================================

perturbation_results = [
    # Each entry: what parameter was perturbed, what phenotype resulted
    # {
    #     "parameter": "alpha",
    #     "perturbation": "decrease by 50%",
    #     "predicted_phenotype": "increased size variance",
    #     "matches_cancer_phenotype": True/False,
    #     "known_mutation": "Rb loss",
    # },
]


# ============================================================
# Step 6: Run validation
# ============================================================

if __name__ == "__main__":
    equation = ProposedEquation(
        growth_function=my_growth_function,
        division_condition=my_division_condition,
        param_names=["alpha", "V_target"],
        description="Placeholder equation - replace with your unified model",
    )

    report = run_full_validation(
        eq=equation,
        params_sizer=params_sizer,
        params_adder=params_adder,
        params_timer=params_timer,
        datasets=None,          # Provide real data when available
        fit_results=fit_results,
        prediction_tests=None,  # Provide prediction test results
        mechanism_mapping=mechanism_mapping,
        perturbation_results=perturbation_results,
    )

    print(report.summary())
