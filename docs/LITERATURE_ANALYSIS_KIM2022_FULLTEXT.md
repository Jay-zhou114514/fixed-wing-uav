# Kim 2022 全文分析（已获取：负责人提供页面截图，覆盖全部正文）

- 日期：2026-09-19（V2 更新：补入第 V、VI 节与 Table III–V）
- 对象：**Kim, J., Liberko, N., Atkins, E. (2022).** *Airspace Geofencing Volume Sizing with an
  Advanced Air Mobility Vehicle Performance Model.* IEEE/AIAA 41st DASC.
  DOI `10.1109/DASC55683.2022.9925807`
- 获取方式：**负责人提供论文页面截图**（第三方渠道均不可用，见第 1 节）
- 覆盖范围：**正文 I–VI 节全部 + Fig 1–16 + Table I–V + 参考文献表**
- 状态：**已读全文**；式 7 已与 Table IV/V **数值交叉核对通过**
  （脚本 `notes/verify_kim2022_eq7.py`）

---

## 1. 获取过程（记录）

| 渠道 | 结果 |
| --- | --- |
| ResearchGate（负责人提供链接） | **403**（IP 级拦截，"unusual activity"） |
| Deep Blue（密歇根机构库） | **403 + 政策封锁**：美国司法部法规禁止"关注国家"访问 |
| Unpaywall / OpenAlex / Semantic Scholar | 均确认 **closed access** |
| IEEE Xplore | **202**（人机验证） |
| arXiv / NASA NTRS / CORE / OpenAIRE | 无预印本、无技术报告 |
| **负责人提供页面截图** | ✅ **成功（本次覆盖全部正文）** |

**附带发现（对后续检索有用）**：**MDPI 全文可用浏览器读取**（curl 被 403，真实浏览器通过）。
该课题组姊妹篇 Kim & Atkins (2022, *Applied Sciences*, `10.3390/app12020576`) 已借此获取；
其为**围栏体积化 + 路径规划**，`uncertainty`/`verify`/`latency`/`margin`/`acute`/`corner`
各 **0 命中**，**与缓冲尺寸问题无关**，不构成竞争。

## 2. 他们的方法（式 1–7，逐项核录）

### 2.1 系统架构（Fig 1）

```text
Flight Planning ← OSM（地图）
Guidance → r(t) ─(+)→ e(t) → Control → u(t) → Plant → 输出
                 (-)↑ x̂(t)                       ↑ w(t)（过程噪声）
            Navigation ← Sensors（v(t) 传感器噪声）
                                  ↑ T(t)（CFD 风场）
```

`r(t)` 参考状态、`x̂(t)` 估计状态、`e(t)` 误差、`T(t)` 风矢量。
目标：**用真实传感器与风的不确定性，统计刻画导航与轨迹跟踪误差**。

### 2.2 动力学模型（式 1–6）

**完整 6 自由度刚体**：位置 `[pn, pe, pd]`（NED 惯性系）、地速 `[u,v,w]`（机体系）、
姿态 `[φ,θ,ψ]`、角速率 `[p,q,r]`、力 `[fx,fy,fz]`、力矩 `[l,m,n]`、转动惯量 `J`；
系数 `Γ1…Γ8`（式 6a–6d）。
**气动**：非线性升力/阻力，**含失速**（Fig 3 明确 "Stall performance reduction is captured"）；
纵向/横向力矩用线性模型；**舵机饱和限制已施加**。

### 2.3 控制与导航

- **PID**：纵向与横向解耦；内环姿态 → 外环高度/航向/空速。
- **EKF**（Fig 5）：陀螺/静压/动压 **0.01 s**；**GPS 1 s**。
  位置不确定性来自：导航误差 + 控制扰动 + 环境风。
- 位置标准差 `σx, σy, σz` 由 EKF 协方差对角元的平方根取得
  （原文："taking square of variances `[cov(x,x), cov(y,y), cov(z,z)]` from EKF"）。

### 2.4 **缓冲尺寸公式（式 7a–7d）——本文核心**

```text
δ_sbx = 3σx + (1/2)·f_l                             （7a，纵向）
δ_sby = 3σy + ε_guidance_y + (1/2)·b                 （7b，横向）
δ_sbz = 3σz + ε_guidance_z + (1/2)·h                 （7c，垂向）
δ_sb  = max[ δ_sby , δ_sbz ]                         （7d，截面取最大）
```

