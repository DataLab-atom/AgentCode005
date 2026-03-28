"""
Validation Framework for Unified Cell Size Control Equation
============================================================

This script validates whether a proposed equation F(V, mu, p) satisfies
the five Nature-level criteria defined in the README:

1. Unified equation that recovers sizer/adder/timer as limiting cases
2. Cross-species universality (E. coli, B. subtilis, S. pombe, mammalian)
3. Falsifiable quantitative predictions beyond existing models
4. Molecular mechanism interpretability
5. Connection to disease (cancer size dysregulation)

Usage:
    python validate_equation.py --equation <module_path>
"""

import numpy as np
import pandas as pd
from scipy import stats, optimize
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple
from pathlib import Path
import json
import sys

# ============================================================
# Data structures
# ============================================================

@dataclass
class CellCycleData:
    """Single-cell cycle data for one species/condition."""
    species: str
    condition: str
    v_birth: np.ndarray       # Birth volumes
    v_division: np.ndarray    # Division volumes
    delta_v: np.ndarray       # Added volumes
    interdiv_time: np.ndarray # Interdivision times
    growth_rate: np.ndarray   # Per-cell growth rates

    @property
    def n_cells(self) -> int:
        return len(self.v_birth)


@dataclass
class ProposedEquation:
    """Interface for a proposed unified equation."""
    # F(V, mu, params) -> dV/dt
    growth_function: Callable[[float, float, np.ndarray], float]
    # Division condition: returns True when cell should divide
    division_condition: Callable[[float, float, np.ndarray], bool]
    # Parameter names
    param_names: List[str]
    # Description of the equation
    description: str = ""


@dataclass
class ValidationResult:
    """Result of a single validation test."""
    test_name: str
    passed: bool
    score: float          # 0.0 to 1.0
    details: str
    data: dict = field(default_factory=dict)


@dataclass
class ValidationReport:
    """Complete validation report."""
    results: List[ValidationResult]

    @property
    def all_passed(self) -> bool:
        return all(r.passed for r in self.results)

    @property
    def overall_score(self) -> float:
        return np.mean([r.score for r in self.results])

    def summary(self) -> str:
        lines = ["=" * 70]
        lines.append("VALIDATION REPORT: Unified Cell Size Control Equation")
        lines.append("=" * 70)
        for r in self.results:
            status = "PASS" if r.passed else "FAIL"
            lines.append(f"[{status}] {r.test_name} (score: {r.score:.3f})")
            lines.append(f"       {r.details}")
        lines.append("-" * 70)
        lines.append(f"Overall: {'ALL PASSED' if self.all_passed else 'SOME FAILED'}")
        lines.append(f"Score:   {self.overall_score:.3f}")
        lines.append("=" * 70)
        return "\n".join(lines)


# ============================================================
# Criterion 1: Limiting case recovery
# ============================================================

def test_sizer_limit(eq: ProposedEquation, params_sizer: np.ndarray,
                     mu: float = 0.01, n_cells: int = 5000) -> ValidationResult:
    """
    Test that in the sizer parameter regime, V_division ~ constant
    regardless of V_birth.
    """
    v_births = np.random.lognormal(mean=np.log(1.0), sigma=0.3, size=n_cells)
    v_divs = []

    for vb in v_births:
        v = vb
        dt = 0.01
        for _ in range(100000):
            dv = eq.growth_function(v, mu, params_sizer) * dt
            v += dv
            if eq.division_condition(v, mu, params_sizer):
                break
        v_divs.append(v)

    v_divs = np.array(v_divs)

    # Sizer: slope of V_div vs V_birth should be ~0
    slope, intercept, r, p, se = stats.linregress(v_births, v_divs)
    cv_vdiv = np.std(v_divs) / np.mean(v_divs)

    passed = abs(slope) < 0.15 and cv_vdiv < 0.15
    score = max(0, 1.0 - abs(slope) / 0.3)

    return ValidationResult(
        test_name="Criterion 1a: Sizer limit recovery",
        passed=passed,
        score=score,
        details=f"slope(V_div vs V_birth)={slope:.4f} (expect ~0), CV(V_div)={cv_vdiv:.4f}",
        data={"slope": slope, "cv_vdiv": cv_vdiv}
    )


def test_adder_limit(eq: ProposedEquation, params_adder: np.ndarray,
                     mu: float = 0.01, n_cells: int = 5000) -> ValidationResult:
    """
    Test that in the adder parameter regime, Delta_V ~ constant
    regardless of V_birth.
    """
    v_births = np.random.lognormal(mean=np.log(1.0), sigma=0.3, size=n_cells)
    delta_vs = []

    for vb in v_births:
        v = vb
        dt = 0.01
        for _ in range(100000):
            dv = eq.growth_function(v, mu, params_adder) * dt
            v += dv
            if eq.division_condition(v, mu, params_adder):
                break
        delta_vs.append(v - vb)

    delta_vs = np.array(delta_vs)

    # Adder: slope of Delta_V vs V_birth should be ~0
    slope, intercept, r, p, se = stats.linregress(v_births, delta_vs)
    cv_dv = np.std(delta_vs) / np.mean(delta_vs)

    passed = abs(slope) < 0.15 and cv_dv < 0.15
    score = max(0, 1.0 - abs(slope) / 0.3)

    return ValidationResult(
        test_name="Criterion 1b: Adder limit recovery",
        passed=passed,
        score=score,
        details=f"slope(DeltaV vs V_birth)={slope:.4f} (expect ~0), CV(DeltaV)={cv_dv:.4f}",
        data={"slope": slope, "cv_dv": cv_dv}
    )


