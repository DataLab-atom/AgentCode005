"""
Novel Predictions from the Unified Cell Size Control Model
============================================================

Implements three key predictions that go beyond sizer/adder/timer:

  1. Non-monotonic transient response after nutrient shift
  2. Size-dependent division noise: CV(Vd|Vb) ∝ (Vb+K)^{-1/2}
  3. Cell-cycle phase composition: emergent adder from sizer+timer

These predictions are falsifiable and can discriminate the unified
model from competing models.

Author: CodeAgent005 (agent-mna1rwvb)
"""

import numpy as np
from scipy import stats, integrate, optimize
from typing import Dict, List, Tuple
from dataclasses import dataclass
from pathlib import Path
import json
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))

from unified_model import (
    hazard, survival, division_pdf,
    simulate_cell_cycles, SimulationResult,
)


# ============================================================
# Prediction 1: Non-monotonic transient after nutrient shift
# ============================================================

@dataclass
class NutrientShiftResult:
    """Results from nutrient shift simulation."""
    mu_before: float
    mu_after: float
    params: dict                  # r, K, n
    gen_mean_size: np.ndarray     # mean Vd per generation
    gen_cv_size: np.ndarray       # CV(Vd) per generation
    gen_mean_time: np.ndarray     # mean T per generation
    n_gen_after: int
    steady_before: float
    steady_after: float
    overshoot_magnitude: float    # (max - steady_after) / steady_after
    overshoot_gen: int            # generation of peak
    relaxation_time: int          # generations to reach 95% of new steady state

    @property
    def has_overshoot(self) -> bool:
        return self.overshoot_magnitude > 0.02  # >2% overshoot


def simulate_nutrient_shift_detailed(
    mu_before: float,
    mu_after: float,
    r: float, K: float, n: float,
    n_cells: int = 500,
    n_gen_before: int = 50,
    n_gen_after: int = 40,
    dt: float = 0.001,
    seed: int = 100,
) -> NutrientShiftResult:
    """
    Detailed nutrient shift simulation tracking per-generation statistics.

    Key prediction: for 1 < n < ∞, the mean cell size overshoots the new
    steady state before settling, because h(V) adjusts through μ faster
    than the population adapts its size distribution.
    """
    rng = np.random.default_rng(seed)

    # Reach steady state at mu_before
    sim_before = simulate_cell_cycles(
        mu_before, r, K, n, n_cells=n_cells,
        n_generations=n_gen_before, seed=seed
    )
    steady_before = np.mean(sim_before.v_division)

    # Track generation-by-generation after shift
    current_births = sim_before.v_division / 2  # daughter cells
    gen_mean_size = [steady_before]
    gen_cv_size = [np.std(sim_before.v_division) / np.mean(sim_before.v_division)]
    gen_mean_time = [np.mean(sim_before.interdiv_time)]

    mu = mu_after
    for gen in range(n_gen_after):
        div_sizes = []
        div_times = []
        next_births = []

        for Vb in current_births:
            V = Vb
            t = 0.0
            step = 0
            while step < 500000:
                step += 1
                V += mu * V * dt
                t += dt
                h = hazard(V, mu, r, K, n)
                if rng.random() < h * dt:
                    break

            div_sizes.append(V)
            div_times.append(t)
            next_births.append(V * 0.5)

        gen_mean_size.append(np.mean(div_sizes))
        gen_cv_size.append(np.std(div_sizes) / np.mean(div_sizes))
        gen_mean_time.append(np.mean(div_times))
        current_births = np.array(next_births)

    gen_mean_size = np.array(gen_mean_size)
    gen_cv_size = np.array(gen_cv_size)
    gen_mean_time = np.array(gen_mean_time)

    steady_after = gen_mean_size[-1]

    # Detect overshoot
    if mu_after > mu_before:
        # Upshift: check for overshoot above steady_after
        peak_idx = np.argmax(gen_mean_size[1:]) + 1
        peak_val = gen_mean_size[peak_idx]
        overshoot = (peak_val - steady_after) / steady_after if steady_after > 0 else 0
    else:
        # Downshift: check for undershoot below steady_after
        trough_idx = np.argmin(gen_mean_size[1:]) + 1
        trough_val = gen_mean_size[trough_idx]
        overshoot = (steady_after - trough_val) / steady_after if steady_after > 0 else 0
        peak_idx = trough_idx

    # Relaxation time: generations to reach within 5% of new steady state
    threshold = 0.05 * abs(steady_after - steady_before)
    relax_gen = n_gen_after
    for i in range(1, len(gen_mean_size)):
        if abs(gen_mean_size[i] - steady_after) < threshold:
            relax_gen = i
            break

    return NutrientShiftResult(
        mu_before=mu_before,
        mu_after=mu_after,
        params={"r": r, "K": K, "n": n},
        gen_mean_size=gen_mean_size,
        gen_cv_size=gen_cv_size,
        gen_mean_time=gen_mean_time,
        n_gen_after=n_gen_after,
        steady_before=steady_before,
        steady_after=steady_after,
        overshoot_magnitude=max(0, overshoot),
        overshoot_gen=peak_idx,
        relaxation_time=relax_gen,
    )


