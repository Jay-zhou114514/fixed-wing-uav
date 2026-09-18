# 文献地图 v0.1

日期：2026-09-16
状态：初版。**本文件的作用是记录"哪些方向已被占据"，不是为某个方向找支持。**

## 0. 检索规模与方法

| 项目 | 内容 |
| --- | --- |
| 数据库 | Scopus（API）、OpenAlex、Crossref、arXiv |
| 检索次数 | Scopus 约 50 组、OpenAlex 36 组、arXiv 11 组、Crossref 6 组 |
| 语料库 | `outputs/scopus_corpus.csv`，2023 年以来的 187 条去重题录 |
| 全文阅读 | **0 篇**（这是目前最大的缺口） |
| 未覆盖 | IEEE Xplore 会议论文全文、AIAA 与 Elsevier 付费全文、CNKI 中文库 |

## 1. 语料库画像（187 条，2023–2026）

- 类型：Article 138、Conference Paper 43、Review 5、Note 1。
- 年份：2023 年 56 条、2024 年 61 条、2025 年 51 条、2026 年 19 条（检索时点）。
- 产出最多的期刊：Drones (MDPI) 20 篇、Aerospace Science and Technology 7 篇、
  AIAA SciTech 2023 6 篇、Sensors 5 篇、IEEE Access 4 篇、JGCD 4 篇、ICRA 4 篇、RA-L 3 篇。

**含义**：`Drones` 是这个子领域的"主场期刊"，也是本项目最现实的期刊扩展目标；
AAAI/AIAA/IEEE 会议层是会议论文的现实目标。

## 2. 标题词频（187 条内）

| 词 | 次数 | 词 | 次数 |
| --- | --- | --- | --- |
| wind | 42 | robust | 8 |
| reinforcement learning | 25 | dubins | 8 |
| energy | 12 | safety | 8 |
| obstacle | 10 | geofence | 6 |
| review | 6 | collision | 6 |
| experiment | 6 | safe | 5 |
| uncertain | 3 | gust | 2 |
| benchmark | 0 | open-source | 0 |
| reproducib* | 0 | dataset | 0 |
| flight test | 0 | field test | 0 |
| real-world | 0 | hardware | 0 |

**注意**：这是标题级词频，**不能**直接推出"该领域不重视验证"。
标题不提验证，正文可能做了验证。这个词频只能提出一个待检验的怀疑。

## 3. 已确立的事实（证据充分）

1. "风中的最优路径"这个经典问题已被解决。2005 提出、2009–2012 解决强风情形、
   2018 处理不确定风、2023–2024（RA-L、JGCD 2025）给出分类解与闭式解。
   - AIAA GNC 2005, "Optimal path planning in a constant wind with a bounded turning rate"（被引 137）
   - JGCD 2009, "Minimum-Time Path Planning for UAVs in Steady Uniform Winds"（162）
   - JGCD 2012, "Methods for Computing Minimum-Time Paths in Strong Winds"（48）
   - RA-L 2023, "Time-Optimal Path Planning in a Constant Wind ... Dubins Set Classification"（16）
   - JGCD 2025, "Minimum-Time Paths for Dubins Airplane in Steady Wind"（2）
2. "转弯半径与风决定安全缓冲区"这件事 2020 年就有论文。
   - JAIS 2020, "Generating Airspace Geofence Boundary Layers in Wind"（11）：
     摘要原文写明缓冲区是"最小转弯半径与持续风的函数"。
   - 该线仍在延续：JGCD 2026, "Dynamic Geofence Design for Unmanned Aircraft System Path Following in Urban Airspace"。
3. "固定翼 + 安全保证"这一措辞已被占据。
   - Control Engineering Practice 2026, "...dynamic obstacle avoidance algorithm for small fixed-wing aircraft with safety guarantees"。
4. "可认证安全规划"已经被写成综述框架，不再是一个空位。
   - Drones 2026, "A Survey of Risk-Calibrated Certifiably Safe and Resource-Aware (RCSR) Path Planning for UAVs"。
5. 城市风场下固定翼安全规划正在被用强化学习攻。
   - AST 2026（另有 SSRN 预印本）, "Safe Path Planning for Fixed-Wing UAVs in Dynamic Urban Wind Fields"。

## 4. 已被占据、因此本阶段不做的方向

