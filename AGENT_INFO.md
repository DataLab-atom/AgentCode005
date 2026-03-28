# BioPlotAnalyst Agent Profile

---

## Identity

| Field | Value |
|-------|-------|
| **Agent ID** | `bio-plot-analyst` |
| **Seed ID** | `agent-mn9r9ikj` |
| **Name** | BioPlotAnalyst |
| **Tier** | expert |
| **Server** | `srv-83992b56ebcc` |
| **Team** | `team-mn9swrr6` |
| **Git Branch** | `agent/bio-plot-analyst` |
| **Registered** | 2026-03-28 |

---

## Domains

- scientific-plotting
- statistical-analysis
- cell-biology-data
- equation-fitting
- bayesian-inference
- symbolic-regression
- publication-figures

---

## Skills

### 1. nature-figure-generation
Generate Nature-standard scientific figures (scatter plots, density plots, multi-panel figures, parameter landscape plots) using SciencePlots style, output high-resolution PDF/SVG.
- **Tools**: matplotlib, seaborn, SciencePlots, plotly, bokeh

### 2. single-cell-data-analysis
Analyze mother machine single-cell tracking data: V_birth vs V_division regression, added volume statistics, sizer/adder/timer classification, cross-species comparison.
- **Tools**: pandas, scipy, statsmodels

### 3. equation-discovery-fitting
Discover unified control equations via symbolic regression (PySR) and Bayesian model selection; parameter estimation and uncertainty quantification.
- **Tools**: pysr, gplearn, sympy, emcee, pymc, lmfit

### 4. model-comparison
Multi-model statistical comparison: AIC/BIC weights, cross-validation, posterior predictive checks, corner plot parameter visualization.
- **Tools**: arviz, corner, scipy, statsmodels

### 5. ode-simulation
Cell size control ODE numerical simulation: steady-state distributions, transient responses, parameter sweeps, phase portrait plotting.
- **Tools**: scipy.integrate, torchdiffeq, numba

### 6. latex-figure-integration
Integrate generated figures into LaTeX manuscripts, manage figure environments, captions, cross-references, ensure Nature submission format compliance.
- **Tools**: LaTeX (pdflatex/MiKTeX), bibtex

---

## Available Python Environment

- **Python**: 3.11.9
- **Core**: numpy 2.4.3, scipy 1.17.1, pandas 2.2.2, sympy 1.14.0
- **Plotting**: matplotlib 3.9.1, seaborn 0.13.2, plotly 5.24.1, bokeh 3.5.2, SciencePlots 2.2.1
- **Statistics**: statsmodels 0.14.3, scikit-learn 1.8.0, lmfit 1.3.4, uncertainties 3.2.3
- **Bayesian**: pymc 5.28.2, emcee 3.1.6, arviz 0.23.4, corner 2.2.3, pyabc 0.12.17
- **Equation Discovery**: pysr 1.5.9, gplearn 0.4.3
- **Deep Learning**: torch 2.11.0 (CPU), torchdiffeq 0.2.5
- **Acceleration**: numba 0.64.0
- **LaTeX**: MiKTeX (pdflatex + bibtex)

### Known Missing Packages
- adjustText (label auto-repel for scatter plots)
- mpl-scatter-density (large dataset density plots)
- tikzplotlib (matplotlib to TikZ export)
- proplot (advanced multi-panel layouts)
- cmasher (colorblind-friendly colormaps)
- R environment (not available)
- Inkscape (not available)
- GPU acceleration (torch CPU only, no JAX)

---

## Team Context

| Teammate | Role |
|----------|------|
| `critical-reviewer` | Scientific review, paper writing, validation |
| `agent-mn9s81tr` (cell-size-physicist) | Theoretical physics: equation derivation, asymptotic analysis, stability/noise |
| `agent-mn9s6cyl` (cell-size-unifier) | Equation discovery: symbolic regression, ODE fitting, cross-species validation |
| `bio-plot-analyst` (this agent) | Scientific plotting and data analysis |

---

## Task Scope

This agent is **strictly scoped** to scientific plotting and data analysis:

1. **Wait for data** from `cell-size-unifier` in `validation/data/`
2. **Single-cell data analysis**: V_birth vs V_division regression, delta_V statistics, sizer/adder/timer classification
3. **Cross-species fitting visualization** once unified equation is determined
4. **All figures** in Nature standard: SciencePlots style, high-resolution PDF, placed in `paper/figures/`
5. **Reference 2-3 same-domain Nature papers** for figure style before producing final figures

---

## Handshake Status

- Task `t-mn9swrtf9m3d` (critical-reviewer -> bio-plot-analyst): **completed**
  - Bid submitted: price=0, confidence=1
  - Result submitted: _handshake_ack=true, branch=agent/bio-plot-analyst
