"""
Unified Cell Size Control Model: Hill-type Hazard Function
===========================================================

Core implementation of the unified equation:
  Growth:           dV/dt = mu * V
  Division hazard:  h(V) = mu * r * V^n / (V^n + K^n)

Parameters:
  n — Hill coefficient (cooperativity): timer(n→0), adder(n≈1), sizer(n→∞)
  K — characteristic size threshold
  r — division rate scaling
  mu — exponential growth rate

This module provides:
  1. Stochastic cell cycle simulation (Monte Carlo)
  2. Steady-state distribution solver
  3. Limiting case verification
  4. Cross-species parameter fitting
  5. Transient response prediction
"""

import numpy as np
from scipy import stats, integrate, optimize
from scipy.special import beta as beta_func, betainc
from dataclasses import dataclass, field
from typing import Tuple, List, Dict, Optional
import warnings


# ============================================================
# Core model
# ============================================================

def hazard(V: float, mu: float, r: float, K: float, n: float) -> float:
    """Instantaneous division rate h(V) = mu * r * V^n / (V^n + K^n)."""
    if n < 1e-6:
        return mu * r * 0.5
    Vn = V ** n
    return mu * r * Vn / (Vn + K ** n)


def survival(V: float, Vb: float, mu: float, r: float, K: float, n: float) -> float:
    """
    Survival function S(V | Vb) = P(no division before reaching volume V).
    S(V) = exp(-integral_{Vb}^{V} h(V')/(mu*V') dV')
    """
    if V <= Vb:
        return 1.0

    def integrand(v):
        return hazard(v, mu, r, K, n) / (mu * v)

    result, _ = integrate.quad(integrand, Vb, V, limit=200)
    return np.exp(-result)


def division_pdf(Vd: float, Vb: float, mu: float, r: float, K: float, n: float) -> float:
    """Division volume probability density p(Vd | Vb)."""
    h = hazard(Vd, mu, r, K, n)
    S = survival(Vd, Vb, mu, r, K, n)
    return h / (mu * Vd) * S


# ============================================================
# Monte Carlo cell cycle simulation
# ============================================================

@dataclass
class SimulationResult:
    """Results from a Monte Carlo cell cycle simulation."""
    v_birth: np.ndarray
    v_division: np.ndarray
    delta_v: np.ndarray
    interdiv_time: np.ndarray
    growth_rate: float
    params: dict

    @property
    def n_cells(self) -> int:
        return len(self.v_birth)

    @property
    def slope_vdiv_vbirth(self) -> float:
        """Slope of V_div vs V_birth regression."""
        s, _, _, _, _ = stats.linregress(self.v_birth, self.v_division)
        return s

    @property
    def slope_deltav_vbirth(self) -> float:
        """Slope of DeltaV vs V_birth regression."""
        s, _, _, _, _ = stats.linregress(self.v_birth, self.delta_v)
        return s

    @property
    def cv_division(self) -> float:
        return np.std(self.v_division) / np.mean(self.v_division)

    @property
    def cv_deltav(self) -> float:
        return np.std(self.delta_v) / np.mean(self.delta_v)

    @property
    def cv_time(self) -> float:
        return np.std(self.interdiv_time) / np.mean(self.interdiv_time)


