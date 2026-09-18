# Literature Audit V2：缓冲充分性缺口是否成立

- 日期：2026-09-17
- 对象：**README 的核心主张** ——
  "JAIS 2020 给出了缓冲数值，但从未验证这些数值是否足以防止飞机在有风条件下越界"
- 性质：**本文件的唯一目的是判定这个立项理由是否成立**。不产生新方向。
- 阅读深度：**2 篇全文**（JAIS 2020 原文，12 页；Thomas 2024，27 页）+ 约 15 篇摘要 + 施引列表
- 依据规范：`docs/CONVENTIONS.md` 第 5 节；本文件结论最高为 **B**

---

## 0. 结论摘要（先给判定）

| 主张 | 判定 |
| --- | --- |
| **"JAIS 2020 的缓冲构造，其充分性从未被验证"** | **✅ 已确认成立**（已读该文全文，含此前未读的第 III 节） |
| "缓冲数值从未被验证充分性"（一般化表述） | ❌ 不成立。Thomas 2024 做过延迟与缓冲的闭环验证；Kim 2022 摘要自称统计保证 |
| "延迟预算"这个概念是新的 | ❌ 不成立。Thomas 2024 §4.3 已发表起步转弯的 rise-time 延迟距离 `s_t` |
| 缺口能否支撑项目 | ✅ 能，**但重心应从"审计他作"移到"给出新量"**。见第 5 节 |

**一句话**：立项理由**保住了，而且是干净的**——但保住的只是"这个构造"层面；
项目的价值重心应放在 `τL*` 的精确刻画与任务层后果上，而不是"我们发现别人没验证"。

---

## 1. JAIS 2020 第 III 节已读：缺口确认成立（本节为新增的确定性证据）

**已读原文**：`refs/nsf_10165605.pdf`（NSF 公共访问库版本，12 页，合法公开）。
此前该文第 III 节未读，是立项理由唯一的悬空点。**现已读完，结论明确。**

### 1.1 第 III 节做的是什么

第 III 节标题为 "Geofence Layer Generation"，由四小节构成，**全部是几何构造**：

| 小节 | 内容 |
| --- | --- |
| III.A Boundary Smoothing | 按边长与顶点角判断，移除会导致非法层的顶点 |
| III.B Scaled Layer Generation | 各边沿法线平移，顶点落在相邻平移边的交点；对角 > π 的顶点做"展平" |
| III.C Cross-Check | 检查缩放层是否为闭合简单多边形，且**距原始围栏**满足 δu/δd |
| III.D Smoothing Selection | 在多个平滑方案中选可用面积最大者 |

### 1.2 关键：Cross-Check 验证的是什么（原文引用）

> "Once formed, each closed polygon q is compared to the original geofence o to check that
> the uniform buffer δu and the direction buffer δd at angle ϕd are not violated.
> ... The cross-check returns only those polygons that are at least the minimum required
> buffer distances **from the original geofence**."（III.C）

**这是一个几何自洽性检查**：验证"我构造出的多边形，与我给出的缓冲距离定义一致"。
它**没有**验证"这个缓冲距离是否足以覆盖飞机在有风条件下的真实可达集"。

### 1.3 全文关键词核查（决定性）

对 JAIS 2020 全文（56,285 字符）做朴素关键词计数：

| 关键词 | 出现次数 | 含义 |
| --- | --- | --- |
| `guarantee` | **0** | 全文没有任何"保证"式主张 |
| `proof` | **0** | 无证明 |
| `uncertainty` | **0** | 未处理不确定性 |
| `wind estimat` | **0** | 未处理风估计误差 |
| `delay` | **0** | **未处理延迟** |
| `response time` | **0** | 同上 |
| `contain` | 6 | 全部指"空域/面积包含"，**无一指可达集包含** |
| `sufficien` | 4 | 见下，均非可达性充分性 |
| `reachab` | 3 | 2 处指"可达飞行体积"（描述平滑的保守性），1 处是引用 Coombes 的迫降可达性论文 |

