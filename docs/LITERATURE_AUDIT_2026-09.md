# 文献审计：决策类候选方向的可占性判定

日期：2026-09-17
审计对象：**桌面文档《固定翼无人机智能决策与自主飞行项目_初步研究计划_V0.1》提出的四条因果链**
（链 A 不确定性→决策边界；链 C 当前动作→未来可行空间；链 D 计算价值；链 B 可恢复性→临界延迟）
审计人：外部审计（非项目负责人）
状态：**审计报告。本文件不产生任何肯定性新颖性主张。**

---

## 0. 本文件的规范声明

按 `docs/CONVENTIONS.md` 第 5 节与 `LITERATURE_MAP.md` 第 9 节：

- 本审计基于**题录 + 摘要**，**未读任何一篇正文**。因此按 Phase B 门槛，
  本文件**只允许得出否定性结论**（"某方向已被占据"），
  **不允许得出肯定性结论**（"某方向还有空间"）。
- 凡本文件出现的"仍开放"表述，一律等价于"**在本次检索范围内未发现已被占据**"，
  不等于"无人做过"。
- 全部条目均为 Scopus / OpenAlex / arXiv 实际返回，无编造。
  检索式的可复现清单见第 5 节。

证据等级沿用项目规范：**A/B/C/D**。本文件的判定结论最高不超过 **C**
（因为未读正文）。

---

## 1. 结论摘要（先给判定）

| 链 | 桌面文档给的价值 | 本次审计判定 | 主要依据 |
| --- | --- | --- | --- |
| 链 A 不确定性→决策边界 | ★★★★★，可能比 C 更易获奖 | **风险高**：概念已被 RDM/DAPP 传统彻底闭合 | 第 2 节 |
| 链 C 当前动作→未来可行空间 | ★★★★★（一号选择） | **生死线未过**：存在"等价奖励重塑"的致命反驳 | 第 3 节 |
| 链 D 计算价值 VOC | ★★★★，论文潜力★★★★★ | **框架已被占据**，只剩一个非单调性内核 | 第 4.1 节 |
| 链 B 可恢复性→临界延迟 | ★★★★☆ | **朴素版已被航空适航文献杀死** | 第 4.2 节 |

**最重要的一条发现（与桌面文档无关）**：本仓库 EXP-FW-V1-23 已推出的
精确法则 `τL* = 1/(ω(1+w))`，**本身就是链 B 所寻找的 `T_critical` 的一个精确实例**，
而且比桌面文档里那条模糊假设强得多。详见第 6 节。

---

## 2. 链 A：不确定性 → 决策边界

**桌面文档设想**：构造 U ∈ {0..5}，测 A/B/C 三个动作的成功率交叉，得到临界不确定度
U*，画出 x=U、y=Recoverability 的"决策地图"（regime map）。

### 2.1 已经闭合（证据等级 C，基于题录与摘要）

**"不确定性高时应该更稳健"这个命题本身无缺口**，已被三条独立传统闭合：

| 标题 | 年份 | 期刊 | 第一作者 | DOI |
| --- | --- | --- | --- | --- |
| The Price of Robustness | 2004 | Operations Research | Bertsimas D. | 10.1287/opre.1030.0065 |
| Dynamic adaptive policy pathways: A method for crafting robust decisions for a deeply uncertain world | 2013 | Global Environmental Change | Haasnoot M. | 10.1016/j.gloenvcha.2012.12.006 |
| A General, Analytic Method for Generating Robust Strategies and Narrative Scenarios | 2006 | Management Science | Lempert R.J. | 10.1287/mnsc.1050.0472 |
| Improving scenario discovery for handling heterogeneous uncertainties and multinomial classified outcomes | 2015 | Environmental Modelling & Software | Kwakkel J. | 10.1016/j.envsoft.2015.11.020 |
| A Methodology for Trading-Off Performance and Robustness Under Uncertainty | 2005 | ASME IDETC/CIE | Mourelatos Z.P. | 10.1115/detc2005-85019 |

要点：

- Bertsimas–Sim 的"不确定性预算 Γ"已给出**稳健性代价随不确定性增长的定量界**。
  桌面文档想用标量 U 扫描决策，方法学先例就是 Γ 与 info-gap 的 α。
- Haasnoot 2013 的 DAPP **本质就是画"在什么条件下从策略 A 切换到策略 B"的图**，
  并通过 transfer point 标注切换时刻。**桌面文档设想的 U\* 就是 DAPP 的 transfer point；
  设想的 regime map 就是 DAPP 的 pathway map。**