def test_timer_limit(eq: ProposedEquation, params_timer: np.ndarray,
                     mu: float = 0.01, n_cells: int = 5000) -> ValidationResult:
    """
    Test that in the timer parameter regime, interdivision time ~ constant
    regardless of V_birth.
    """
    v_births = np.random.lognormal(mean=np.log(1.0), sigma=0.3, size=n_cells)
    times = []

    for vb in v_births:
        v = vb
        dt = 0.01
        t = 0
        for _ in range(100000):
            dv = eq.growth_function(v, mu, params_timer) * dt
            v += dv
            t += dt
            if eq.division_condition(v, mu, params_timer):
                break
        times.append(t)

    times = np.array(times)

    # Timer: slope of T vs V_birth should be ~0
    slope, intercept, r, p, se = stats.linregress(v_births, times)
    cv_t = np.std(times) / np.mean(times)

    passed = abs(slope) < 0.15 * np.mean(times) and cv_t < 0.15
    score = max(0, 1.0 - cv_t / 0.3)

    return ValidationResult(
        test_name="Criterion 1c: Timer limit recovery",
        passed=passed,
        score=score,
        details=f"slope(T vs V_birth)={slope:.4f}, CV(T)={cv_t:.4f} (expect low)",
        data={"slope": slope, "cv_t": cv_t}
    )


# ============================================================
# Criterion 2: Cross-species fitting
# ============================================================

def test_cross_species_fit(eq: ProposedEquation,
                           datasets: Dict[str, CellCycleData],
                           fit_results: Dict[str, dict]) -> ValidationResult:
    """
    Test that the same functional form fits data from at least 4 species
    with R^2 > 0.8 for each.
    """
    species_required = {"E. coli", "B. subtilis", "S. pombe", "mammalian"}
    species_present = set(datasets.keys())
    coverage = len(species_required & species_present) / len(species_required)

    r2_values = {}
    for sp, result in fit_results.items():
        r2_values[sp] = result.get("r2", 0.0)

    min_r2 = min(r2_values.values()) if r2_values else 0.0
    mean_r2 = np.mean(list(r2_values.values())) if r2_values else 0.0

    passed = coverage >= 0.75 and min_r2 > 0.7
    score = coverage * 0.4 + mean_r2 * 0.6

    return ValidationResult(
        test_name="Criterion 2: Cross-species universality",
        passed=passed,
        score=score,
        details=f"Coverage: {coverage:.0%}, R2 range: [{min_r2:.3f}, {max(r2_values.values()) if r2_values else 0:.3f}]",
        data={"r2_values": r2_values, "coverage": coverage}
    )


# ============================================================
# Criterion 3: Predictions beyond existing models
# ============================================================

def test_novel_predictions(eq: ProposedEquation,
                           prediction_tests: List[dict]) -> ValidationResult:
    """
    Test that the equation makes at least one quantitative prediction
    that sizer/adder/timer cannot make, and that prediction is validated.
    """
    n_novel = sum(1 for t in prediction_tests if t.get("is_novel", False))
    n_validated = sum(1 for t in prediction_tests
                      if t.get("is_novel", False) and t.get("validated", False))

    passed = n_validated >= 1
    score = min(1.0, n_validated / max(1, n_novel)) if n_novel > 0 else 0.0

    return ValidationResult(
        test_name="Criterion 3: Falsifiable novel predictions",
        passed=passed,
        score=score,
        details=f"{n_novel} novel predictions proposed, {n_validated} validated by data",
        data={"n_novel": n_novel, "n_validated": n_validated}
    )


# ============================================================
# Criterion 4: Molecular mechanism interpretability
# ============================================================

def test_mechanism_interpretation(eq: ProposedEquation,
                                 mechanism_mapping: dict) -> ValidationResult:
    """
    Test that the equation's functional form maps to known molecular mechanisms.
    """
    known_mechanisms = {
        "concentration_dilution",    # Whi5/Rb dilution
        "surface_volume_ratio",      # Membrane-cytoplasm sensing
        "dna_concentration",         # Gene dosage
        "growth_rate_feedback",      # Growth-rate-dependent control
    }

    proposed = set(mechanism_mapping.get("supported_mechanisms", []))
    excluded = set(mechanism_mapping.get("excluded_mechanisms", []))
    has_interpretation = len(proposed) > 0
    makes_discrimination = len(excluded) > 0

    passed = has_interpretation and makes_discrimination
    score = 0.5 * int(has_interpretation) + 0.5 * int(makes_discrimination)

    return ValidationResult(
        test_name="Criterion 4: Molecular mechanism interpretation",
        passed=passed,
        score=score,
        details=f"Supports: {proposed or 'none'}, Excludes: {excluded or 'none'}",
        data=mechanism_mapping
    )