def simulate_cell_cycles(
    mu: float,
    r: float,
    K: float,
    n: float,
    n_cells: int = 10000,
    n_generations: int = 50,
    dt: float = 0.001,
    v0: float = 1.0,
    noise_cv: float = 0.0,
    seed: int = 42,
) -> SimulationResult:
    """
    Monte Carlo simulation of cell division using the Hill hazard model.

    Each time step:
      1. Cell grows: V += mu * V * dt
      2. Division probability: P(divide in dt) = h(V) * dt
      3. If divides: daughter gets V/2 (+ optional noise)

    Runs n_generations to reach steady state, then collects n_cells.
    """
    rng = np.random.default_rng(seed)

    v_births = []
    v_divisions = []
    times = []

    V = v0
    t_cell = 0.0
    Vb = v0
    collected = 0
    generation = 0

    max_steps = int(5e7)
    step = 0

    while collected < n_cells and step < max_steps:
        step += 1
        dV = mu * V * dt
        V += dV
        t_cell += dt

        h = hazard(V, mu, r, K, n)
        p_divide = h * dt

        if rng.random() < p_divide:
            generation += 1

            if generation > n_generations:
                v_births.append(Vb)
                v_divisions.append(V)
                times.append(t_cell)
                collected += 1

            if noise_cv > 0:
                split = rng.normal(0.5, noise_cv * 0.5)
                split = np.clip(split, 0.3, 0.7)
            else:
                split = 0.5

            V = V * split
            Vb = V
            t_cell = 0.0

    v_births = np.array(v_births[:n_cells])
    v_divisions = np.array(v_divisions[:n_cells])
    times = np.array(times[:n_cells])
    delta_v = v_divisions - v_births

    return SimulationResult(
        v_birth=v_births,
        v_division=v_divisions,
        delta_v=delta_v,
        interdiv_time=times,
        growth_rate=mu,
        params={"mu": mu, "r": r, "K": K, "n": n},
    )


# ============================================================
# Analytical predictions
# ============================================================

def predict_mean_division_size(Vb: float, mu: float, r: float, K: float, n: float,
                                V_max_factor: float = 10.0) -> float:
    """Compute E[V_div | V_birth] by numerical integration of p(Vd) * Vd."""
    V_max = Vb * V_max_factor

    def integrand(Vd):
        return Vd * division_pdf(Vd, Vb, mu, r, K, n)

    result, _ = integrate.quad(integrand, Vb, V_max, limit=200)
    return result


def predict_mean_added_volume(Vb: float, mu: float, r: float, K: float, n: float) -> float:
    """E[DeltaV | V_birth] = E[V_div | V_birth] - V_birth."""
    return predict_mean_division_size(Vb, mu, r, K, n) - Vb


def predict_mean_interdiv_time(Vb: float, mu: float, r: float, K: float, n: float,
                                V_max_factor: float = 10.0) -> float:
    """E[T | V_birth] by converting volume integral to time."""
    V_max = Vb * V_max_factor

    def integrand(Vd):
        T = np.log(Vd / Vb) / mu
        return T * division_pdf(Vd, Vb, mu, r, K, n)

    result, _ = integrate.quad(integrand, Vb, V_max, limit=200)
    return result


# ============================================================
# Limiting case verification
# ============================================================

def verify_sizer_limit(r: float = 50.0, K: float = 2.0, n: float = 50.0,
                       mu: float = 0.01, n_cells: int = 5000) -> dict:
    """Verify sizer behavior at large n: V_div ≈ K regardless of V_birth."""
    sim = simulate_cell_cycles(mu, r, K, n, n_cells=n_cells, n_generations=30, seed=1)
    slope = sim.slope_vdiv_vbirth
    cv = sim.cv_division
    mean_vd = np.mean(sim.v_division)
    return {
        "regime": "sizer",
        "params": {"n": n, "K": K, "r": r},
        "slope_Vdiv_vs_Vbirth": slope,
        "cv_Vdiv": cv,
        "mean_Vdiv": mean_vd,
        "expected_Vdiv": K,
        "pass": abs(slope) < 0.2 and cv < 0.15,
    }


def verify_adder_limit(r: float = 5.0, K: float = 20.0, n: float = 1.0,
                       mu: float = 0.01, n_cells: int = 5000) -> dict:
    """Verify adder behavior at n=1, K >> Vb: DeltaV ≈ const."""
    sim = simulate_cell_cycles(mu, r, K, n, n_cells=n_cells, n_generations=30, seed=2)
    slope = sim.slope_deltav_vbirth
    cv = sim.cv_deltav
    mean_dv = np.mean(sim.delta_v)
    expected_dv = K * np.log(2) / r
    return {
        "regime": "adder",
        "params": {"n": n, "K": K, "r": r},
        "slope_DeltaV_vs_Vbirth": slope,
        "cv_DeltaV": cv,
        "mean_DeltaV": mean_dv,
        "expected_DeltaV": expected_dv,
        "pass": abs(slope) < 0.2 and cv < 0.3,
    }


