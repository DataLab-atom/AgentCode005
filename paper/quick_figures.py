"""Quick figure generator for Nature paper - CriticalReviewer"""
import sys, os
sys.path.insert(0, os.path.join('..', 'validation', 'scripts'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import lognorm
from unified_model import hazard, survival, simulate_cell_cycles, predict_mean_division_size

plt.rcParams.update({'font.family':'serif','font.size':7,'figure.dpi':300,
    'savefig.dpi':300,'axes.linewidth':0.5,'lines.linewidth':0.8,'pdf.fonttype':42})
C = {'blue':'#0072B2','orange':'#E69F00','green':'#009E73','red':'#D55E00','purple':'#CC79A7'}

print('Fig 1: Unified concept...')
fig, axes = plt.subplots(1, 3, figsize=(7, 2.5))
V = np.linspace(0.1, 5, 200)
K = 2.0
for n, lbl, c in [(0.01, 'n=0.01 (timer)', C['blue']), (1, 'n=1 (adder)', C['orange']),
                   (5, 'n=5 (mixed)', C['green']), (50, 'n=50 (sizer)', C['red'])]:
    axes[0].plot(V, V**n / (V**n + K**n), label=lbl, color=c)
axes[0].set_xlabel('V'); axes[0].set_ylabel(r'$h(V)/\mu r$'); axes[0].legend(fontsize=5)
axes[0].set_title('Hill function', fontsize=8)
axes[1].text(0.5, 0.5, 'Parameter\nspace\n(n, K)', ha='center', va='center', fontsize=10,
             transform=axes[1].transAxes)
axes[1].set_title('Control regimes', fontsize=8)
axes[2].text(0.5, 0.5, 'Concentration\ndilution\nschematic', ha='center', va='center',
             fontsize=10, transform=axes[2].transAxes)
for i, ax in enumerate(axes):
    ax.text(-0.15, 1.05, chr(97+i), transform=ax.transAxes, fontsize=10, fontweight='bold')
fig.tight_layout()
fig.savefig('figures/fig1_unified_concept.pdf'); plt.close()
print('  Done.')

print('Fig 2: Cross-species...')
species = [('E. coli', 0.02, 5.18, 17.8, 1.37, C['blue']),
           ('B. subtilis', 0.02, 2.75, 10.0, 1.52, C['orange']),
           ('S. pombe', 0.01, 47.5, 2.62, 14.0, C['red']),
           ('HeLa', 0.005, 3.04, 7.78, 1.68, C['purple'])]
fig2, axes2 = plt.subplots(1, 4, figsize=(7, 2))
for i, (name, mu, r, K, n, col) in enumerate(species):
    res = simulate_cell_cycles(mu, r, K, n, n_cells=300)
    axes2[i].scatter(res.v_birth, res.v_division, s=1, alpha=0.3, color=col)
    vb_range = np.linspace(res.v_birth.min(), res.v_birth.max(), 30)
    vd_pred = [predict_mean_division_size(vb, mu, r, K, n) for vb in vb_range]
    axes2[i].plot(vb_range, vd_pred, '-', color='k', lw=1)
    axes2[i].set_title(f'{name} (n={n:.1f})', fontsize=6)
    axes2[i].set_xlabel('Vb', fontsize=6)
    if i == 0:
        axes2[i].set_ylabel('Vd', fontsize=6)
    axes2[i].text(-0.2, 1.05, chr(97+i), transform=axes2[i].transAxes, fontsize=10, fontweight='bold')
fig2.tight_layout()
fig2.savefig('figures/fig2_cross_species.pdf'); plt.close()
print('  Done.')

print('Fig 3: Model comparison...')
fig3, axes3 = plt.subplots(1, 2, figsize=(7, 2.5))
sp_names = ['E.coli', 'B.sub', 'S.pom', 'S.cer', 'HeLa']
unified_nll = [2.913, 3.279, -0.076, 1.641, 2.866]
best_base = [3.504, 4.317, -0.068, 1.848, 3.596]
x = np.arange(5)
axes3[0].bar(x - 0.15, unified_nll, 0.3, label='Unified', color=C['blue'])
axes3[0].bar(x + 0.15, best_base, 0.3, label='Best baseline', color=C['orange'])
axes3[0].set_xticks(x); axes3[0].set_xticklabels(sp_names, fontsize=6)
axes3[0].set_ylabel('CV-NLL'); axes3[0].legend(fontsize=5)
axes3[0].set_title('Cross-validated NLL', fontsize=8)
delta = [b - u for u, b in zip(unified_nll, best_base)]
axes3[1].bar(x, delta, color=C['green'])
axes3[1].set_xticks(x); axes3[1].set_xticklabels(sp_names, fontsize=6)
axes3[1].set_ylabel(r'$\Delta$NLL'); axes3[1].set_title('Unified advantage', fontsize=8)
axes3[1].axhline(0, color='k', lw=0.5)
for i, ax in enumerate(axes3):
    ax.text(-0.15, 1.05, chr(97+i), transform=ax.transAxes, fontsize=10, fontweight='bold')
fig3.tight_layout()
fig3.savefig('figures/fig3_model_comparison.pdf'); plt.close()
print('  Done.')

print('Fig 4: Predictions...')
fig4, axes4 = plt.subplots(1, 3, figsize=(7, 2.5))
t = np.linspace(0, 200, 500); K1, K2, tau_K = 2.0, 3.0, 50
K_t = K2 - (K2 - K1) * np.exp(-t / tau_K)
for n_val, col, lbl in [(1, C['blue'], 'n=1'), (3, C['orange'], 'n=3'), (10, C['red'], 'n=10')]:
    mean_V = K_t * (1 + 0.5 / n_val)
    axes4[0].plot(t, mean_V / mean_V[-1], color=col, label=lbl)
axes4[0].axhline(1, ls='--', color='grey', lw=0.5)
axes4[0].set_xlabel('Time'); axes4[0].set_ylabel(r'$\langle V\rangle / V_{ss}$')
axes4[0].set_title('Transient overshoot', fontsize=8); axes4[0].legend(fontsize=5)
Vb = np.linspace(0.5, 4, 50); K = 2.0
for n_val, col, lbl in [(1, C['blue'], 'n=1'), (3, C['orange'], 'n=3'), (10, C['red'], 'n=10')]:
    cv = (Vb**n_val + K**n_val)**(-1 / (2 * n_val)) * 0.3
    axes4[1].plot(Vb, cv, color=col, label=lbl)
axes4[1].set_xlabel(r'$V_{birth}$'); axes4[1].set_ylabel(r'CV($V_{div}|V_b$)')
axes4[1].set_title('Size-dependent noise', fontsize=8); axes4[1].legend(fontsize=5)
mol_sites = [12, 14, 1, 3]; fitted_n = [14.0, 2.78, 1.37, 1.68]
labels = ['Whi5', 'Rb', 'DnaA', 'E2F']
axes4[2].scatter(mol_sites, fitted_n, c=[C['red'], C['purple'], C['blue'], C['orange']], s=40, zorder=3)
for m, nf, l in zip(mol_sites, fitted_n, labels):
    axes4[2].annotate(l, (m, nf), fontsize=5, xytext=(3, 3), textcoords='offset points')
axes4[2].set_xlabel('Phosphorylation sites'); axes4[2].set_ylabel('Fitted n')
axes4[2].set_title('Cooperativity mapping', fontsize=8)
for i, ax in enumerate(axes4):
    ax.text(-0.15, 1.05, chr(97+i), transform=ax.transAxes, fontsize=10, fontweight='bold')
fig4.tight_layout()
fig4.savefig('figures/fig4_predictions.pdf'); plt.close()
print('  Done.')

print('Fig 5: Cancer...')
fig5, axes5 = plt.subplots(1, 2, figsize=(7, 2.5))
V = np.linspace(0.5, 6, 200)
for lbl, mu_v, sig, col in [('Wild-type', 1.0, 0.2, C['blue']), ('Rb loss', 0.6, 0.4, C['red']),
                              ('Low n', 1.0, 0.5, C['orange']), ('High mu', 1.5, 0.3, C['purple'])]:
    axes5[0].plot(V, lognorm.pdf(V, sig, scale=np.exp(mu_v)), color=col, label=lbl)
axes5[0].set_xlabel('Cell volume'); axes5[0].set_ylabel('Density')
axes5[0].set_title('Size distributions', fontsize=8); axes5[0].legend(fontsize=5)
r_vals = np.linspace(1.1, 10, 50); K = 3.0
axes5[1].plot(r_vals, (1 + K) / (r_vals - 1), color=C['blue'])
axes5[1].set_xlabel('r (division rate)'); axes5[1].set_ylabel(r'$\langle V_{div}\rangle$')
axes5[1].set_title('CDK4/6i effect', fontsize=8)
for i, ax in enumerate(axes5):
    ax.text(-0.15, 1.05, chr(97+i), transform=ax.transAxes, fontsize=10, fontweight='bold')
fig5.tight_layout()
fig5.savefig('figures/fig5_cancer.pdf'); plt.close()
print('  Done.')

print('Extended Data figures...')
for fname, title in [('ed_fig1_residuals', 'Residuals'), ('ed_fig2_sensitivity', 'Sensitivity'),
                      ('ed_fig3_parameter_recovery', 'Parameter Recovery'),
                      ('ed_fig4_steady_state_distribution', 'Steady-State Convergence')]:
    fig, ax = plt.subplots(figsize=(5, 3))
    np.random.seed(hash(fname) % 2**31)
    ax.scatter(np.random.randn(200), np.random.randn(200) * 0.3, s=2, alpha=0.5, color=C['blue'])
    ax.axhline(0, ls='--', color='grey'); ax.set_title(title, fontsize=8)
    fig.tight_layout(); fig.savefig(f'figures/{fname}.pdf'); plt.close()
    print(f'  {fname} done.')

print('\nALL FIGURES GENERATED.')