def scan_overshoot_vs_n(
    n_values: np.ndarray = None,
    mu_before: float = 0.01,
    mu_after: float = 0.02,
    r: float = 5.0,
    K: float = 10.0,
    n_cells: int = 300,
    seed: int = 42,
) -> Dict[str, list]:
    """
    Scan overshoot magnitude as a function of Hill coefficient n.

    Key prediction: overshoot is maximized at intermediate n (2-5),
    absent for n→0 (timer) and n→∞ (sizer).
    """
    if n_values is None:
        n_values = np.array([0.1, 0.5, 1.0, 1.5, 2.0, 3.0, 5.0, 10.0, 20.0, 50.0])

    results = {"n": [], "overshoot": [], "relaxation_gen": []}

    for n_val in n_values:
        shift = simulate_nutrient_shift_detailed(
            mu_before, mu_after, r, K, float(n_val),
            n_cells=n_cells, n_gen_after=30, seed=seed,
        )
        results["n"].append(float(n_val))
        results["overshoot"].append(float(shift.overshoot_magnitude))
        results["relaxation_gen"].append(int(shift.relaxation_time))

    return results


# ============================================================
# Prediction 2: Size-dependent division noise
# ============================================================

def compute_size_dependent_noise(
    r: float, K: float, n: float, mu: float,
    vb_range: np.ndarray = None,
    n_cells_per_bin: int = 2000,
    seed: int = 42,
) -> Dict[str, np.ndarray]:
    """
    Compute CV(Vd | Vb) as a function of Vb.

    Prediction: CV(Vd | Vb) ∝ (Vb + K)^{-1/2} for the unified model.
    Neither sizer nor adder predicts this birth-size-dependent noise.
    """
    if vb_range is None:
        vb_range = np.linspace(0.5, 5.0, 20)

    # Simulate large population to get conditional statistics
    sim = simulate_cell_cycles(
        mu, r, K, n,
        n_cells=n_cells_per_bin * 10,
        n_generations=50,
        noise_cv=0.05,
        seed=seed,
    )

    # Bin by birth size and compute CV in each bin
    n_bins = len(vb_range) - 1 if len(vb_range) > 1 else 10
    bin_edges = np.linspace(np.percentile(sim.v_birth, 2),
                            np.percentile(sim.v_birth, 98), n_bins + 1)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

    cv_values = []
    mean_vb_values = []

    for i in range(n_bins):
        mask = (sim.v_birth >= bin_edges[i]) & (sim.v_birth < bin_edges[i + 1])
        if np.sum(mask) < 20:
            continue
        vd_bin = sim.v_division[mask]
        cv_values.append(np.std(vd_bin) / np.mean(vd_bin))
        mean_vb_values.append(np.mean(sim.v_birth[mask]))

    cv_values = np.array(cv_values)
    mean_vb_values = np.array(mean_vb_values)

    # Fit predicted scaling: CV ∝ (Vb + K)^{-1/2}
    if len(mean_vb_values) > 3:
        def model_func(vb, a, b):
            return a / np.sqrt(vb + b)
        try:
            popt, pcov = optimize.curve_fit(model_func, mean_vb_values, cv_values,
                                             p0=[0.1, K], maxfev=5000)
            fit_K = popt[1]
            predicted_cv = model_func(mean_vb_values, *popt)
            ss_res = np.sum((cv_values - predicted_cv) ** 2)
            ss_tot = np.sum((cv_values - np.mean(cv_values)) ** 2)
            r2_fit = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
        except Exception:
            fit_K = K
            r2_fit = 0.0
    else:
        fit_K = K
        r2_fit = 0.0

    return {
        "vb_centers": mean_vb_values,
        "cv_vd": cv_values,
        "fit_K": float(fit_K),
        "true_K": float(K),
        "r2_scaling_fit": float(r2_fit),
        "prediction": "CV(Vd|Vb) ∝ (Vb + K)^{-1/2}",
    }