def verify_timer_limit(r: float = 5.0, K: float = 2.0, n: float = 0.001,
                       mu: float = 0.01, n_cells: int = 5000) -> dict:
    """Verify timer behavior at n→0: interdivision time ≈ const."""
    sim = simulate_cell_cycles(mu, r, K, n, n_cells=n_cells, n_generations=30, seed=3)
    slope_t, _, _, _, _ = stats.linregress(sim.v_birth, sim.interdiv_time)
    cv_t = sim.cv_time
    mean_t = np.mean(sim.interdiv_time)
    expected_t = 2.0 / (mu * r)
    return {
        "regime": "timer",
        "params": {"n": n, "K": K, "r": r},
        "slope_T_vs_Vbirth": slope_t,
        "cv_T": cv_t,
        "mean_T": mean_t,
        "expected_T": expected_t,
        "pass": cv_t < 0.5,
    }


# ============================================================
# Cross-species parameter fitting
# ============================================================

def negative_log_likelihood(params: np.ndarray, v_birth: np.ndarray,
                            v_division: np.ndarray, mu: float) -> float:
    """
    Negative log-likelihood for observed (V_birth, V_division) pairs
    given model parameters [r, K, n].
    """
    r, K, n = params
    if r <= 0 or K <= 0 or n <= 0:
        return 1e12

    nll = 0.0
    for vb, vd in zip(v_birth, v_division):
        if vd <= vb:
            nll += 100.0
            continue
        pdf = division_pdf(vd, vb, mu, r, K, n)
        if pdf <= 0 or np.isnan(pdf):
            nll += 100.0
        else:
            nll += -np.log(pdf)

    return nll