| 方向 | 状态 | 依据 |
| --- | --- | --- |
| 风下 Dubins / 常值风最优路径 | 已解决，2025 年仍在推进 | 见 3.1 |
| 风下转弯几何各向异性本身 | 教科书级已知，术语为 trochoid | ICUAS 2018 等 |
| 风感知的围栏/缓冲区膨胀 | 2020 已发表，仍在延续 | 见 3.2 |
| "可认证安全规划"作为框架 | 已被综述占据 | 见 3.4 |
| 固定翼 + RL + 风场安全 | 2026 正在被做 | 见 3.5 |
| **"解析定义安全缓冲并证明其充分性"（方法层）** | **已被占据（航空冲突探测领域，定理级成果）** | 见 3.6 |
| **"固定翼不能紧急停住"作为动机** | **已被占据** | 见 3.6 |
| **围栏违规预测 + 安全机动选择的形式化验证** | **已被占据（2021，且已飞行试验）** | 见 3.6 |

## 3.6 潜力评估新增的相邻传统（2026-09-17，见 `POTENTIAL_ASSESSMENT.md`）

做潜力评估时发现两条**方法层与动机层**已被占据，必须正面处理：

| 文献 | 年 | 被引 | 占据了什么 |
| --- | --- | --- | --- |
| Herencia-Zapana et al., Formal verification of safety buffers for state-based conflict detection and resolution | 2010 | 11 | 用机械定理证明器形式化证明安全缓冲 |
| **Narkawicz et al., Formal verification of lateral and temporal safety buffers** | 2013 | 5 | 摘要原文："safety buffers are given that **guarantee mathematically** that the probability of a missed alert is zero"，"**formally proven using a mechanical theorem prover**" |
| **Kouskoulas et al., Good Fences Make Good Neighbors** | 2021 | 2 | **围栏**违规预测 + 安全机动选择的**形式化验证**算法；高阶动力学（线性变化向心加速度）；含模型参数不确定性；**已飞行试验**。且**同用"固定翼不能急停"动机** |
| Dill et al., SAFEGUARD: An assured safety net technology for UAS | 2016 | **52** | 系统级"保证安全网"（含 stay-in/stay-out 区域），V&V 导向 |
| D'Souza et al., Feasibility of varying geo-fence ... vehicle performance and wind | 2016 | **32** | 本方向源头：按性能与风算 keep-in 围栏尺寸 |

**对本项目的含义**：

1. **"验证缓冲充分性"不是新方法**——该传统在冲突探测领域已成定理级成果。
   本项目是**该方法在围栏具体构造上的应用**。
2. **"固定翼不能急停"不能作为新颖性来源**——已被多次使用。
3. **仍然未被占据的**：该特定构造（JAIS δu ⊕ δd）的**裕度方向结构**与**精确紧性**
   （检索：裕度/紧性 0 命中；方向依赖 1 命中且不相关；JAIS 13 条施引无一涉及）。
4. **同源活跃线（抢先风险）**：
   `D'Souza 2016 → JAIS 2020 (Stevens & Atkins) → {Stevens 2021, Kim 2021, Kim 2022, Abdul 2026}`
   —— 该线持续发表但 6 年内未做该构造的充分性验证。风险中等偏低，但存在。

**参考**：该方向确切交叉点（`"fixed-wing" AND geofence`）仅 **9 篇**论文；
核心论文 JAIS 2020 年均被引约 **2 次**。属冷门小众，非热点。

## 3.7 EXP-FW-V1-27A 的新颖性重叠（2026-09-18 新增，重要）

27A 判定 **H-B 成立**（逐边不蕴含同时；锐角顶点处违反 ≈0.87 R）。
但核对既有文献发现**该问题的发现层面已被占**：

**Thomas & Sarhadi (2024, *Machines*) §3.4 "Acute Internal Angles"** 原文：

> "A problem arises when the angle between two fences is acute. In this scenario, ...
> the vehicle will be driven towards the vertex of the two fences and **eventually
> penetrate the fence**. Furthermore, if the turn is initiated when s⁺ ≤ s_min, then
> the vehicle will be **unable to complete a full turn**, as the turning circle c₁
> extends out of the geozone."

即：**"标准方法在锐角顶点失效"已被明确指出**，且该文给出了对策
（检查两侧最小转弯圆与相邻围栏的距离，必要时提前转向，其 turning circle c₂）。