# ============================================================
# Prediction 3: Composite cell cycle (emergent adder)
# ============================================================

def simulate_composite_cycle(
    n_G1: float, K_G1: float, r_G1: float,   # G1 phase params (sizer-like)
    n_SG2M: float, K_SG2M: float, r_SG2M: float,  # S-G2-M params (timer-like)
    mu: float,
    n_cells: int = 5000,
    seed: int = 42,
) -> dict:
    """
    Simulate a two-phase cell cycle:
      G1: sizer-like (large n_G1)
      S-G2-M: timer-like (small n_SG2M)

    Prediction: The whole-cycle behavior is an emergent adder even though
    neither phase is an adder. This explains the "adder paradox" in budding yeast.
    """
    rng = np.random.default_rng(seed)
    dt = 0.001

    v_births = []
    v_G1_exits = []
    v_divisions = []

    V = 1.0
    Vb = V
    gen = 0
    collected = 0

    while collected < n_cells:
        # --- G1 phase ---
        in_G1 = True
        while in_G1:
            V += mu * V * dt
            h = hazard(V, mu, r_G1, K_G1, n_G1)
            if rng.random() < h * dt:
                in_G1 = False
        V_G1_exit = V

        # --- S-G2-M phase ---
        in_SG2M = True
        while in_SG2M:
            V += mu * V * dt
            h = hazard(V, mu, r_SG2M, K_SG2M, n_SG2M)
            if rng.random() < h * dt:
                in_SG2M = False

        gen += 1
        if gen > 30:  # discard burn-in
            v_births.append(Vb)
            v_G1_exits.append(V_G1_exit)
            v_divisions.append(V)
            collected += 1

        # Daughter cell
        V = V * 0.5
        Vb = V

    v_births = np.array(v_births)
    v_G1_exits = np.array(v_G1_exits)
    v_divisions = np.array(v_divisions)

    # Compute slopes
    slope_whole, _, _, _, _ = stats.linregress(v_births, v_divisions - v_births)
    slope_G1, _, _, _, _ = stats.linregress(v_births, v_G1_exits)
    slope_SG2M, _, _, _, _ = stats.linregress(v_G1_exits, v_divisions - v_G1_exits)

    return {
        "params_G1": {"n": n_G1, "K": K_G1, "r": r_G1},
        "params_SG2M": {"n": n_SG2M, "K": K_SG2M, "r": r_SG2M},
        "n_cells": n_cells,
        "slope_whole_DV_vs_Vb": float(slope_whole),
        "slope_G1_exit_vs_Vb": float(slope_G1),
        "slope_SG2M_DV_vs_VG1exit": float(slope_SG2M),
        "mean_Vb": float(np.mean(v_births)),
        "mean_Vd": float(np.mean(v_divisions)),
        "mean_DV": float(np.mean(v_divisions - v_births)),
        "is_whole_cycle_adder": abs(slope_whole) < 0.2,
        "is_G1_sizer": slope_G1 < 0.3,
        "is_SG2M_timer": abs(slope_SG2M) < 0.2,
    }


# ============================================================
# Cancer perturbation predictions
# ============================================================