- Kwakkel 的 scenario discovery（PRIM）已能**自动圈出"策略失败区域"的边界**。

### 2.2 最接近的无人机先例

| 标题 | 年份 | 期刊 | 第一作者 | DOI | 平台 |
| --- | --- | --- | --- | --- | --- |
| Robust Satisficing Decision Making for Unmanned Aerial Vehicle Complex Missions under Severe Uncertainty | 2016 | PLoS ONE | Ji X. | 10.1371/journal.pone.0166448 | 通用 |
| A Tube-based Robust MPC for a Fixed-wing UAV: an Application for Precision Farming | 2018 | arXiv | Mammarella M. | 10.48550/arXiv.1805.04295 | **固定翼** |
| Robust Wind-Aware Path Optimization Onboard Small Fixed-wing UAVs | 2023 | AIAA SciTech | Bücher T. | 10.2514/6.2023-2640 | **固定翼** |
| Wind-Aware Trajectory Planning for Fixed-Wing Aircraft in Loss of Thrust Emergencies | 2018 | IEEE DASC | Paul S. | 10.1109/DASC.2018.8569842 | **固定翼** |
| Adaptive risk tendency in uncertainty-aware motion planning using risk-sensitive Reinforcement Learning | 2024 | Advanced Engineering Informatics | Wang Z. | 10.1016/j.aei.2024.102942 | 非航空 |

Ji 2016 是全库最接近"稳健性随不确定水平变化"的 UAV 工作，但它输出**单一最稳健策略**，
未画 A/B 相对优劣的切换图。

### 2.3 判定

- **"存在临界不确定度 U\*"这一命题，在误差单调影响性能的假设下近乎自明**
  （稳健动作的劣势不随不确定性增长、优势增长 ⇒ 必存在交点）。
  按现在的表述投期刊，**大概率以"tautological / already known in RDM"被拒**。
- 未被占据的只剩两点：(i) **U\* 对任务压力的非单调回折**（极端压力下稳健动作重新变差）；
  (ii) 固定翼物理参数进入 U\* 的标度律。
- **必须正面引用的"挡箭牌"**：Bertsimas 2004、Haasnoot 2013、Ji 2016。
  不引用它们并说明差异，会被直接指为 re-invention。

---

## 3. 链 C：当前动作 → 未来可行空间（桌面文档的一号选择）

**桌面文档设想**：定义 F_future = 执行当前动作后仍可完成的未来任务/机动空间，
对比 Myopic（只优化 J_now）与 Future-aware（优化 J_now − λ·F_future）。
桌面文档自己标注的最大风险是：**"需要证明未来可行空间不是简单换一个 reward。"**

**本次审计判定：这条风险是真实的，而且比桌面文档估计的更严重。这是链 C 的生死线。**

### 3.1 致命机制：奖励重塑的策略不变性

强化学习与决策论有一组**策略不变性定理**：若附加项能写成状态势函数 Φ 的差分，
则最优策略**完全不变**。

| 标题 | 年份 | 会议/期刊 | 第一作者 | 被引 | 说明 |
| --- | --- | --- | --- | --- | --- |
| Theoretical considerations of potential-based reward shaping for multi-agent systems | 2011 | AAMAS | Devlin S. | 103 | 势函数塑形的理论边界 |
| Dynamic potential-based reward shaping | 2012 | AAMAS | Devlin S. | 109 | 动态势函数下仍保持策略不变 |
| Policy invariance under reward transformations for multi-objective reinforcement learning | 2017 | Neurocomputing | Mannion P. | 48 | 奖励变换下的策略不变性（多目标版） |

**对链 C 的直接含义**：如果 `F_future` 可以表示为**当前状态的函数**，
那么 `J_total = J_now − λ·F_future` 与 `J_now` **产生完全相同的最优策略**——
"future-aware planner"会退化成 myopic planner，实验必然测出"无差异"。
这正是桌面文档担心的那件事，而且它是一个**已证明的定理**，不是一个待检验的猜想。

### 3.2 逃逸路径（链 C 唯一可能的立足点）

要让 F_future 不被策略不变性吞掉，它必须**不是当前状态的函数**。三条可能的出口：

1. **F_future 依赖未来任务上下文**（非马尔可夫奖励）。
   已有"非马尔可夫奖励的决策论规划"传统可借鉴：
   | 标题 | 年份 | 期刊 | 第一作者 | DOI |
   | --- | --- | --- | --- | --- |
   | Decision-theoretic planning with non-Markovian rewards | 2006 | JAIR | Thiébaux S. | 10.1613/jair.1676 |
