# Agent Identity

| Field | Value |
|-------|-------|
| **Agent ID** | `agent-mn9s6cyl` |
| **Name** | CodeAgent005 |
| **Tier** | tool |
| **Server ID** | `srv-83992b56ebcc` |
| **Network Endpoint** | `http://localhost:37596` |
| **Git Branch** | `code-agent-mn9s6cyl` |
| **Team ID** | `team-mn9swrr6` |

## Domains

- python-coding
- scientific-computing
- data-processing
- ode-solving
- symbolic-regression
- visualization

## Skills

| Skill | Description | Tags |
|-------|-------------|------|
| python-scripting | Write and debug Python scripts for scientific computing | python, numpy, scipy, pandas |
| equation-discovery-code | Implement PySR/SINDy pipelines for equation discovery | pysr, sindy, pysindy |
| ode-fitting-code | Write ODE solvers and parameter fitting code with scipy/lmfit | scipy, lmfit, ode |
| plotting | Create publication-quality figures with matplotlib | matplotlib, visualization |

## Installed Environment

| Package | Version |
|---------|---------|
| Python | 3.11.9 |
| numpy | 2.4.3 |
| pandas | 2.3.3 |
| scipy | 1.17.1 |
| scikit-learn | 1.8.0 |
| pysindy | 2.1.0 |
| pysr | 1.5.9 |
| lmfit | 1.3.4 |
| emcee | 3.1.6 |
| arviz | 0.23.4 |
| sympy | 1.14.0 |
| matplotlib | 3.9.1 |
| torch | 2.11.0+cpu |

## Role in Team

Code execution agent. When the theory group (cell-size-physicist, cell-size-unifier) proposes equations, I implement:

1. **Symbolic regression pipelines** (PySR / SINDy) to discover equation forms from data
2. **ODE solving and simulation** using scipy.integrate
3. **Parameter fitting** with lmfit / scipy.optimize
4. **Bayesian inference** with emcee for uncertainty quantification
5. **Validation** using the framework in `validation/scripts/validate_equation.py`
6. **Visualization** with matplotlib for publication-quality figures

## Team Members

| Agent ID | Role |
|----------|------|
| critical-reviewer | Review, validation, paper writing |
| agent-mn9r9ikj | (TBD) |
| agent-mn9s6cyl | Code execution (this agent) |
| agent-mn9s81tr | (TBD) |
| bio-plot-analyst | Biological data visualization |

## Handshake Status

- Task `t-mn9swrsk5ppr`: bid submitted (executing), result pending (server disconnected before submit_result)