| 符号 | 含义 |
| --- | --- |
| `[σx, σy, σz]` | 全程路径上机体系三轴位置的**最大标准差**（来自 EKF 协方差） |
| `3σ` | **99.7% 置信**（原文："multiplying those σ values by 3, achieving 99.7% confidence"） |
| `ε_guidance_y`, `ε_guidance_z` | 制导误差（估计位置与标称航迹最大偏差），分横向与高度 |
| `f_l`, `b`, `h` | 机身长、翼展、机高 |

**原文关键句**：
- "The cross-sectional geofencing safety buffer size δ_sb was calculated as the **maximum of
  [δ_sby, δ_sbz]**"
- "This process models the flight trajectory keep-in geofence cross-section to be **square**"
- 围栏宽度 = **2 δ_sb**（Fig 6）

### 2.5 Case study 参数

**Table III — 传感器参数**

| 量 | Aerosonde | AAM |
| --- | --- | --- |
| σ_accel [m/s²] | 0.024 | 0.024 |
| σ_gyro [rad/s] | 0.002 | 0.002 |
| σ_staticpress [Pa] | 10 | 7 |
| σ_diffpress [Pa] | 2 | 1.5 |
| σ_GPSn / σ_GPSe [m] | 7.2 / 7.2 | 6.5 / 6.5 |
| σ_GPSh [m] | 3.67 | 3 |
| σ_GPSVg [m/s] | 0.2 | 0.2 |
| σ_GPSχ [rad] | 0.05 | 0.05 |

Aerosonde 参数取自 [7][8]；AAM 的 GPS/气压计协方差**被调低**（假设 AAM 有更贵/更准的传感器）。
传感器偏置项假设已通过标定消除。巡航高度均 **300 m MSL**。

**Table IV — 缓冲尺寸参数（Unit: m）**

| 量 | Aerosonde | AAM |
| --- | --- | --- |
| `ε_guidance_y` | 16.90 | 18.11 |
| `ε_guidance_z` | 5.45 | 4.86 |
| `σ = [σx,σy,σz]` | [1.08, 0.66, 0.28] | [1.03, 0.78, 0.23] |
| `b`（翼展） | 2.89 | 8.7 |
| `f_l`（机身长） | 0.72 | 2.538 |
| `h`（机高） | 0.3 | 0.9 |

**Table V — 缓冲尺寸结果（Unit: m）**

| 模型 | δ_sb | δ_sbx |
| --- | --- | --- |
| Aerosonde UAS | **20.33** | **3.6** |
| AAM | **24.8** | **4.36** |

AAM 由 Aerosonde **按 3 倍线性放大**得到（碳纤维 `ρ = 250 kg/m³` 假设）；
机身长/机高由 Fig 7 示意图估计（真实尺寸未公开）。
场景：**曼哈顿 300 m MSL**，风场由 **ANSYS Fluent CFD** 生成（Fig 12）。

### 2.6 **式 7 的数值交叉核对（本次新增，脚本 `notes/verify_kim2022_eq7.py`）**

| 模型 | 量 | 式 7 计算 | Table V | 偏差 | 判定 |
| --- | --- | --- | --- | --- | --- |
| Aerosonde | δ_sbx | 3.6000 | 3.60 | 0.0000 | ✓ |
| Aerosonde | δ_sb | 20.3250 | 20.33 | −0.0050 | ✓ |
| AAM | δ_sbx | 4.3590 | 4.36 | −0.0010 | ✓ |
| AAM | δ_sb | 24.8000 | 24.80 | −0.0000 | ✓ |

**结论：式 7 完全复现 Table V ⟹ 我们对其缓冲构造的判读可靠。**

**笔误判定**：若式 7b 严格按正文印刷的 `3σz` 计算，得 δ_sb = 19.1850 m（Aerosonde）
与 23.1500 m（AAM），**与发表值不符**（差 −1.1450 / −1.6500 m）。
故确认 **7b 印刷为 `3σy` 之误**（按 Table V 反推必然使用横向 σ）。

**正文差值陈述复现**：横向差 4.4750 m（正文 4.47 ✓）、纵向差 0.7590 m（正文 0.76 ✓）。
正文称围栏宽度差 "approximately 8 m"，按表中数值应为 **8.95 m（≈9 m）**——
属其自身四舍五入不一致，**不影响任何结论**（仅说明其文本精度）。

**结构性判读（关键）**：

| 项 | Aerosonde | AAM |
| --- | --- | --- |
| 导航项 `3σ` | [3.24, 1.98, 0.84] m | [3.09, 2.34, 0.69] m |
| 制导项 | [16.90, 5.45] m | [18.11, 4.86] m |
| 制导项占横向分支 | **83.1%** | **73.0%** |
| 截面分支 [横向, 垂向] | [20.32, 6.44] → max 20.32 | [24.80, 6.00] → max 24.80 |