`sufficien` 的 4 处逐一核对：

1. 引言中的**动机性断言**（非结果）：
   > "buffer distance values are calculated to provide sufficient time and space for the UAS
   > to avoid violating the original geofence boundaries."
2. 引用 Ref [15] D'Souza，说明 **15 m / 5 m 水平垂直偏差**对**多旋翼**足够——
   即缓冲尺寸的验证依据来自**他人**，且是**多旋翼**。
3. "The cross-check algorithm presented here is sufficient but not unique."
   —— 说的是**算法**充分，不是缓冲充分。
4. "geofences with insufficient size" —— 指多边形太小放不下缓冲。

### 1.4 该文自己承认抽象掉了机型

> "Without loss of generality, layering case studies presented in this paper abstract away
> from a specific UAS type by presenting results over a series of geofence..."

即第 III/IV 节的分层研究**刻意不绑定机型**。

### 1.5 第 IV 节的验证指标（原文引用）

> "The first metric of success considered is the **percentage of cases for which at least
> one smoothing setup resulted in a valid scaled layer**."（第 IV 节）

这是**几何可行性**指标（算法能否产出合法多边形），不是安全性指标。

### 1.6 判定

**立项理由成立，且比我预期的更干净：**

- 该文（a）推导了 δu、δd；（b）构造了合法缩放层；（c）验证了层与**原始围栏**的几何距离；
- 该文**没有**（a）证明 δu ⊕ δd 包含有风固定翼的真实可达集；
  （b）使用 "guarantee" 一词；（c）处理风估计误差；（d）处理任何延迟。
- 其 δd 的定义原文为"account for **steady wind**"，即**常值风**。

**因此"该构造的缓冲充分性此前未被验证"这一表述，可以安全写入申报书。**

---

## 2. 最重要的发现：Thomas 2024 已发表"延迟预算"概念

**Thomas, P. & Sarhadi, P. (2024). Geofencing Motion Planning for Unmanned Aerial Vehicles
Using an Anticipatory Range Control Algorithm. *Machines*, 12(1), 36.**
DOI `10.3390/machines12010036` · 被引 9 · **CC-BY，已读全文（27 页）**

### 2.1 它做了什么（摘要级）

提出 ARC（anticipatory range control）算法，用**转弯圆相交测试**预判围栏边界，
使飞机在穿透前转弯，适用于一般地缘形状、凹多边形、锐角顶点、极区/子午线。

### 2.2 关键：它定义了一个与 τL\* 概念同源的量

式 (12)：

```text
s_min = G·V²·(cscθ − cotθ) + s_t
```

> "with s_t being an additional term to cover the distance required for the transient
> behavior on initiating a turn (**i.e., the rise time delay**)."
> "The transience will be dictated by the maneuverability of the specific vehicle and the
> heading flight controller and so **must be tailored for each vehicle**."（§3.2）

`s_t` 的取值（§4.3）：由一阶滚转响应 `τ = 0.8 s` 得

```text
t_c = −τ·ln(1 − φ/φ_max)  |_(φ=0.99φ_max)  = 3.7 s,     s_t = V·t_c
```

并且 §4.3 明确写道：

> "**Increasing s_t (through increasing t_c) provides more secure flight** around the fence,
> creating a larger buffer zone around the zone edge. The disadvantage to the pilot is a
> reduced working field... **a convenient way of adding robustness to the system.**"

### 2.3 这对本项目意味着什么

| 对比 | Thomas 2024 的 `s_t` | 本项目的 `τL*` |
| --- | --- | --- |
| 概念 | 起步转弯的 rise-time 延迟距离 | 接管延迟预算 |
| 是否含**风** | **否**（见 1.4） | **是**（含 w） |
| 是否**精确** | 否，经验调参（"tailored for each vehicle"） | 是，闭式解，45 点网格偏差 0.000 |
| 与空速关系 | `s_t = V·t_c`，**正比于 V** | **与 Va 无关**（反直觉） |
| 用途 | 保守性调参旋钮（"adding robustness"） | 精确失效边界 |