2. **F_future 作为约束而非代价**（可行性 vs 最优性的区别、viability kernel）。
3. **有限时域 + 不可逆动力学**下势函数分解失效。

**注意**：这三条出口都意味着链 C 的卖点不能是"加一项奖励"，而必须是
"当前决策改变了后续**可行域**（feasible set），这是一个约束层面的问题"。
桌面文档现在的表述（`J_total = J_now − λ·F_future`）**恰好踩在第 3.1 节的定理上**，
按此表述做实验，预期结果是零差异。

### 3.3 正面的检索证据（不完备，仅供方向判断）

- `TITLE-ABS-KEY("reachability" AND "decision making" AND ("backup" OR "fallback" OR "abort"))`
  → **全库仅 6 条**，且**无一条是固定翼**：

  | 标题 | 年份 | 会议/期刊 | 平台 |
  | --- | --- | --- | --- |
  | Powered Descent Decision Making: A Reachability-Steering Approach | 2026 | AIAA SciTech | 航天 |
  | Online Safety Verification of Autonomous Driving Decision-Making Based on Dynamic Reachability Analysis | 2023 | IEEE Access | 自动驾驶 |
  | Contact Planning for Multilegged Robots Under Constraints Through Parallel MCTS | 2025 | IEEE T-RO | 腿式机器人 |
  | Stochastic predictive control for crash avoidance in autonomous vehicles based on stochastic reachable set threat assessment | 2021 | ASME IMECE | 自动驾驶 |

- `TITLE-ABS-KEY("option preservation" OR "keeping options open" AND robot)` → **0 条**。
- `TITLE-ABS-KEY("future feasible" OR "future feasibility" AND planning)` → 22 条，
  **无一条与选题相关**（全被能源/医学/社科污染）。

**解读（务必按第 0 节的强度规则读）**：这说明"选项保留/未来可行空间"**不是本领域的既有术语**。
两种可能——(a) 确实没人做；(b) 该概念在别的名字下被处理了
（reachability、viability、safety margin、backup plan、abort feasibility）。
**第二种可能性更高**，因此不能凭术语空缺断言存在空间。
最接近的邻居是腿式机器人的接触点选择（当前落脚点消耗未来落脚选项），
这提示链 C 的真实机制可能是"**不可逆承诺**"，而非"未来可行空间"。

### 3.4 判定

链 C **目前过不了生死线**：桌面文档给的目标函数形式直接落在一个策略不变性定理上。
若要继续，必须把命题改造成"当前动作改变后续**可行域**"的约束型问题，
并证明该约束**不能**被写成状态势函数。
**在这些完成之前，链 C 不得立项。**

---

## 4. 链 D 与链 B

### 4.1 链 D：计算价值（VOC）——框架已被占据

**"value of computation"是成熟术语**（Scopus 37 条，可上溯至 1988）：

| 标题 | 年份 | 会议/期刊 | 第一作者 | 被引 | DOI |
| --- | --- | --- | --- | --- | --- |
| Reasoning Under Varying and Uncertain Resource Constraints | 1988 | AAAI | Horvitz E.J. | 101 | — |
| Principles of metareasoning | 1991 | Artificial Intelligence | Russell S. | — | 10.1016/0004-3702(91)90015-C |
| Deliberation scheduling for problem solving in time-constrained environments | 1994 | Artificial Intelligence | Boddy M. | — | 10.1016/0004-3702(94)90054-X |
| Resource-bounded sensing and planning in autonomous systems | 1996 | Autonomous Robots | Zilberstein S. | — | 10.1007/BF00162466 |
| Allocating planning effort when actions expire | 2019 | AAAI | Shperberg S.S. | — | 10.1609/aaai.v33i01.33012371 |
| Situated Temporal Planning Using Deadline-aware Metareasoning | 2021 | ICAPS | Shperberg S.S. | — | 10.1609/icaps.v31i1.15979 |
| Learning When to Quit: Meta-Reasoning for Motion Planning | 2021 | IROS | Sung Y. | — | 10.1109/IROS51168.2021.9636864 |
| Metareasoning for Safe Decision Making in Autonomous Systems | 2022 | ICRA | Svegliato J. | — | 10.1109/ICRA46639.2022.9811887 |
| Belief Space Metareasoning for Exception Recovery | 2019 | IROS | Svegliato J. | — | 10.1109/IROS40897.2019.8967676 |
| Using metareasoning to improve autonomous robot planning | 2023 | SPIE | Herrmann J.W. | — | 10.1117/12.2662961 |
| Computationally adaptive multi-objective trajectory optimization for UAS with variable planning deadlines | 2009 | IEEE Aerospace | Narayan P. | — | 10.1109/AERO.2009.4839607 |
| MLAE2: Metareasoning for Latency-Aware Energy-Efficient Autonomous Nano-Drones | 2023 | ISCAS | Navardi M. | — | 10.1109/ISCAS46773.2023.10181715 |
| Static and dynamic values of computation in MCTS | 2020 | UAI | Sezener E. | — | — |
| Time Spent Thinking in Online Chess Reflects the Value of Computation | 2025 | Cognitive Science | Russek E.M. | — | 10.1111/cogs.70119 |