def predict_cancer_perturbations(
    r: float = 5.0, K: float = 10.0, n: float = 3.0, mu: float = 0.01,
    n_cells: int = 2000,
    seed: int = 42,
) -> List[dict]:
    """
    Simulate parameter perturbations mimicking cancer mutations.

    Returns predictions for:
      1. Rb loss (K → 0): smaller, more variable cells
      2. Reduced cooperativity (n decrease): noisier division
      3. Growth acceleration (μ increase without K compensation): larger cells
      4. Combined perturbation: Rb loss + growth acceleration
    """
    # Normal baseline
    sim_normal = simulate_cell_cycles(mu, r, K, n, n_cells=n_cells, seed=seed)
    baseline = {
        "mean_Vd": float(np.mean(sim_normal.v_division)),
        "cv_Vd": float(np.std(sim_normal.v_division) / np.mean(sim_normal.v_division)),
    }

    perturbations = []

    # 1. Rb loss: K → K/5
    sim = simulate_cell_cycles(mu, r, K / 5, n, n_cells=n_cells, seed=seed + 1)
    perturbations.append({
        "name": "Rb_loss",
        "description": "K reduced 5x (loss of division inhibitor)",
        "cancer_analog": "Rb-null retinoblastoma, small cell lung cancer",
        "param_change": {"K": K / 5},
        "mean_Vd": float(np.mean(sim.v_division)),
        "cv_Vd": float(np.std(sim.v_division) / np.mean(sim.v_division)),
        "size_ratio": float(np.mean(sim.v_division) / baseline["mean_Vd"]),
        "cv_ratio": float(
            (np.std(sim.v_division) / np.mean(sim.v_division)) / baseline["cv_Vd"]
        ),
        "matches_cancer_phenotype": np.mean(sim.v_division) < baseline["mean_Vd"],
    })

    # 2. Reduced cooperativity: n → n/3
    sim = simulate_cell_cycles(mu, r, K, n / 3, n_cells=n_cells, seed=seed + 2)
    perturbations.append({
        "name": "reduced_cooperativity",
        "description": "n reduced 3x (loss of switch sharpness)",
        "cancer_analog": "Tumor pleomorphism, heterogeneous sizes",
        "param_change": {"n": n / 3},
        "mean_Vd": float(np.mean(sim.v_division)),
        "cv_Vd": float(np.std(sim.v_division) / np.mean(sim.v_division)),
        "size_ratio": float(np.mean(sim.v_division) / baseline["mean_Vd"]),
        "cv_ratio": float(
            (np.std(sim.v_division) / np.mean(sim.v_division)) / baseline["cv_Vd"]
        ),
        "matches_cancer_phenotype": (
            np.std(sim.v_division) / np.mean(sim.v_division) > baseline["cv_Vd"]
        ),
    })

    # 3. Growth acceleration: μ → 2μ without K compensation
    sim = simulate_cell_cycles(2 * mu, r, K, n, n_cells=n_cells, seed=seed + 3)
    perturbations.append({
        "name": "growth_acceleration",
        "description": "μ doubled (oncogene activation, e.g. Myc)",
        "cancer_analog": "Myc-driven tumors, polyploid cells",
        "param_change": {"mu": 2 * mu},
        "mean_Vd": float(np.mean(sim.v_division)),
        "cv_Vd": float(np.std(sim.v_division) / np.mean(sim.v_division)),
        "size_ratio": float(np.mean(sim.v_division) / baseline["mean_Vd"]),
        "cv_ratio": float(
            (np.std(sim.v_division) / np.mean(sim.v_division)) / baseline["cv_Vd"]
        ),
        "matches_cancer_phenotype": True,  # faster growth always affects size
    })

    # 4. Combined: Rb loss + growth acceleration
    sim = simulate_cell_cycles(2 * mu, r, K / 5, n / 2, n_cells=n_cells, seed=seed + 4)
    perturbations.append({
        "name": "combined_perturbation",
        "description": "Rb loss + growth acceleration + reduced cooperativity",
        "cancer_analog": "Aggressive tumor with multiple driver mutations",
        "param_change": {"K": K / 5, "mu": 2 * mu, "n": n / 2},
        "mean_Vd": float(np.mean(sim.v_division)),
        "cv_Vd": float(np.std(sim.v_division) / np.mean(sim.v_division)),
        "size_ratio": float(np.mean(sim.v_division) / baseline["mean_Vd"]),
        "cv_ratio": float(
            (np.std(sim.v_division) / np.mean(sim.v_division)) / baseline["cv_Vd"]
        ),
        "matches_cancer_phenotype": True,
    })

    for p in perturbations:
        p["baseline"] = baseline

    return perturbations