**判定**：**"提出延迟预算"不能再作为创新点**。Thomas 2024 已公开该概念，
且它是本项目必须正面引用并说明差异的最近邻工作。

**但同时**：`s_t` 是**经验调参**、**不含风**、**正比于 V**，与本项目的
"精确、含风、与空速无关"三者全不相同。所以 τL\* 本身仍然独立成立。

### 2.4 Thomas 2024 明确把风留为开放问题（这是本项目的机会）

§5.2 "Uncertainty Handling" 原文：

> "The presence of wind and turbulence **would be expected to deteriorate the performance**
> of the algorithm, but two aspects would **support limiting** this effect."
> "Secondly, the timing parameter `t_c` can also be increased to improve the buffer zone...
> This amounts to adding an additional safety, or 'slack' param[eter]"

即 Thomas 2024 对风的处理是：用**地速**代替空速 + **手动加大 `t_c`**，
并称要做稳健处理还需"additional modeling of the aircraft dynamics、
additional measurements of wind speeds、more predictive control"。

**它自己承认风未被解决。** 它把 JAIS 2020 [23] 归为"另一条风下缩放软边界的路线"，
**并未验证那条路线的充分性**。

---

## 3. 最大的未决威胁：Kim 2022

**Kim, J., Liberko, N., et al. (2022). Airspace Geofencing Volume Sizing with an
Advanced Air Mobility Vehicle Performance Model. *DASC*.**
DOI `10.1109/DASC55683.2022.9925807` · 被引 5 · **全文未获取（IEEE 付费）**

摘要原文（已核验）：

> "Airspace safety buffer sizes can be **determined and verified** by modeling vehicle
> dynamics as well as quantifying guidance, navigation and control uncertainties.
> This paper proposes a methodology to **design safety buffer sizes** given specific vehicle
> and sensor properties **and wind**. These parameters are then translated to geofence safety
> buffer dimensions for straight and turning flight to **statistically guarantee** an aircraft
> will stay inside its flight trajectory based keep-in geofence."

**为什么这是最大威胁**：它的措辞几乎正面覆盖了本项目的立项理由——
"含风的缓冲尺寸设计"+"统计保证"+"直线与转弯飞行"。

**为什么还不能判定它杀死了缺口**（三条保留）：

1. **未读全文**，无法确认它的"guarantee"是解析包含性证明，还是 Monte Carlo 统计；
2. 它是 **DASC 会议论文（5 次引用）**，非期刊，方法与结论强度未核；
3. 关键未知：它是否处理**接管延迟/响应延迟**？若否，则 τL\* 这条线仍独立。

**行动**：这是本审计的**唯一必读项**。在读到它之前，
**不得**在申报书中写"缓冲充分性从未被验证"。

---

## 4. 其余相关工作的定位（按威胁度排序）

### 4.1 同一作者线的延续（未闭合缺口）

| 文献 | 年 | 出处 | 被引 | 它与缺口的关系 |
| --- | --- | --- | --- | --- |
| Stevens & Atkins, Layered geofences in complex airspace environments | 2018 | AIAA AVIATION | 15 | 提出按"性能约束与环境条件（含风）"缩放边界；**给出方法，未验证充分性** |
| Stevens & Atkins, Generating airspace geofence boundary layers in wind | 2020 | JAIS | 13 | **本项目的研究对象** |
| Stevens & Atkins, Mission Implementation of a Geofence System for UAS | 2021 | AIAA AVIATION | 2 | 系统实现，非验证 |
| Kim, Mathur, et al., Operational Volumization and Inverse Volumization | 2021 | AIAA AVIATION | 8 | **有 Monte Carlo 统计验证**，但验证对象是"分层算法的冲突自由性"，非风下充分性 |