| 项 | Thomas 2024 §3.4 | EXP-27A |
| --- | --- | --- |
| 指出锐角顶点问题 | **是** | 是（独立复现） |
| 给出对策 | **是**（提前转向 + 检查相邻围栏） | 否 |
| 量化缺口 | 未报告违反量 | **0.87 R**（首次外摆口径） |
| "逐边 vs 同时"的形式化 | 未以该形式表述 | **是** |

**因此不可主张"首次发现锐角顶点失效"。** 可主张的收窄为：
(i) 以"**逐边 vs 同时**"形式化该缺口；
(ii) 给出**违反量 0.87 R**；
(iii) 证明 **EXP-27 的逐边判据不充分**（对本项目内部结论的修正）。

**对论文的影响**：C3（适用边界）得到实质强化，但必须在论文中
**正面引用 Thomas 2024 §3.4**，并把贡献定位在"形式化 + 量化"而非"发现"。

### 3.7.1 定位裁定：**相关工作，不作冲突**（2026-09-18，负责人决定 6）

应负责人要求做了独立复核与文献比对后，**定位如下**（V2.2 第 4 节）：

**引述方式**：

> Thomas & Sarhadi (2024) 指出锐角顶点处转弯圆放不下，并采用"对每个候选转弯方向
> 检查所有相邻围栏"的判据给出对策（§3.4）。本工作的关系为：**独立复现该机制**，
> 并**给出其穿透量的闭式表达式** `R·cos(θ/2)`（该文仅做二值判断），
> 以及**用"逐边 vs 同时"形式化该缺口**。

**为何定位为"相关工作"而非"冲突"——全文关键词核验**：

| 关键词 | 出现次数 | 含义 |
| --- | --- | --- |
| `violat*` | **0** | 无违反量 |
| `overshoot` | **0** | 无超调量 |
| `depth` / `how far` / `margin` / `buffer size` | **各 0** | 无深度/裕度/缓冲量级 |
| `penetrat*` | 9 | **全部为定性表述**（"before penetrating"、"will eventually penetrate"、"which circles have penetrated"） |

**该文未给出穿透量或死区范围的公式。**

> **⚠ 表述更正（2026-09-19，获全文后核验）**：此前本处写作"该文给出的是**二值判据**
> （相交/不相交），**未给出穿透量公式**"。**该表述过宽**：
> 该文在 §3.2 给出**直边**轨道触发距离闭式
> `s_min = r(cscθ − cotθ) = r·tan(θ/2)`（式 10）+ 瞬态项 `s_t = V·t_c`（式 12/23），
> 并在 §3.4 给出**联合检验**（两转弯圆 × 三条围栏，判据 `(i∧ii)∨iii`）。
> **准确表述**：该文对**直边**有闭式、对**顶点**仅定性；
> **未给出顶点穿透深度与死区范围**（`depth`/`overshoot`/`margin`/`buffer size` 各 0 次）。
> 详见 `LITERATURE_ANALYSIS_THOMAS2024_FULLTEXT.md`。**K8/K9 的增量不受影响。**

**因此**：

| 层面 | 判定 |
| --- | --- |
| 机制（锐角顶点失效） | 已见该文 → **不主张"首次发现"**（D16） |
| 判据形式（同时判据） | 已见该文 → **不主张"首次提出"**（D17） |
| **穿透量闭式律 `R·cos(θ/2)`** | **该文无 → 可主张为新（K8）** |
| **对本构造逐边判据的否证** | 该文针对自有 ARC 算法，未涉 JAIS δu⊕δd → **属本项目内部结论修正** |

**检索证据**：OpenAlex 全库 `geofence + acute + vertex + turn radius + penetration`
**仅命中 Thomas 2024 一篇**，该交叉点文献稀疏。

**结论**：27A 的 **K8（闭式律）+ 形式化 + 否证**可作**核心发现（C3）**，
Thomas 2024 作为**相关工作**正面引用。

## 3.8 计算几何线：圆盘填充与曲率约束路径（2026-09-18 扩检新增）

应负责人要求扩大检索（不只依赖 Thomas 2024 一篇），发现一条**此前完全漏掉**、
且**比航空文献更贴近本项目问题**的文献线。详见 `docs/LITERATURE_SEARCH_EXTENDED.md`。