def fit_species(v_birth: np.ndarray, v_division: np.ndarray, mu: float,
                init_params: Optional[np.ndarray] = None,
                method: str = "Nelder-Mead") -> dict:
    """
    Fit the unified model to single-species data via MLE.

    Returns dict with best-fit params, NLL, AIC, BIC, R^2.
    """
    if init_params is None:
        K_init = np.mean(v_division) * 1.5
        init_params = np.array([5.0, K_init, 2.0])

    result = optimize.minimize(
        negative_log_likelihood,
        init_params,
        args=(v_birth, v_division, mu),
        method=method,
        options={"maxiter": 5000, "xatol": 1e-6, "fatol": 1e-6},
    )

    r_fit, K_fit, n_fit = result.x
    nll = result.fun
    n_data = len(v_birth)
    k_params = 3

    aic = 2 * nll + 2 * k_params
    bic = 2 * nll + k_params * np.log(n_data)

    # Compute R^2 for V_division prediction
    v_div_pred = np.array([
        predict_mean_division_size(vb, mu, r_fit, K_fit, n_fit)
        for vb in v_birth
    ])
    ss_res = np.sum((v_division - v_div_pred) ** 2)
    ss_tot = np.sum((v_division - np.mean(v_division)) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0

    return {
        "r": r_fit,
        "K": K_fit,
        "n": n_fit,
        "nll": nll,
        "aic": aic,
        "bic": bic,
        "r2": r2,
        "converged": result.success,
        "message": result.message,
    }


# ============================================================
# Competing model baselines for AIC comparison
# ============================================================

def fit_pure_sizer(v_birth: np.ndarray, v_division: np.ndarray) -> dict:
    """Pure sizer: V_div = V* (constant). MLE = mean(V_div)."""
    v_star = np.mean(v_division)
    residuals = v_division - v_star
    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((v_division - v_star) ** 2)
    n = len(v_division)
    sigma2 = ss_res / n
    nll = 0.5 * n * (np.log(2 * np.pi * sigma2) + 1)
    return {"model": "sizer", "V_star": v_star, "nll": nll,
            "aic": 2 * nll + 2, "bic": 2 * nll + np.log(n),
            "r2": 0.0}  # R^2 = 0 by construction (constant prediction)


def fit_pure_adder(v_birth: np.ndarray, v_division: np.ndarray) -> dict:
    """Pure adder: DeltaV = const. MLE = mean(DeltaV)."""
    dv = v_division - v_birth
    dv_star = np.mean(dv)
    v_pred = v_birth + dv_star
    residuals = v_division - v_pred
    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((v_division - np.mean(v_division)) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    n = len(v_division)
    sigma2 = ss_res / n
    nll = 0.5 * n * (np.log(2 * np.pi * sigma2) + 1) if sigma2 > 0 else 0
    return {"model": "adder", "DeltaV": dv_star, "nll": nll,
            "aic": 2 * nll + 2, "bic": 2 * nll + np.log(n),
            "r2": r2}


def fit_linear_interpolation(v_birth: np.ndarray, v_division: np.ndarray) -> dict:
    """Linear model: V_div = a * V_birth + b (2 params)."""
    slope, intercept, r_val, p_val, se = stats.linregress(v_birth, v_division)
    v_pred = slope * v_birth + intercept
    residuals = v_division - v_pred
    ss_res = np.sum(residuals ** 2)
    n = len(v_division)
    sigma2 = ss_res / n
    nll = 0.5 * n * (np.log(2 * np.pi * sigma2) + 1) if sigma2 > 0 else 0
    return {"model": "linear", "slope": slope, "intercept": intercept,
            "nll": nll, "aic": 2 * nll + 4, "bic": 2 * nll + 2 * np.log(n),
            "r2": r_val ** 2}


# ============================================================
# Transient response prediction (novel prediction #1)
# ============================================================

def simulate_nutrient_shift(
    mu_before: float, mu_after: float,
    r: float, K: float, n: float,
    n_cells: int = 500,
    n_gen_before: int = 50,
    n_gen_after: int = 30,
    seed: int = 100,
) -> dict:
    """
    Simulate a nutrient upshift: mu changes from mu_before to mu_after.
    Track mean cell size across generations after the shift.
    """
    # Reach steady state at mu_before
    sim_before = simulate_cell_cycles(
        mu_before, r, K, n, n_cells=n_cells,
        n_generations=n_gen_before, seed=seed
    )
    mean_size_before = np.mean(sim_before.v_division)

    # Now simulate generation by generation after shift
    rng = np.random.default_rng(seed + 1)
    # Start from steady-state birth sizes
    current_births = sim_before.v_division / 2

    gen_means = [mean_size_before]
    mu = mu_after
    dt = 0.001

    for gen in range(n_gen_after):
        div_sizes = []
        next_births = []
        for Vb in current_births:
            V = Vb
            step = 0
            while step < 500000:
                step += 1
                V += mu * V * dt
                h = hazard(V, mu, r, K, n)
                if rng.random() < h * dt:
                    break
            div_sizes.append(V)
            next_births.append(V * 0.5)

        gen_means.append(np.mean(div_sizes))
        current_births = np.array(next_births)

    return {
        "mu_before": mu_before,
        "mu_after": mu_after,
        "mean_size_trajectory": gen_means,
        "steady_state_before": mean_size_before,
        "steady_state_after": gen_means[-1],
        "has_overshoot": any(
            gen_means[i] > max(gen_means[0], gen_means[-1]) * 1.05
            for i in range(1, len(gen_means) - 1)
        ),
    }


# ============================================================
# Entry point: run all verifications
# ============================================================

if __name__ == "__main__":
    import json
    import time

    print("=" * 70)
    print("Unified Cell Size Control Model — Verification Suite")
    print("=" * 70)
    print()

    # 1. Limiting cases
    print("[1/4] Verifying limiting cases...")
    t0 = time.time()

    sizer = verify_sizer_limit(n_cells=3000)
    print(f"  Sizer (n={sizer['params']['n']}): slope={sizer['slope_Vdiv_vs_Vbirth']:.4f}, "
          f"CV={sizer['cv_Vdiv']:.4f}, PASS={sizer['pass']}")

    adder = verify_adder_limit(n_cells=3000)
    print(f"  Adder (n={adder['params']['n']}): slope(DV)={adder['slope_DeltaV_vs_Vbirth']:.4f}, "
          f"CV={adder['cv_DeltaV']:.4f}, PASS={adder['pass']}")

    timer = verify_timer_limit(n_cells=3000)
    print(f"  Timer (n={timer['params']['n']}): CV(T)={timer['cv_T']:.4f}, PASS={timer['pass']}")

    print(f"  Completed in {time.time()-t0:.1f}s")
    print()

    # 2. Generate synthetic cross-species data
    print("[2/4] Generating synthetic cross-species data...")
    t0 = time.time()

    species_params = {
        "E_coli":      {"mu": 0.02, "r": 5.0,  "K": 20.0, "n": 1.2},
        "B_subtilis":  {"mu": 0.015,"r": 4.0,  "K": 18.0, "n": 1.0},
        "S_pombe":     {"mu": 0.008,"r": 30.0, "K": 2.5,  "n": 15.0},
        "S_cerevisiae":{"mu": 0.01, "r": 8.0,  "K": 5.0,  "n": 3.0},
        "HeLa":        {"mu": 0.005,"r": 3.0,  "K": 8.0,  "n": 2.0},
    }

    species_data = {}
    for sp, p in species_params.items():
        sim = simulate_cell_cycles(
            p["mu"], p["r"], p["K"], p["n"],
            n_cells=2000, n_generations=40, noise_cv=0.05,
            seed=hash(sp) % (2**31)
        )
        species_data[sp] = sim
        print(f"  {sp}: {sim.n_cells} cells, <Vd>={np.mean(sim.v_division):.3f}, "
              f"slope(Vd|Vb)={sim.slope_vdiv_vbirth:.3f}")

    print(f"  Completed in {time.time()-t0:.1f}s")
    print()

    # 3. Fit unified model to each species
    print("[3/4] Fitting unified model to each species...")
    t0 = time.time()

    fit_results = {}
    for sp, sim in species_data.items():
        # Use subset for faster fitting
        idx = np.random.choice(sim.n_cells, min(500, sim.n_cells), replace=False)
        vb = sim.v_birth[idx]
        vd = sim.v_division[idx]
        true_p = species_params[sp]

        result = fit_species(vb, vd, true_p["mu"],
                            init_params=np.array([true_p["r"]*1.2, true_p["K"]*0.8, true_p["n"]*1.1]))
        fit_results[sp] = result

        # Also fit baselines
        sizer_fit = fit_pure_sizer(vb, vd)
        adder_fit = fit_pure_adder(vb, vd)
        linear_fit = fit_linear_interpolation(vb, vd)

        print(f"  {sp}: R²={result['r2']:.4f}, n={result['n']:.2f} (true={true_p['n']:.1f}), "
              f"K={result['K']:.2f} (true={true_p['K']:.1f})")
        print(f"    AIC: unified={result['aic']:.0f}, sizer={sizer_fit['aic']:.0f}, "
              f"adder={adder_fit['aic']:.0f}, linear={linear_fit['aic']:.0f}")

    print(f"  Completed in {time.time()-t0:.1f}s")
    print()

    # 4. Transient response prediction
    print("[4/4] Simulating nutrient shift (novel prediction)...")
    t0 = time.time()

    shift = simulate_nutrient_shift(
        mu_before=0.01, mu_after=0.02,
        r=5.0, K=10.0, n=3.0,
        n_cells=200, n_gen_after=20
    )
    print(f"  Size before shift: {shift['steady_state_before']:.3f}")
    print(f"  Size after shift:  {shift['steady_state_after']:.3f}")
    print(f"  Overshoot detected: {shift['has_overshoot']}")
    print(f"  Completed in {time.time()-t0:.1f}s")

    # Save report
    print()
    print("=" * 70)
    report = {
        "limiting_cases": {
            "sizer": {k: float(v) if isinstance(v, (np.floating, float)) else v
                      for k, v in sizer.items()},
            "adder": {k: float(v) if isinstance(v, (np.floating, float)) else v
                      for k, v in adder.items()},
            "timer": {k: float(v) if isinstance(v, (np.floating, float)) else v
                      for k, v in timer.items()},
        },
        "cross_species_fits": {
            sp: {k: float(v) if isinstance(v, (np.floating, float)) else v
                 for k, v in r.items()}
            for sp, r in fit_results.items()
        },
        "nutrient_shift": {
            "steady_state_before": shift["steady_state_before"],
            "steady_state_after": shift["steady_state_after"],
            "has_overshoot": shift["has_overshoot"],
        },
    }

    report_path = "D:/Git/Bio/myagents/AgentCode005/validation/reports/verification_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"Report saved to {report_path}")