**读法**：该线持续在做"方法"，验证工作集中在**几何/算法可行性**层面。
**没有一篇验证 JAIS 的风下缓冲数值本身是否足够。**

### 4.2 其他围栏安全线（机制不同，不构成直接竞争）

| 文献 | 年 | 被引 | 机制 | 为何不构成竞争 |
| --- | --- | --- | --- | --- |
| Yoon & Lee, Predictive Runtime Monitoring... Geofence Enforcement for UAVs | 2019 | 21 | LTI 随机系统的控制包络集 | 线性系统，非固定翼转弯几何 |
| Zhang et al., MPC based dynamic geofence system | 2017 | 16 | MPC 软/硬围栏 | 控制层，非缓冲尺寸充分性 |
| Abdul et al., Dynamic Geofence Design... Urban Airspace | 2026 | 1 | APF + Lyapunov 稳定性算最小围栏尺寸 | 机制为势场包含，非缓冲缩放 |
| Seiferth et al., Fully-automatic geofencing module / Evasive maneuvers | 2019/2020 | 9 / 4 | 自动围栏模块、规避机动 | 3D 机动策略，非缓冲充分性 |
| D'Souza et al., Feasibility of varying geo-fence... vehicle performance and wind | 2016 | **32** | 按性能与风变化围栏 | **标题直指本项目交叉**，摘要未取，**需补看** |
| Arora & Deswal, Geofence-Based Boundary Violation Detection | 2024 | 3 | 越界检测算法（凸包） | 检测，非缓冲 |

### 4.3 施引全景

JAIS 2020 共 **13 次引用**（OpenAlex）/ **11 条**（Semantic Scholar）。
本子领域**引用密度低**，说明它不是一个被大量跟进的热点——
这对项目是**双面**信号：被抢先风险低，但"读者关心度"也低。

### 4.4 一个弱正面证据（须按弱证据读）

Scopus 四词联合查询：

```text
TITLE-ABS-KEY(wind AND geofence AND (delay OR "reaction" OR "rise time" OR "budget"))
→ total: 0
```

**为什么这是弱证据**：四词 AND 本身过严；且 Thomas 2024 明显触及该交叉却未被命中
（因其摘要用 "rise time" 但未与 wind/geofence 在题录层共现）。
**不能据此声称"无人做过"**，只能说"未作为命名主题出现"。

---

## 5. 对本项目的判定与修正后的表述

### 5.1 缺口的三层拆分

原主张"充分性从未被验证"太粗。拆开看：

| 层 | 是否已被占 | 依据 |
| --- | --- | --- |
| **该构造的充分性未被自身检验** | **✅ 未被占** | 第 1 节：JAIS 2020 全文 0 次 `guarantee`，0 次 `delay`，第 IV 节指标为几何可行性 |
| **概念**：起步转弯需要预留延迟距离 | **❌ 已被占**（2024） | Thomas 2024 式 (12) + §4.3 |
| **一般化方法**：含风的缓冲尺寸设计并统计保证 | **⚠️ 疑似被占** | Kim 2022 摘要声称；**全文未获取** |
| **交叉**：风 × **精确闭式** × **该构造** × 空速无关性 | **未发现被占** | 第 2.3 节对比表；第 4.4 节的 0 命中（弱证据） |

### 5.2 修正后的立项理由

因第 1 节已确认 JAIS 2020 自身的缺口，原表述可以保留**但要限定范围**：

**可以写（有全文级证据）**：

> JAIS 2020 给出了缓冲数值（δu、δd）与分层构造算法，并验证了缩放层与原始围栏的
> 几何距离；但该文全文未出现 "guarantee"，未处理风估计误差，未处理任何延迟，
> 其第 IV 节的验证指标是"能否生成合法分层"（几何可行性），而非"缓冲是否足以
> 覆盖有风条件下的真实可达集"。该文亦明确"abstract away from a specific UAS type"。

**必须同时写（否则会被 Thomas 2024 反驳）**：