**已闭合**：VOC 的形式化（1991）、时间约束下的计算调度（1994–1996）、
"何时停止规划"（Sung 2021 / Svegliato 2020）、截止与动作过期驱动的元推理（Shperberg 2019/2021）、
**无人机上的延迟感知元推理**（Navardi 2023、Narayan 2009）。

**结论**："把元推理/VOC 用到无人机" **不是新意**。Shperberg 的"动作会过期 → 算太晚无价值"
已经覆盖了桌面文档假设中"极低裕度 → 计算无价值"的那一端。

**仅剩的内核**：VOC 对"剩余可恢复裕度"**非单调、在中段取峰**。
本次检索未发现该形态，但**未发现 ≠ 不存在**，且该断言强度只能是 C。

### 4.2 链 B：可恢复性 → 临界延迟——朴素版已被杀死

**航空适航与人因文献已研究"何时就来不及了"数十年**：

| 标题 | 年份 | 期刊/会议 | 第一作者 | DOI | 说明 |
| --- | --- | --- | --- | --- | --- |
| Go-Around Criteria Refinement for Transport Category Aircraft | 2022 | J. Air Transportation | Campbell A.M. | 10.2514/1.D0250 | 模拟机实验检验"500 ft 不符即复飞"准则 |
| Determination of rejected landing roll runway point-of-no-return and go-around in transport category airplanes | 2016 | IJAAA | Daidzic N.E. | 10.15394/ijaaa.2016.1110 | 落地相位的不可返回点 |
| Interpretable Tracking and Detection of Unstable Approaches Using Tunnel Gaussian Process | 2023 | IEEE TAES | Goh S.K. | 10.1109/TAES.2022.3217994 | 在线判定"再继续就晚了" |
| Launch-pad abort flight envelope computation for a personnel launch vehicle using reachability | 2005 | AIAA GNC | Kitsios I. | 10.2514/6.2005-6150 | 用**可达集**算中止可行包线 |
| Triggering algorithm based on inevitable collision states for autonomous emergency braking | 2015 | IEEE IV | Savino G. | 10.1109/IVS.2015.7225845 | 用 ICS 推导最晚制动时刻 |
| Provably safe navigation for mobile robots with limited field-of-views in dynamic environments | 2012 | Autonomous Robots | Bouraine S. | 10.1007/s10514-011-9258-8 | ICS / 被动安全 |
| Preflight contingency planning approach for fixed wing UAVs with engine failure in the presence of winds | 2019 | Sensors | Ayhan B. | 10.3390/s19020227 | **固定翼** UAV 应急着陆预规划 |
| Generalizing minimum safe operating altitudes for fixed-wing UAVs in real-time | 2024 | J. Field Robotics | Milne A. | 10.1002/rob.22331 | **固定翼** 在线最低安全高度 = 安全裕度在线计算 |
| Safe Low-Altitude Navigation in Steep Terrain With Fixed-Wing Aerial Vehicles | 2024 | IEEE RA-L | Lim J. | 10.1109/LRA.2024.3368800 | **固定翼** 不可避免碰撞状态/可达性 |
| Risk-Aware Markov Decision Process Contingency Management Autonomy for UAS | 2024 | J. Aerospace Info. Systems | Sharma P. | 10.2514/1.I011235 | 风险感知 MDP 应急管理 |

**关键判定**：中断起飞 V1、决断高度、稳定进近准则、点-不可返回，
**本质上就是 `T_critical = f(状态, 性能)`**，且已被适航体系解决。
因此"研究何时来不及决策"这一朴素表述**新颖性基本归零**。

**未被覆盖的（仍属 C 级）**：
- 航空的临界时刻是**离线、确定性、按适航数据预计算、服务跑道阶段与有人机组**。
  把"任意飞行状态的剩余恢复能力"作为**在线、随不确定性变化的**决策截止来源，
  用于**航路/任务中段的固定翼无人机**（该阶段无适航程序）——未发现直接对应工作。