| 文献 | 年 | 被引 | 与本项目的关系 |
| --- | --- | --- | --- |
| **Agarwal, Biedl, Lazard, Robbins, Suri**, *Curvature-Constrained Shortest Paths in a Convex Polygon*, SIAM J. Computing | 2002 | **79** | 凸多边形内单位曲率机器人的最优路径；最短路径至多 8 段 |
| **Ahn, Cheong, Matoušek, Vigneron**, *Reachability by Paths of Bounded Curvature in a Convex Polygon*, Comput. Geom.（arXiv:1008.4244） | 2011 | 15 | 给定起点构型的**可达区域**刻画（O(n) 复杂度）；工具 = **圆盘填充 `fil(P)`** |
| Balachandran, Narkawicz, Muñoz, Consiglio, *A Geofence Violation Prevention Mechanism for Small UAS*, NASA | 2018 | 4 | 基于**接近率约束**的围栏越界预防（作者含已引的形式化验证作者） |
| *The Complexity of the 2D Curvature-Constrained Shortest-Path Problem* | 1998 | **82** | 该问题为 NP-hard（离散化意义下）——说明是被深入研究过的经典问题 |

**关键等价（已核对 Ahn 2011 全文）**：

```text
Ahn 2011 的 "圆盘填充 fil(P)"：半径 R 的圆盘须完全落在 P 内
  ⟺  R ≤ d_e 对所有边 e（d_e 为圆心到边距离）
  ⟺  本项目 27A 的同时判据 V = min_sign max_e (R − d_e)

Ahn 2011 的 Lemma 3（Pocket lemma）：路径进入 pocket 后无法离开
  ⟺  本项目 27A 的"零余量方向"概念（可达性受限的方向）
```

**对本项目定位的影响（重要，属收窄）**：

| 项 | 原定位 | 扩检后 |
| --- | --- | --- |
| **同时判据** | 隐含视为本项目贡献 | **❌ 不新**：即计算几何的**圆盘填充可行性**，Ahn 2011 已系统使用 |
| **逐边 vs 同时的形式化** | 视为本项目贡献 | **❌ 大幅削弱** |
| **K8 闭式律 `R·cos(θ/2)`** | 可主张 | **仍未在任何文献中找到该形式**，可保留 |

**修正后的正确表述（比原表述更准且更难被驳倒）**：

> **JAIS 2020 的缓冲构造缺少圆盘填充/可达性检验**；
> 本项目指出该缺失、给出**越界量的闭式表达式** `R·cos(θ/2)`，
> 并证明其**逐边判据不充分**。
> 该检验的**方法**（圆盘填充）在计算几何中早已成熟（Ahn 等 2011）。

**新增引用义务**（论文必须包含，否则定位不成立）：
Agarwal 2002、**Ahn 2011**、Balachandran 2018、Thomas & Sarhadi 2024。

## 3.9 Kim 2022 全文核验：**四个"否"**（2026-09-19，全文已读）

**Kim, Liberko & Atkins (2022), DASC, `10.1109/DASC55683.2022.9925807`** ——
与 JAIS 2020 **同一课题组**（Atkins），其参考文献 [6] 即 JAIS 2020 本身。
全文已由负责人提供（截图，覆盖 I–VI 节 + 全部图表），
**本记录只做方法对比，不复现其模型**（负责人指示，2026-09-19）。
详见 `LITERATURE_ANALYSIS_KIM2022_FULLTEXT.md`。

**其缓冲公式（式 7）**：

```text
δ_sbx = 3σx + f_l/2                        纵向
δ_sby = 3σy + ε_guidance_y + b/2            横向
δ_sbz = 3σz + ε_guidance_z + h/2            垂向
δ_sb  = max[δ_sby, δ_sbz]                   截面取最大（⟹ 各向同性）
```

**四个悬置问题的答案（全部为"否"）**：

| # | 问题 | 答案 | 依据 |
| --- | --- | --- | --- |
| 1 | 解析还是统计？ | **统计**（3σ = 99.7%） | 式 7 用 3σ；原文 "achieving 99.7% confidence" |
| 2 | 是否处理多边形顶点？ | **否** | 式 7 只含 σ/制导误差/机体尺寸；无内角分析 |
| 3 | 转弯缓冲是否方向依赖？ | **否**（水平面内各向同性） | `max[δsby,δsbz]` 取单一值 + "cross-section ... square" |
| 4 | 是否含接管延迟？ | **否** | 式 7 无延迟项 |
| 5 | "转弯飞行"如何体现？ | **仅通过 σ 的数值** | 无转弯专用几何项 |