> 起步转弯的延迟距离概念并非本项目首次提出：Thomas & Sarhadi (2024) 已给出经验形式
> `s_t = V·t_c`（`t_c` 由滚转响应 rise time 确定），并将其作为保守性调参旋钮。
> 差异在于：该处理是经验标定（"must be tailored for each vehicle"）、不含风、
> 且正比于空速；而本构造下由常值风引起的临界延迟是精确闭式、含风、与空速无关。

### 5.3 创新点的最终收窄

**可主张**：

1. 给出该缓冲构造在常值风下的**精确接管延迟预算闭式解** `τL* = 1/(ω(1+w))`，
   并揭示其**与空速无关**的反直觉性质（EXP-FW-V1-23，等级 A）；
2. 给出该构造沿风向**余量恒等于 δu** 的结构性事实（EXP-FW-V1-22）；
3. 指出该构造的充分性**在其自身文献中未被检验**（已由全文关键词核查支持）；
4. 给出该预算的**任务层后果**与**适用边界**（待 EXP-FW-V1-26/27/28）。

**不可主张**：

- ~~首次提出延迟/响应预算概念~~ → Thomas 2024 §4.3 已发表；
- ~~首次研究风下围栏~~ → JAIS 2018/2020 已占；
- ~~首次研究风下 Dubins 最优路径~~ → `LITERATURE_MAP.md` 第 3.1 节链条已解决；
- ~~证明 JAIS 2020 有误~~ → 该文未声称充分性，其缺口是"未做"而非"做错"。

**关于 Kim 2022 的处理**：其摘要声称含风设计并统计保证，但**全文未读**。
在读到之前，第 4 条的表述**不得**写成"此前无人验证风下缓冲"，
只能写成"未在该构造下被验证"。

---

## 6. 待完成的核验清单（按优先级）

| # | 项 | 为什么关键 | 状态 |
| --- | --- | --- | --- |
| 1 | **Kim 2022 DASC 全文** | 唯一可能直接杀死立项理由的工作 | 未获取（IEEE 付费，需机构权限） |
| 2 | **JAIS 2020 第 III 节** | 确认缺口是否已被该文自身处理 | 未读（本地仅有精读笔记） |
| 3 | D'Souza 2016 摘要/全文 | 标题直指"vehicle performance and wind" | 仅题录 |
| 4 | Seiferth 2020 摘要 | 规避机动是否已含风下缓冲 | 仅题录 |
| 5 | JAIS 2020 的 13 条施引逐篇读摘要 | 防止遗漏 | 已列全，未逐篇读 |

**纪律**：第 1、2 项完成前，**不得**把本项目的缺口表述写入申报书。

---

## 7. Observation / Interpretation / Limitation

### Observation（观察到什么）

1. Thomas 2024（已读全文）在第 4.3 节定义了起步转弯的 rise-time 延迟距离 `s_t = V·t_c`，
   并将其作为保守性调参旋钮。
2. Thomas 2024 第 5.2 节明确将风列为未解决项，处理方式是地速 + 手动增大 `t_c`。
3. Kim 2022 摘要自称可"含风设计缓冲尺寸并统计保证"遏制，全文未获取。
4. JAIS 2020 共 13 次引用；施引中未见对其缓冲数值充分性的验证工作。
5. 四词联合查询（wind × geofence × delay 类）返回 0 条。

### Interpretation（可能意味着什么 —— 未确立）

- 概念层已被占，但"精确 + 含风 + 该构造"的交叉可能仍开放；
- Kim 2022 的威胁性质取决于其"guarantee"是解析还是统计，**本审计无法判定**。

### Limitation（不能证明什么）

1. **不能**证明缺口成立——Kim 2022 全文未读，第 1、2 项未完成。
2. **不能**证明"无人做过该交叉"——0 命中是过严查询的结果，非穷尽检索。
3. 本审计只读了 **1 篇全文**；其余为摘要级。
4. 未覆盖 IEEE Xplore 全文层、AIAA 付费全文、中文库。
5. 对 Thomas 2024 的"同源"判断基于概念与公式形式，非作者自述。