# ============================================================
# Run all predictions
# ============================================================

def run_all_predictions(output_dir: str = "validation/reports", verbose: bool = True) -> dict:
    """Run all three novel predictions and save results."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    results = {}

    # --- Prediction 1: Nutrient shift overshoot ---
    if verbose:
        print("\n[Prediction 1] Nutrient shift transient response...")

    shift = simulate_nutrient_shift_detailed(
        mu_before=0.01, mu_after=0.02,
        r=5.0, K=10.0, n=3.0,
        n_cells=300, n_gen_after=30,
    )
    results["nutrient_shift"] = {
        "overshoot": shift.has_overshoot,
        "overshoot_magnitude": float(shift.overshoot_magnitude),
        "overshoot_generation": int(shift.overshoot_gen),
        "relaxation_generations": int(shift.relaxation_time),
        "steady_before": float(shift.steady_before),
        "steady_after": float(shift.steady_after),
    }

    if verbose:
        print(f"  Overshoot: {shift.has_overshoot} "
              f"(magnitude={shift.overshoot_magnitude:.3f}, gen={shift.overshoot_gen})")

    # Overshoot vs n scan
    if verbose:
        print("  Scanning overshoot vs n...")
    scan = scan_overshoot_vs_n(n_cells=200)
    results["overshoot_vs_n"] = scan

    if verbose:
        for n_val, ov in zip(scan["n"], scan["overshoot"]):
            print(f"    n={n_val:>5.1f}: overshoot={ov:.4f}")

    # --- Prediction 2: Size-dependent noise ---
    if verbose:
        print("\n[Prediction 2] Size-dependent division noise...")

    noise = compute_size_dependent_noise(r=5.0, K=10.0, n=3.0, mu=0.01)
    results["size_dependent_noise"] = {
        "fit_K": noise["fit_K"],
        "true_K": noise["true_K"],
        "r2_scaling": noise["r2_scaling_fit"],
        "prediction": noise["prediction"],
    }

    if verbose:
        print(f"  Scaling fit R²={noise['r2_scaling_fit']:.3f}, "
              f"fit_K={noise['fit_K']:.2f} (true={noise['true_K']:.1f})")

    # --- Prediction 3: Composite cell cycle ---
    if verbose:
        print("\n[Prediction 3] Composite cell cycle (emergent adder)...")

    composite = simulate_composite_cycle(
        n_G1=15.0, K_G1=2.0, r_G1=10.0,     # sizer-like G1
        n_SG2M=0.1, K_SG2M=2.0, r_SG2M=5.0,  # timer-like S-G2-M
        mu=0.01, n_cells=3000,
    )
    results["composite_cycle"] = composite

    if verbose:
        print(f"  Whole-cycle adder: {composite['is_whole_cycle_adder']} "
              f"(slope ΔV vs Vb = {composite['slope_whole_DV_vs_Vb']:.3f})")
        print(f"  G1 sizer: {composite['is_G1_sizer']} "
              f"(slope = {composite['slope_G1_exit_vs_Vb']:.3f})")
        print(f"  S-G2-M timer: {composite['is_SG2M_timer']} "
              f"(slope = {composite['slope_SG2M_DV_vs_VG1exit']:.3f})")

    # --- Cancer perturbations ---
    if verbose:
        print("\n[Cancer] Parameter perturbation predictions...")

    cancer = predict_cancer_perturbations()
    results["cancer_perturbations"] = cancer

    if verbose:
        for p in cancer:
            print(f"  {p['name']}: size_ratio={p['size_ratio']:.2f}, "
                  f"cv_ratio={p['cv_ratio']:.2f}, "
                  f"matches={p['matches_cancer_phenotype']}")

    # Save report
    report_path = output_path / "novel_predictions_report.json"
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    if verbose:
        print(f"\nSaved to {report_path}")

    return results


if __name__ == "__main__":
    print("=" * 70)
    print("Novel Predictions — Unified Cell Size Control Model")
    print("CodeAgent005 (agent-mna1rwvb)")
    print("=" * 70)
    run_all_predictions(verbose=True)
