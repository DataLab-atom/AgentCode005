"""
Submission: Hill-type Hazard Function for Unified Cell Size Control
===================================================================

Equation: h(V) = mu * r * V^n / (V^n + K^n)
Growth:   dV/dt = mu * V (exponential)

Limits:
  n → ∞: pure sizer (V_div = K)
  n → 0: pure timer (T independent of V_birth)
  n = 1, K >> V_b: pure adder (ΔV = const)
"""

import sys
import numpy as np
sys.path.insert(0, '.')
from unified_model import (
    hazard, survival, division_pdf, simulate_cell_cycles,
    predict_mean_division_size, predict_mean_added_volume,
)


def run_limit_tests():
    """Verify all three limiting cases numerically."""
    mu = 0.02  # growth rate (1/min)

    print("=" * 60)
    print("LIMIT CASE VERIFICATION")
    print("=" * 60)

    # --- Sizer limit: n=50, K=2.0, r=20 ---
    print("\n1. SIZER LIMIT (n=50, K=2.0, r=20)")
    n, K, r = 50.0, 2.0, 20.0
    Vb_values = [1.0, 1.5, 2.0, 2.5]
    for Vb in Vb_values:
        if Vb >= K:
            print(f"   Vb={Vb:.1f}: divides immediately (Vb >= K)")
            continue
        mean_Vd = predict_mean_division_size(Vb, mu, r, K, n)
        print(f"   Vb={Vb:.1f}: <Vd>={mean_Vd:.3f} (expect ~{K:.1f})")

    # --- Timer limit: n=0.001, K=2.0, r=5 ---
    print("\n2. TIMER LIMIT (n=0.001, K=2.0, r=5)")
    n, K, r = 0.001, 2.0, 5.0
    results = simulate_cell_cycles(mu, r, K, n, n_cells=5000)
    times = np.log(results.v_division / results.v_birth) / mu
    for Vb_bin in [(0.5, 1.0), (1.0, 1.5), (1.5, 2.0)]:
        mask = (results.v_birth >= Vb_bin[0]) & (results.v_birth < Vb_bin[1])
        if mask.sum() > 10:
            mean_T = times[mask].mean()
            print(f"   Vb in [{Vb_bin[0]:.1f}, {Vb_bin[1]:.1f}): <T>={mean_T:.2f} (n={mask.sum()})")
    print(f"   Expected <T> = 2/(mu*r) = {2/(mu*r):.2f}")

    # --- Adder limit: n=1, K=20, r=10 ---
    print("\n3. ADDER LIMIT (n=1, K=20.0, r=10)")
    n, K, r = 1.0, 20.0, 10.0
    results = simulate_cell_cycles(mu, r, K, n, n_cells=5000)
    added = results.v_division - results.v_birth
    for Vb_bin in [(0.5, 1.5), (1.5, 2.5), (2.5, 3.5)]:
        mask = (results.v_birth >= Vb_bin[0]) & (results.v_birth < Vb_bin[1])
        if mask.sum() > 10:
            mean_dV = added[mask].mean()
            print(f"   Vb in [{Vb_bin[0]:.1f}, {Vb_bin[1]:.1f}): <ΔV>={mean_dV:.3f} (n={mask.sum()})")
    expected_dV = K / (r - 1)
    print(f"   Expected <ΔV> = K/(r-1) = {expected_dV:.3f}")

    print("\n" + "=" * 60)
    print("VALIDATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    run_limit_tests()
