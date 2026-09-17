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