**由此得到的三条判读**：

1. **无直接竞争**：本项目 K1/K2/K8/K9/H2/H3 **全部不受该文覆盖**；
2. **K6/D1 表述由全文支持**：该文只做**尺寸设计**，不做**裕度刻画**；
3. **D18 理由加强**：其"含转弯飞行"仅指 σ 内含转弯影响，**不等于**构造了转弯缓冲几何。

**新增不可主张 D19**：**不得**声称"既有围栏缓冲忽略方向依赖/假设各向同性"——
JAIS 2020 自身即用**方向性** δd；Kim 的各向同性是其**问题设定**（包裹单条已知航迹）
使然，且取 max 属**保守**选择。两者是**不同设计哲学**，**不作优劣判断**。

**抢先风险**：由"中等偏低"→ **中等**（该课题组持续产出 + 其未来工作直言要建
"不同城市模型/风况的缓冲尺寸数据库"）。**缓解**：卖点固定在
**解析闭式 + 顶点/延迟**（该课题组不做）。

**该文未使用的工具**：其引用 de Berg《Computational Geometry》
**仅用于 visibility graph 路径规划**，**未使用圆盘填充/顶点可行性分析** ——
即 §3.8 那条计算几何线**仍是本项目独有的工具来源**。

## 5. 观察到的异常（标注置信度）

| # | 观察 | 置信度 | 说明 |
| --- | --- | --- | --- |
| O1 | 方法层高度集中在强化学习：187 条里 25 条标题含 RL，Dubins 只有 8 条 | 中高 | 词频直接可见 |
| O2 | 标题层几乎没有基准、可复现、数据集、开源、真机试验的痕迹 | **低** | 已验证：换成基准/可复现类检索式，Scopus 返回 657 / 591 条，但这些数字被其他领域严重污染。**Scopus 的 TITLE-ABS-KEY 匹配过松，绝对计数不可信。** 该观察必须靠读正文验证 |
| O3 | 2026 年新论文大量为 0 引用，领域移动极快 | 高 | 检索结果直接可见 |
| O4 | "风 + RL + 真机验证"的交叉只有 15 条（全部年份） | 中低 | 同样受匹配过松影响 |

## 6. 候选问题（全部待验证，不得直接立项）

| 候选 | 形态 | 需要先确认什么 |
| --- | --- | --- |
| P1 复现驱动的严谨性检验 | 取 2–3 篇 2024–2026 代表性 RL / 学习类风感知规划工作，在统一协议下复现，检验随机种子敏感性、统计功效与结论稳健性；能复现则给出可复现基准，不能复现则给出失效机制 | 必须先读正文确认这些论文是否真的缺少种子报告与统计检验；大概率会有 1–2 篇做得很扎实 |
| P2 有保证的膨胀界 | 地面扫掠集的闭式包络，并证明"按最大局部曲率半径膨胀"不足 | 已被 JAIS 2020 抢先一步；需要读全文确认其界的形式与紧性，才有判断 |

## 7. 必须读全文的清单（按优先级）

1. ~~`10.2514/1.i010792` — Generating Airspace Geofence Boundary Layers in Wind~~ **已读完**（NSF 公共访问库版本，本地 `refs/nsf_10165605.pdf`）。结论：缓冲数值被推导，但充分性未被验证。精读笔记见 `refs/NOTES_JAIS2020.md`
2. `10.3390/drones10050351` — RCSR 综述（决定整个框架是否还有空位）
3. `10.2514/1.g008932` — Minimum-Time Paths for Dubins Airplane in Steady Wind（决定"最优路径"线的边界）
4. `10.1016/j.ast.2026.112920` — Safe Path Planning for Fixed-Wing UAVs in Dynamic Urban Wind Fields（决定 RL 路线的现状）
5. `arXiv:2306.11845` — RA-L 2023 Dubins Set Classification（有公开预印本，可直接开工）

## 8. 下一步