---

## 8. Phase B 门禁自检（按 `research-stack-router`，2026-09-17 补）

`docs/LITERATURE_MAP.md` 第 109 行已引用 `research-stack-router` 的 Phase B 门槛，
但该技能此前未安装。现已安装（`~/.zcode/skills/research-stack-router`），
按其实质条款对本审计做自检：

### 8.1 Phase B Gate 逐条

| 门禁条款 | 本审计的符合情况 |
| --- | --- |
| "Separate established evidence, interpretation, and open questions" | ✅ 第 7 节三层分列；第 5.2 节区分"可写/必须同时写" |
| "Do not claim novelty from a small or unverified search" | ✅ 第 5.3 节全部为"不可主张"清单；第 3 节明确 Kim 2022 未读 |

### 8.2 §6 Universal evidence rule 逐条

| 禁止项 | 本审计 |
| --- | --- |
| 未读论文却称 "paper reports" | ✅ JAIS 2020 与 Thomas 2024 均为**全文**；其余标注为摘要级 |
| 无文献基础却称 "novel" | ✅ 未作任何新颖性主张 |
| 只有仿真却称 "validated" | ✅ 第 7 节 Limitation 已列明 |

### 8.3 尚缺的证据（Phase B 未通过）

**Phase B 门禁当前状态：未通过。** 唯一阻塞项：

> **Kim et al. 2022（`10.1109/DASC55683.2022.9925807`）全文未获取**
> （Unpaywall 确认 `is_oa: false`，IEEE 付费）。

在读到它之前，本项目的"缺口"陈述只能限定为
"**未在该构造下被验证**"，不得扩展为"风下缓冲充分性无人验证"。

### 8.4 research-state 七件套与本仓库的映射

`research-state` 要求维护 7 个工件。本仓库已有对应物，映射如下：

| research-state 要求 | 本仓库对应 | 状态 |
| --- | --- | --- |
| `PLAN.md` | `docs/plans/RESEARCH_PLAN_v1.x.md` | ✅ |
| `LITERATURE.md` | `docs/LITERATURE_MAP.md` + `docs/LITERATURE_AUDIT*.md` | ✅ |
| `EXPERIMENTS.md` | `experiments/README.md`（注册表） | ✅ |
| `RESULTS.md` | `experiments/EXP-FW-V1-*.md` + `outputs/*.csv` | ✅ |
| `DECISIONS.md` | `docs/DECISIONS.md`（FW-D-00X） | ✅ |
| `LIMITATIONS.md` | 分散在各计划与实验记录的 Limitation 节 | 🔶 建议汇总为单文件 |
| `PROVENANCE.md` | `docs/CONVENTIONS.md` 第 12 节数值互验要求 | 🔶 建议独立成文件 |

**建议（非指令）**：`LIMITATIONS.md` 与 `PROVENANCE.md` 目前分散，
按 `research-state` 的要求聚合成单文件会提升交接可靠性。

---

## 9. 对项目定位的影响（回答你的问题）

**"优秀大创"还是"有论文潜力的大创"？**

本审计的答案：**仍是"有论文潜力"，但潜力点在移动。**

- 原潜力点（"验证别人没验证的充分性"）**受 Kim 2022 威胁**，且属于"审计他作"型贡献，
  论文层级偏低。
- 移动后的潜力点（"精确延迟法则 + 风 + 空速无关性 + 任务层后果"）
  **更接近 EXP-FW-V1-23 那种研究级产出**，且与 Thomas 2024 有清晰的差异化。

**这个移动是好事**：从"指出别人没做"变为"给出一个新量"。
但它要求 EXP-FW-V1-26 必须做（否则 τL\* 停在几何层）。

**下一步唯一动作**：拿到 Kim 2022 与 JAIS 第 III 节。
两者在拿到之前，本项目**不具备**写申报书"研究缺口"段的资格。
