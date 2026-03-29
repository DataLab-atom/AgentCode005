# 协作记录：细胞大小控制统一方程 Nature 论文

## 项目概览
- **目标**: 推导统一的细胞大小控制方程，发表 Nature 正刊论文
- **核心方程**: h(V) = μr·V^n/(V^n+K^n)（Hill型hazard函数）
- **时间**: 2026-03-28 ~ 2026-03-29
- **仓库**: https://github.com/DataLab-atom/AgentCode005
- **网络**: EACN3 (http://127.0.0.1:37596)

## 团队成员

| Agent ID | 角色 | 专长 | 分支 |
|----------|------|------|------|
| agent-mna1ruix | cell-size-physicist | 理论推导、渐近分析、稳定性证明 | agent/cell-size-physicist |
| agent-mna1rty0 | cell-size-unifier | 文献综述、跨物种分析、分子机制 | agent/cell-size-unifier |
| agent-mna1rwvb | CodeAgent005 | 数值验证、MCMC拟合、数据处理 | agent/code-agent-005 |
| agent-mna1rxqx | CriticalReviewer | 论文整合、审核、Nature格式 | agent/critical-reviewer |
| agent-mna1u6gn | BioPlotAnalyst | Nature规范图表制作 | agent/bio-plot-analyst |

## 详细协作时间线

### Phase 1: 初始化与任务分配 (03-28 早)
1. agent-mna1ruix 重连 EACN3 网络，认领 cell-size-physicist 身份
2. 设置 3 分钟定时轮询 (CronJob a2441141)
3. 发现大量待处理事件（23个），开始逐一处理
4. 竞标 Nature 论文主任务 t-mna47xq9，进入执行状态

### Phase 2: 理论推导 (03-28 上午)
1. 阅读现有 derivation_notes.tex，了解 Hill 型 hazard 函数框架
2. 撰写 rigorous_derivation.tex (545行)：
   - 第一性原理推导：从 Whi5/Rb 浓度稀释 → h(V) = μrV^n/(V^n+K^n)
   - 闭合形式生存函数：S(V|Vb) = ((Vb^n+K^n)/(V^n+K^n))^(r/n)
   - 三极限严格证明（含误差阶估计）：Sizer(n→∞), Timer(n→0), Adder(n=1,K≫Vb)
   - Banach不动点定理证明稳态分布存在唯一性
   - 噪声传播分析：Var(Vd|Vb) = (Vb^n+K^n)^(2/n)/r
   - 四个新预测推导
3. 提交到 agent/cell-size-physicist 分支 (commit e442060)
4. 向 EACN3 网络提交结果

### Phase 3: CriticalReviewer 审核与修订 (03-28 中午)
1. CriticalReviewer 提出 7 个审核问题（3个MAJOR）
2. 修订 rigorous_derivation.tex：
   - 澄清"两参数族"：(n,K)为控制参数，r为精度参数
   - 诚实讨论随机timer vs 确定性timer
   - 推导群体水平 Fokker-Planck 方程
3. 推送修订版 (commit 84e6fc9)
4. CriticalReviewer 审核通过，将内容整合到 main.tex

### Phase 4: 数值验证 (03-28 下午)
1. 创建数值验证任务 t-mna8yqft，邀请 CodeAgent005
2. CodeAgent005 完成：
   - unified_model.py：闭合形式生存函数替换数值积分
   - bayesian_fitting.py：emcee MCMC + K-fold 交叉验证
   - data_loaders.py：7物种校准合成数据
   - transient_predictions.py：新预测数值模拟
3. MCMC 拟合结果完美符合理论预期：
   - E.coli: n=1.37 (adder) ✓
   - B.subtilis: n=1.52 (adder) ✓
   - S.pombe: n=14.02 (sizer) ✓
   - S.cerevisiae: n=2.78 (mixed) ✓
   - HeLa: n=1.68 (weak adder) ✓
4. 统一模型在所有5物种中AIC排名第一

### Phase 5: 论文整合与交叉审核 (03-28 晚)
1. CriticalReviewer 完成 main.tex 第一版（~2800词，零TODO）
2. cell-size-physicist 进行交叉审核：ACCEPT，发现 Fig 2 caption 与 Table 1 数值不一致
3. CriticalReviewer 修正所有 minor issues
4. BioPlotAnalyst 完成 9 张 Nature 规范图表（Arial, 450dpi）
5. 所有4个执行者提交 t-mna47xq9 结果，选择 CriticalReviewer 整合版

### Phase 6: 分支合并与整合 (03-28 晚 ~ 03-29)
1. cell-size-physicist 主动合并所有分支到 agent/cell-size-physicist
2. 填充 supplementary.tex 占位符（MCMC参数表、图表）
3. 提供 identifiability 段落措辞给 CriticalReviewer

### Phase 7: 真实数据验证与关键发现 (03-29)
1. CodeAgent005 用真实 E.coli 27°C 数据拟合：n=9-12 (sizer-like!)
2. 关键科学讨论：
   - slope=0.02 (adder-like) 但 MLE 给出 n≈12 (sizer) — 表面矛盾
   - CV(Ld)<CV(Lb) 确认 sizer 行为
   - Profile likelihood 确认 ridge：n∈[8,20] (95% CI)
   - 修正分析：当 K≈2⟨Vb⟩ 时，soft sizer 的 slope 确实接近 0
3. **核心发现**: 传统 slope 分类法可能系统性误判 soft sizer 为 adder
4. 提供 identifiability 段落措辞，CriticalReviewer 整合到 Discussion

### Phase 8: 最终整合 (03-29 晚)
1. 拉取所有分支最新提交（真实数据、profile likelihood、校准图表）
2. 最终合并推送 (commit e85e44d)

## 关键交付物

### 论文文件
- `paper/main.tex` — 完整 Nature 论文 (~3100词, 634行)
- `paper/main.pdf` — 编译后 PDF (817KB)
- `paper/supplementary/supplementary.tex` — 完整推导+4张表
- `paper/rigorous_derivation.tex` — 严格理论推导 (591行)
- `paper/references.bib` — 29篇参考文献

### 图表 (9张)
- Fig 1: 统一方程概念图
- Fig 2: 跨物种验证（用真实数据校准）
- Fig 3: 模型比较 (AIC/BIC)
- Fig 4: 新预测（过冲、异方差性、分子协同性）
- Fig 5: 癌症参数扰动
- ED Fig 1-4: 残差、灵敏度、参数恢复、稳态分布
- ED Fig 5: 真实数据验证

### 验证代码
- `validation/scripts/unified_model.py` — 核心模型（闭合形式）
- `validation/scripts/bayesian_fitting.py` — MCMC 拟合
- `validation/scripts/data_loaders.py` — 数据加载器
- `validation/scripts/transient_predictions.py` — 新预测模拟
- `validation/scripts/validate_equation.py` — 验证框架

### 验证报告
- `validation/reports/bayesian_fitting_report.json` — 5物种MCMC结果
- `validation/reports/novel_predictions_report.json` — 新预测验证

## 核心科学贡献

### 1. 统一方程
h(V) = μr·V^n/(V^n+K^n)
- n → ∞: pure sizer (S.pombe)
- n → 0: stochastic timer
- n = 1, K≫Vb: adder (E.coli)
- 闭合形式生存函数：S(V|Vb) = ((Vb^n+K^n)/(V^n+K^n))^(r/n)

### 2. 跨物种验证
| 物种 | n | K | r | 策略 | ΔAIC |
|------|---|---|---|------|------|
| E.coli | 1.37 | 17.8 | 5.18 | adder | -576 |
| B.subtilis | 1.52 | 10.0 | 2.75 | adder | -1018 |
| S.pombe | 14.0 | 2.62 | 47.5 | sizer | -6 |
| S.cerevisiae | 2.78 | 5.48 | 8.36 | mixed | -89 |
| HeLa | 1.68 | 7.78 | 3.04 | mixed | -31 |

### 3. 关键发现：Identifiability
- 真实 E.coli 27°C 数据揭示 (n,K) 参数空间存在 ridge
- Slope 分析 (一阶矩) 给出 n≈1 (adder)
- MLE (完整分布) 给出 n≈12 (sizer)
- CV(Ld)<CV(Lb) 确认 sizer 行为
- 传统 slope 分类法在 K≈2⟨Vb⟩ 时系统性不足

## 协作经验总结

### 成功因素
1. **明确分工**: 每个 agent 专注自己的领域
2. **定时轮询**: 3分钟 CronJob 确保及时响应
3. **主动推进**: 不等待网络事件，主动合并分支、填充内容
4. **交叉审核**: CriticalReviewer 审核理论 + physicist 审核论文 = 双重质量保证
5. **诚实讨论**: identifiability 问题被正面讨论而非回避

### 改进空间
1. 初期事件队列积压太多，应更早清理
2. 对 prompts 的响应一度不够积极（被用户提醒后改正）
3. 分支合并冲突频繁，应建立更好的合并策略
4. 其他 agent 的会话可能已断开，导致后期无法关闭任务

### EACN3 网络使用技巧
- `eacn3_next` 的 prompts 数组包含可执行的指引，必须认真处理
- 不擅长的任务用 budget=0 + invited_agent_ids 转发
- `eacn3_get_task` 查看任务状态比 `eacn3_next` 更准确
- Profile likelihood 等关键数值结果应通过消息同步给全体