- `TITLE-ABS-KEY(("decision deadline" OR "computational deadline" OR "planning deadline") AND (safety OR recovery OR robot OR UAV))`
  → **仅 5 条**。

---

## 5. 检索可复现清单

| 工具 | 说明 |
| --- | --- |
| Scopus API | 主力。查询式见下，字段 `TITLE-ABS-KEY` |
| OpenAlex | 交叉验证，`https://api.openalex.org/works?search=...` |
| arXiv | 补充预印本 |

Scopus 主检索式（链 A/C/D/B 各约 10–25 组，摘要为节选）：

```text
链 A：uncertainty threshold decision switching robustness / price of robustness /
      performance robustness trade-off boundary / robust decision making deep uncertainty
链 C：potential-based reward shaping / policy invariance reward shaping /
      option preservation keeping options open / irreversible decision UAV aircraft /
      reachability decision making backup fallback abort / future feasible planning
链 D：metareasoning robot / value of computation / deliberation scheduling /
      anytime planning UAV / deadline aware metareasoning / when to stop planning
链 B：go-around decision pilot / decision height unstable approach /
      rejected takeoff decision speed / point of no return landing /
      contingency fixed-wing engine failure / last safe moment /
      inevitable collision states emergency braking
```

**明确未覆盖**：IEEE Xplore 全文层、AIAA 与 Elsevier 付费全文、CNKI 中文库。
**全文阅读数量：0 篇。** 这是本审计最大的缺口，也限制了其上界（第 0 节）。

---

## 6. 本仓库已有资产与桌面文档的关系（重要）

本仓库 README 记载的 EXP-FW-V1-23 结论：

```text
τL* = 1 / (ω · (1 + w))
无量纲形式  ω · τL* = 1/(1+w) 弧度
```

**这是链 B 所寻找的 `T_critical` 的一个精确、可推导、经 45 点网格验证的实例。**

与桌面文档的区别：

| 维度 | 桌面文档的链 B | 本仓库 EXP-FW-V1-23 |
| --- | --- | --- |
| 形式 | 假设 `T_critical = f(M_R, U, x)` | **精确闭式** `τL* = 1/(ω(1+w))` |
| 推导 | 无 | 三行解析推导 |
| 验证 | 无 | 45 点网格，偏差 0.000 |
| 证据等级 | 无 | **A** |
| 平台 | 泛泛"固定翼" | 具体构造（JAIS 2020 围栏缓冲） |

**战略含义**：仓库里已经握着一个桌面文档在寻找但没找到的东西。
桌面文档的四条链（A/B/C/D）在文献上各自有致命风险，
而仓库的实际资产（缓冲充分性 + 精确延迟法则）**已经是一个完整的、
可投稿的结果**，且其"被抢先"风险已由 FW-D-005 处理为"验证缺口"。

---

## 7. 下一步（建议，非指令）

按 `CONVENTIONS.md` 与 `EXPERIMENT_STRATEGY.md` 的门槛：

1. **链 C 若要继续**，先做一件纯理论工作：证明或否证
   "执行动作 a 后的可行域 F_future(a) 不能被写成当前状态的势函数"。
   这一步不需要仿真，只需一个反例构造或一个不可能性论证。
   **过不了就不要立项。**
2. **链 B 的正确形态**已在仓库中（EXP-FW-V1-23）。若要扩展成决策问题，
   应表述为"用围栏延迟预算作为规划器的计算截止"，而不是"研究何时来不及"。
3. **链 A 若要继续**，卖点必须是"U\* 对任务压力的非单调回折"，且必须正面比较
   Haasnoot 2013 的 transfer point。
4. **链 D 若要继续**，卖点必须是"VOC 对可恢复裕度非单调单峰"，
   且必须正面比较 Shperberg 2019 与 Navrati 2023。
5. 在读完全文之前，**按项目规范，不得声称任何新颖性**。

---

## 8. Limitation

- 全部结论基于题录与摘要，**未读正文**。因此本文件只能给出否定性判定。
- 未覆盖 IEEE Xplore 全文与中文库。
- 第 3.3 节的"术语空缺"证据有两种解释，本文件不能区分。
- 第 2/3/4 节中关于"会被审稿人如何判定"的推论是判断，不是检索结果。
- 检索失败清单：Scopus 的 `OR` 组合在部分查询中匹配过松；
  arXiv 的多词 AND 在本环境返回 0；Semantic Scholar 全程因 429 未使用。