**注意：横/垂向分支中不含任何与来流方向（风向）有关的项。**
水平面内缓冲被 `max[δ_sby, δ_sbz]` **取为单一值 ⟹ 水平面内各向同性**，与正文
"cross-section ... square" 一致。

### 2.7 第 V 节（Case study 结果）

- 路径规划：**visibility graph**（最小行程航点序列）+ **Dubins 路径**连接（等高度、等速度）。
- Fig 13：黄色为**包裹航迹的 keep-in 围栏**，绿色为**建筑物的 keep-out 围栏**；
  缓冲按式 7 计算以保证 99.7% 置信。围栏宽度 = `2 δ_sb`。
- AAM 的缓冲比 Aerosonde 在**横向大 4.47 m、纵向大 0.76 m**，
  **尽管 AAM 的 GPS/气压传感器更好**——差异**来自机体尺寸**（机体系项与制导误差）。
- **风是主要的跟踪误差来源**：注入 **10 m/s** 大风后，两机**跟随航迹明显变差、
  跟踪误差显著增大**。故结论：
  > 最优缓冲尺寸必须把风纳入考虑（不规则城区/山地地形尤其）。
  > "Note that in the limit, a flight vehicle will be **grounded** when wind conditions
  > are forecast to exceed safe operating constraints."
- Fig 14：曼哈顿 3 m/s 西风飞行可视化。Fig 15/16：状态估计与真实状态时间序列。
  `t ≈ 40 s` 接近右侧高楼时北向风速因湍流增大；**风对 Aerosonde 的滚转/俯仰影响
  大于 AAM**（因 Aerosonde 总重更轻）。

### 2.8 第 VI 节（结论与未来工作）

- **结论**：提出用**车辆性能 + GNC + 预期风模型**计算航迹围栏缓冲尺寸的方法；
  状态估计与跟踪误差的**不确定性被统计建模**，连同**机体尺寸**一起换算为围栏缓冲。
- **未来工作**（原文）：
  > "additional environments, wind speeds, and vehicle models need to be analyzed to better
  > understand how geofence buffer dimensions vary as a function of each parameter.
  > We **hypothesize** that small fixed-wing UAS geofence buffers will have **similar sizings
  > in similar wind conditions** but further analysis is required to confirm this hypothesis.
  > For future analysis, we plan to generate a **database for varying wind conditions in
  > different city models** and investigate the effect of different wind conditions and
  > vehicle types on geofence buffer sizes."

**⚠ 其未来工作与 JAIS 2020 的"层缩放"同源**：注意参考文献 [6] 即
Stevens & Atkins, "Generating airspace geofence boundary layers in wind," *JAIS* 17(2),
113–124, 2020 —— **正是本项目研究对象（JAIS 2020）**。故该文与本项目**共享同一课题组传统**。

## 3. 参考文献表的关键条目（已核）

| # | 条目 | 意义 |
| --- | --- | --- |
| [2] | Stevens & Atkins, "Geofence definition and deconfliction for UAS traffic management," *IEEE T-ITS* 22(9), 5880–5889, 2020 | 同组传统 |
| [3] | J. T. Kim, A. Mathur, N. Liberko, E. Atkins, "Volumization and inverse volumization for low-altitude airspace geofencing," AIAA AVIATION 2021 | 姊妹篇（体积化） |
| [4] | Stevens & Atkins, "Layered geofences in complex airspace environments," 2018 | **分层围栏**（层缩放的源头） |
| [5] | Stevens, Rastgoftar, Atkins, "Geofence boundary violation detection in 3D using triangle weight characterization with adjacency," *JIRS* 95(1), 239–250, 2019 | 违规检测 |
| **[6]** | **Stevens & Atkins, "Generating airspace geofence boundary layers in wind," *JAIS* 17(2), 113–124, 2020** | **= 本项目研究对象（JAIS 2020）** |
| [7] | Beard & McLain, *Small Unmanned Aircraft: Theory and Practice*, Princeton, 2012 | 动力学/控制 |
| [8] | J. R. Rufa, PhD dissertation, University of Michigan, 2014 | 传感器融合（Aerosonde 传感器源） |
| [9] | de Berg et al., *Computational Geometry*, Springer, 1997 | **仅用于 visibility graph / 路径规划**，非圆盘填充 |
| [10] | Huang & Chung, "Dynamic visibility graph for path planning," IROS 2004 | 路径规划 |
| [11] | L. E. Dubins, *Amer. J. Math.* 79(3), 497–516, 1957 | Dubins 路径 |