1. 读上面第 1、2、5 三篇全文（第 5 篇有公开版本，可以立刻开始）。
2. 拿到 IEEE Xplore 与学校图书馆权限，补齐会议论文与付费全文。
3. 读完之后，把第 5 节里置信度低的观察升级为"已确认"或"已否决"，
   再决定 P1 / P2 是否立项。
4. 在读完之前，**不得**声称任何新颖性。

## 9. 方法学备注

本文件的第一版是基于检索量与题录写的，不是基于全文。按 `research-stack-router`
的 Phase B 门槛，这种证据只允许得出"某方向已被占据"这类否定性结论，
不允许得出"某方向还有空间"这类肯定性结论。第 5 节与第 6 节中的肯定性表述
全部标为待验证。


## 10. 全文阅读后的更新（2026-09-16）

已读第一篇：Stevens & Atkins (2020), JAIS, `10.2514/1.i010792`。

- **它做了什么**：给出固定翼围栏缓冲的解析式——均匀缓冲 δu = Va/ω（转弯半径），
  方向缓冲 δd = (Va/ω)√(1−w²) + (Vw/ω)·arccos(−w)，方向取风向。
- **它的实验验证了什么**：3×10⁶ 个随机多边形的**分层生成成功率**（几何可行性）。
- **它没有验证什么**：按这些缓冲值生成的分层是否真的能阻止一架固定翼在有风下越界。
  缓冲区数值的**充分性缺乏实验支持**。
- **对主线的意义**：P1（审计）拿到第一个具体且可引证的对象；
  P2（膨胀界）从"已被抢先"变为"可能是对方未完成的那一步"。

**边界**：第 III 节尚未逐行读，上述结论在读完第 III 节前仍标为待确认。


## 11. 第 III 节核对后（2026-09-17）

第 III.B 节已读。论文的缩放构造为：每条边沿自身外法线外移 δu，且当外法线与风向
同向分量为正时再沿风向平移 δd，顶点取相邻平移直线的交点。

这意味着在方向 n 上的缓冲为：

- n 等于某条边外法线时：δu + δd·max(0, cos∠(n, φd))，与 EXP-FW-V1-20 的模型一致；
- n 位于两条边法线之间时：**大于**上式。

因此 EXP-FW-V1-20 的模型是实际构造的**下界**。该实验的正缺口结论
**只在围栏存在一条外法线沿风向的边时成立**（矩形围栏即属此类）。
对边法线明显偏离风轴的围栏，多边形近似的额外余量可能覆盖缺口。

这是一条可检验的预言，已登记为 EXP-FW-V1-21 的核心假设。

### 11.1 EXP-FW-V1-27 的检验结果（2026-09-17 补充）

上述预言已由 `EXP-FW-V1-27` 在 125 个凸多边形构型、3 个风速比上检验。结论：

**前半部分成立，后半部分需修正。**

- ✅ "n 位于两条边法线之间时缓冲**大于**法向值" —— 成立（P1 通过，
  偏差在浮点极限 7e-14 m）。构造对顶点给出额外裕度 `h = δu/sin(θ_int/2) ≥ δu`，
  顶角越尖裕度越大。
- ⚠️ "**最坏情况**是风向与边法向一致；简单几何结构" —— **需修正**：
  最坏情形由"**是否存在一条法线恰 ⊥ 风向的边**"决定，**与形状复杂度无关**。
  实测三个 w 下的全局最小 margin 均由**正六边形 α = 0°**取得（方向 −90.0°），
  而非对齐矩形；两者 margin 都等于 0。

### 11.2 由 EXP-FW-V1-27 得到的结构（等级 A）

```text
margin(n) = given(n) − required(n)

margin(0°)  = δu            （沿风向，与 w 无关）—— 与 EXP-FW-V1-22 互证
margin(90°) = 0             （垂直风向，精确紧）
```

即该构造在最坏方向上**零冗余**：`required(90°) = given(90°) = δu = R`。

**候选解释（等级 C，未检验）**：若 `margin(90°) = 0` 是设计上的精确紧，
则**任何未建模效应**（延迟、风估计误差、跟踪误差、滚转瞬态）都会直接产生缺口，
因为没有余量可消耗。这正是 EXP-FW-V1-26（闭环）的动机。

**未覆盖**：凹多边形与顶点展平（该展平为回收面积而做，可能**减少**缓冲）。
登记为 **EXP-FW-V1-27B**，是最可能找到真实缺口之处。