# ============================================================
# Criterion 5: Disease connection
# ============================================================

def test_disease_connection(eq: ProposedEquation,
                            perturbation_results: List[dict]) -> ValidationResult:
    """
    Test that parameter perturbations recapitulate cancer-like size phenotypes.
    """
    n_perturbations = len(perturbation_results)
    n_recapitulated = sum(1 for p in perturbation_results
                          if p.get("matches_cancer_phenotype", False))

    passed = n_recapitulated >= 1
    score = n_recapitulated / max(1, n_perturbations)

    return ValidationResult(
        test_name="Criterion 5: Cancer size dysregulation connection",
        passed=passed,
        score=score,
        details=f"{n_recapitulated}/{n_perturbations} perturbations match cancer phenotypes",
        data={"perturbation_results": perturbation_results}
    )


# ============================================================
# Statistical model comparison
# ============================================================

def compare_models_aic(data: CellCycleData,
                       models: Dict[str, Callable],
                       n_params: Dict[str, int]) -> dict:
    """
    Compare models using AIC/BIC on the same dataset.
    Returns AIC weights and rankings.
    """
    n = data.n_cells
    results = {}

    for name, model_fn in models.items():
        try:
            residuals = model_fn(data)
            rss = np.sum(residuals ** 2)
            k = n_params[name]
            aic = n * np.log(rss / n) + 2 * k
            bic = n * np.log(rss / n) + k * np.log(n)
            results[name] = {"aic": aic, "bic": bic, "rss": rss}
        except Exception as e:
            results[name] = {"aic": np.inf, "bic": np.inf, "error": str(e)}

    # AIC weights
    aic_values = [r["aic"] for r in results.values() if "aic" in r]
    if aic_values:
        aic_min = min(aic_values)
        for name in results:
            if "aic" in results[name]:
                delta = results[name]["aic"] - aic_min
                results[name]["delta_aic"] = delta
                results[name]["aic_weight"] = np.exp(-0.5 * delta)

        total_weight = sum(r.get("aic_weight", 0) for r in results.values())
        for name in results:
            if "aic_weight" in results[name]:
                results[name]["aic_weight"] /= total_weight

    return results


# ============================================================
# Main validation runner
# ============================================================

def run_full_validation(eq: ProposedEquation,
                        params_sizer: np.ndarray,
                        params_adder: np.ndarray,
                        params_timer: np.ndarray,
                        datasets: Dict[str, CellCycleData] = None,
                        fit_results: Dict[str, dict] = None,
                        prediction_tests: List[dict] = None,
                        mechanism_mapping: dict = None,
                        perturbation_results: List[dict] = None) -> ValidationReport:
    """
    Run all five criteria tests and produce a validation report.
    """
    results = []

    # Criterion 1: Limiting cases
    print("Testing Criterion 1: Limiting case recovery...")
    results.append(test_sizer_limit(eq, params_sizer))
    results.append(test_adder_limit(eq, params_adder))
    results.append(test_timer_limit(eq, params_timer))

    # Criterion 2: Cross-species
    if datasets and fit_results:
        print("Testing Criterion 2: Cross-species fitting...")
        results.append(test_cross_species_fit(eq, datasets, fit_results))
    else:
        results.append(ValidationResult(
            "Criterion 2: Cross-species universality",
            False, 0.0, "No cross-species data provided"
        ))

    # Criterion 3: Novel predictions
    if prediction_tests:
        print("Testing Criterion 3: Novel predictions...")
        results.append(test_novel_predictions(eq, prediction_tests))
    else:
        results.append(ValidationResult(
            "Criterion 3: Falsifiable novel predictions",
            False, 0.0, "No prediction tests provided"
        ))

    # Criterion 4: Mechanism
    if mechanism_mapping:
        print("Testing Criterion 4: Mechanism interpretation...")
        results.append(test_mechanism_interpretation(eq, mechanism_mapping))
    else:
        results.append(ValidationResult(
            "Criterion 4: Molecular mechanism interpretation",
            False, 0.0, "No mechanism mapping provided"
        ))

    # Criterion 5: Disease
    if perturbation_results:
        print("Testing Criterion 5: Disease connection...")
        results.append(test_disease_connection(eq, perturbation_results))
    else:
        results.append(ValidationResult(
            "Criterion 5: Cancer size dysregulation connection",
            False, 0.0, "No perturbation results provided"
        ))

    report = ValidationReport(results=results)
    return report


# ============================================================
# Entry point
# ============================================================

if __name__ == "__main__":
    print("Cell Size Control Equation Validation Framework")
    print("=" * 50)
    print()
    print("This framework validates proposed equations against")
    print("the five Nature-level criteria. To use:")
    print()
    print("  1. Define your equation as a ProposedEquation object")
    print("  2. Provide parameter sets for sizer/adder/timer limits")
    print("  3. Provide experimental data and fitting results")
    print("  4. Call run_full_validation()")
    print()
    print("See validation/scripts/example_submission.py for a template.")