**要点**：其引用 de Berg（计算几何）与 Dubins，但**仅用于路径规划**，
**未使用圆盘填充/顶点可行性分析**（对比：Ahn 2011 是本项目的几何工具来源）。

---

## 4. **四个悬置问题的答案（本项目长期阻塞项，现已解决）**

| # | 问题 | **答案** | 依据 |
| --- | --- | --- | --- |
| 1 | 其"verification"是解析还是统计？ | **统计**（3σ = 99.7% 置信） | 式 7 + §2.4 原文 |
| 2 | 是否处理**多边形顶点**？ | **否** | 式 7 只含 σ/制导误差/机体尺寸；缓冲为包裹航迹的管状体（Fig 13），**无内角、无顶点分析** |
| 3 | 其"turning flight"缓冲是否**方向依赖**？ | **否，水平面内各向同性** | `max[δsby, δsbz]` 取单一值 + "cross-section ... square"；§2.6 数值核对确认分支中无风方向项 |
| 4 | 是否含**接管延迟**？ | **否** | 式 7 无延迟项；误差来源为导航 σ + 制导误差 + 机体尺寸 |

**补充（第 5 项，本次新增）**：
5. **其"turning flight"如何体现？** —— **只通过 σ 的数值**（转弯使跟踪误差增大 → σ 增大），
   **不存在转弯专用的缓冲公式或方向项**。即"转弯"被吸收进统计 σ，而非进入几何构造。
   这一点很关键：其"含转弯飞行"是本项目 **D18** 的依据，但**不等于**它构造了转弯缓冲几何。

## 5. 与本项目的关系（逐项对照）

| 维度 | Kim 2022 | 本项目 |
| --- | --- | --- |
| 问题 | **需要多少缓冲**（size） | **既有缓冲的裕度如何变化**（margin） |
| 对象构造 | **自有的航迹包裹体积**（volumization） | **JAIS 2020 的 δu⊕δd 多边形缩放** |
| 保证形式 | **统计**（3σ） | **解析**（闭式 `R·cos(θ/2)`、`R·cot(θ/2)`） |
| 缓冲形状 | **各向同性**（截面方形） | **方向依赖**（K2：沿风 δu、垂直风 0） |
| 顶点/拐角 | **不处理** | **K8 / K9** |
| 接管延迟 | **不处理** | **K1 / H2（方向依赖 + 与空速无关）** |
| 滚转滞后 | 隐含于 6-DOF 气动（不单列） | **H3**（等价延迟 `τ_roll`） |
| 模型精度 | **6-DOF + 失速 + 舵机饱和 + CFD 风场**（更精细） | 3-DOF 点质量（更简，可解析） |

### 5.1 **结论：无直接竞争**

**四个问题全部为"否"**，即：该文**不处理顶点、不含延迟、缓冲各向同性、保证为统计**。
故本项目核心 claim **K1/K2/K8/K9/H2/H3 全部不受覆盖**。

### 5.2 **其各向同性缓冲与 P0 结果的呼应（新增观察，须谨慎表述）**

本项目 P0 检验（`EXP-FW-V1-26-envelope-neutrality.md`）发现：

> 用**各向同性半径**作为所需缓冲，在有风时**双向失效**（迎风不足、顺风过多）。

Kim 的截面缓冲正是**各向同性**（`max[δsby, δsbz]` + 明言 "square"），
即它在水平面内**不做方向区分**。

**⚠ 但不得据此批评该文**——理由三条：
1. 其 σ 由**真实不确定性传播**（EKF + CFD 风场）导出，风已进入 σ 的**大小**；
2. 其问题（包裹单条已知航迹）与本项目（缩放多边形围栏）**不同**；
3. 其取 max 是**保守**选择（宁大不小）。

**正确表述**：两者是**两种设计哲学**——
**各向同性 + 统计**（Kim）vs **方向依赖 + 解析**（JAIS/本项目）。
本项目 P0 结果刻画的是**后者的性质**。（由此新增 **D19**，见冻结 V2.4。）

## 6. 对本项目 claim 的影响

| 项 | 影响 |
| --- | --- |
| **K6 / D1**（"裕度特性尚不清晰"） | **维持不变，且现由全文支持**：该文只做尺寸、不做裕度；固定表述继续适用 |
| **D16 / D17**（顶点相关） | **维持**（该文不涉顶点） |
| **D18**（"此前未考虑转弯"） | **维持删除**，且**理由加强**：该文 σ 内已含转弯飞行影响 |
| **D19（新增）** | **不得**声称"既有围栏缓冲忽略方向依赖/假设各向同性"——JAIS 2020 本身即用**方向性** δd |
| **K1/K2/K8/K9/H2/H3** | **全部不受影响** |
| **Phase B 门禁**（原阻塞项 = Kim 2022 未读） | ✅ **已解除** |

### 6.1 **抢先风险评估上调（中等偏低 → 中等）**

该文与 JAIS 2020 **同一课题组**（Atkins），**同年在 DASC 发表**、
明确处理 **wind + GNC 不确定性 + 缓冲尺寸**，且其未来工作直言要建
"不同城市模型/风况的缓冲尺寸数据库"。加上
`D'Souza 2016 → JAIS 2020 → {Stevens 2021, Kim 2021, Kim 2022, Barkey 2023, Abdul 2026}`
的持续产出，说明：

> **该课题组持续在"缓冲尺寸 + 不确定性 + 风"上推进**，
> 而本项目研究的**同一构造（JAIS δu⊕δd）的裕度特性**，恰是其**下一步自然延伸**。

**风险等级上调**（原"中等偏低" → **中等**）。**缓解措施不变**：
卖点放在**解析闭式 + 顶点/延迟**（他们不做），而非泛泛的"裕度刻画"。

## 7. Observation / Interpretation / Limitation

### Observation

1. 缓冲公式为 `δ_sb = max[3σ_y + ε_gy + b/2, 3σ_z + ε_gz + h/2]`，纵向另加 `3σ_x + f_l/2`。
2. 式 7 **完全复现** Table V（4/4 通过，最大偏差 0.005 m = 其保留位数）；
   正文 7b 的 `3σz` **确证为 `3σy` 之误**（按 σz 得 19.185/23.150 m ≠ 20.33/24.80 m）。
3. 保证为 **3σ 统计置信（99.7%）**。
4. 水平面内缓冲**各向同性**（截面方形；分支中无风向相关项）。
5. 动力学为 **6-DOF + 非线性气动（含失速）+ 舵机饱和**，风场由 CFD 生成。
6. 式 7 **不含**延迟/接管时间项；**不含**顶点/内角分析。
7. "转弯飞行"**仅通过 σ 的数值**体现，无转弯专用几何项。
8. 其横向分支由**制导误差主导**（占 83.1% / 73.0%），导航项 `3σ ≤ 3.3 m` 是小量。
9. 结论明确承认**风是主要跟踪误差来源**，并指出风速超限时**应停飞**。
10. 参考文献 [6] = **JAIS 2020**（本项目研究对象）；[9] de Berg 仅用于路径规划。

### Interpretation

- 该文与本研究**问题层次不同、方法不同、构造不同**，**不构成直接竞争**；
- 本项目的解析闭式（K8/K9）与延迟预算（K1/H2/H3）**均为该文未覆盖**；
- **但**该课题组持续产出 + 其自述的下一步（风况/城市数据库）使**抢先风险上调至中等**；
- Kim 的各向同性缓冲与 P0 的"缓冲级双向失效"呼应，但**属不同设计哲学**，
  **不可**表述为"其存在缺陷"。

### Limitation

1. 本次为**截图阅读**，覆盖正文 I–VI、Fig 1–16、Table I–V 与参考文献表，
   **未覆盖**：其引文网络中我们未获取的其他工作；
2. 数值核对**仅针对式 7 与 Table IV/V 的自洽性**，
   **未复现**其 CFD/EKF/6-DOF 仿真（无法复现，也不必要）；
3. 其 σ 与制导误差是**仿真产物**，本项目无法独立核验其量值合理性；
4. 其"转弯飞行"的具体仿真设置（转弯曲率/航段）在正文未明确给出，
   故本记录对其转弯处理的判读仅以式 7 的结构为依据。

## 8. 后续动作

1. ~~更新 Phase B 门禁状态~~ ✅ 已完成（见 RESEARCH_PLAN v1.5 门控 G1）；
2. ~~LITERATURE_MAP 登记~~ ✅ 已完成（§3.9）；
3. ~~新增 D19 并发布冻结 V2.4~~ ✅ 已完成；
4. **维持** Thomas 2024（顶点）与 Ahn 2011（圆盘填充）为最近的竞争性相关工作；
5. **建议**：论文 Related Work 中把 Kim 2022 写成
   "**统计式缓冲尺寸设计**（3σ，各向同性截面）"，
   与本项目的"**解析式裕度刻画**（方向依赖）"并列对照，**不作优劣判断**。
