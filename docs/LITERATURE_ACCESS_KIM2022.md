# 文献获取记录：Kim 2022 全文不可得（合法渠道穷尽）

- 日期：2026-09-19
- 对象：**Kim, J., Liberko, N., Atkins, E. (2022).** *Airspace Geofencing Volume Sizing
  with an Advanced Air Mobility Vehicle Performance Model.* IEEE/AIAA 41st DASC.
  DOI `10.1109/DASC55683.2022.9925807`
- 请求：负责人提供 ResearchGate 链接，要求**阅读全文**
- 结果：**全文未能获取**。合法公开渠道已穷尽（逐条记录见下）

---

## 1. 获取尝试（逐条记录）

| # | 渠道 | 结果 |
| --- | --- | --- |
| 1 | **ResearchGate**（负责人提供的链接） | **HTTP 403**，页面标题 "ResearchGate - Temporarily Unavailable" |
| 2 | **Unpaywall** | `is_oa: false`，**无任何 OA 位置** |
| 3 | **OpenAlex** | `oa_status: "closed"`；`any_repository_has_fulltext: false`；唯一 location 为 IEEE（付费） |
| 4 | **Semantic Scholar** | `openAccessPdf.url` **为空**；仅返回摘要 |
| 5 | **NASA NTRS**（作者为 NASA/密歇根系） | 检索 `geofencing volume sizing` → **0 命中** |
| 6 | **arXiv** | `all:"geofencing" AND all:"Atkins"` → **0**；`all:"geofence" AND all:"sizing"` → **0** |
| 7 | **Deep Blue**（密歇根大学机构库） | 被 Cloudflare 拦（"Just a moment..."），无法检索 |
| 8 | **IEEE Xplore 正文** | HTTP **202**（人机验证），无正文 |
| 9 | **doi.org 解析** | 302 → IEEE Xplore（同上，付费） |
| 10 | **Bing 检索** `"Airspace Geofencing Volume Sizing" ... pdf` | **无 PDF 链接、无学位论文、无 NASA 报告** |

**结论**：该文**闭源**，且**作者未在任何机构库或预印本平台发布**。
（注：作者含 **Ella Atkins**，即 JAIS 2020 的共同作者——故该文是同一课题组自己的后续。）

## 2. 已获取的最完整信息：摘要（已核验）

> "Airspace geofencing is a key enabler for versatile and safe low-altitude Unmanned
> Aircraft System (UAS) Traffic Management (UTM). Geofenced airspace volume sizing analysis
> is necessary to assure efficiency and safety for a broad suite of emerging UAS
> applications. Airspace safety buffer sizes can be determined and verified by modeling
> vehicle dynamics as well as quantifying guidance, navigation and control uncertainties.
> This paper proposes a methodology to design safety buffer sizes given specific vehicle and
> sensor properties and wind. These parameters are then translated to geofence safety buffer
> dimensions for **straight and turning flight** to **statistically guarantee** an aircraft
> will stay inside its flight trajectory based keep-in geofence. Vehicle, sensor, and wind
> parameters are tabulated and analyzed over a prescribed flight trajectory using a
> Computational Fluid Dynamics (CFD) analysis. Case studies using a small UAS model and a
> full-size advanced air mobility (AAM) aircraft model provide comparison of geofence volume
> sizings."

## 3. 摘要层面的关键判读（**这比我此前估计的更相关**）

| 要点 | 与本项目的关系 |
| --- | --- |
| "**determined and verified**" | 其自称做了**验证**——这正是本项目 K6 与 D1 的限定依据 |
| "**straight and turning flight**" | **明确包含转弯飞行**——与本项目的核心对象重合 |
| "**statistically guarantee**" | 其保证是**统计性的**（非解析） |
| 输入含 **GNC 不确定性** + **wind** + **CFD** | 处理的是**不确定性驱动的缓冲尺寸** |
| 输出为**"缓冲尺寸"**（volume sizing） | **问题层面仍不同**：尺寸设计 vs 裕度刻画 |

### 3.1 由摘要可确定的差异（无需全文）

| 维度 | Kim 2022 | 本项目 |
| --- | --- | --- |
| 问题 | **需要多少缓冲** | **既有缓冲的裕度如何变化** |
| 保证形式 | **统计**（Monte Carlo/CFD 抽样） | **解析**（闭式：`R·cos(θ/2)`、`R·cot(θ/2)`） |
| 是否处理顶点几何 | 摘要未提（**未知**） | 是（K8/K9） |
| 是否处理滚转滞后 | 摘要未提（**未知**） | 是（H3） |
| 是否处理联合/同时判据 | 摘要未提（**未知**） | 是（K4'） |

### 3.2 **仍无法确定的（必须全文才能判定）**

1. 其"verification"是**解析**还是**Monte Carlo**？
2. 是否处理**多边形顶点**（夹角 < 90° 的锐角情形）？
3. 其"turning flight"缓冲是否**方向依赖**？
4. 是否处理**接管延迟**（delay/latency）？

**这四项均直接影响本项目的新颖性判定。**

## 4. 对本项目 claim 的影响（**维持原有限定，不升级**）

**K6 与 D1 的表述保持不变**：

> K6：解析式风感知围栏构造的**安全裕度特性尚不清晰**
> （固定表述："Kim studies uncertainty-aware buffer sizing, while the margin
> characteristics of analytical wind-aware geofence constructions remain unclear."）

**理由**：本次仍**未读全文**，故仍不可评估其是否覆盖本项目的具体结论；
但按 `FROZEN_PROTOCOL` 第 13 节的 T3 规则（主张"首次/新"之前必须完成检索），
本项目**所有涉及"首次"的主张保持删除状态**。

**新增记录**：其摘要明确含 "**straight and turning flight**"，
故本项目若在论文中声称"此前工作未考虑转弯"将是**错误**的——
该主张必须避免（登记为 **D18**）。

## 5. 建议的后续获取途径（需负责人协助）

| 途径 | 说明 |
| --- | --- |
| **学校图书馆 IEEE 订阅** | 唯一可靠途径 |
| **向作者索取**（Atkins 课题组，密歇根） | 学术惯例允许 |
| **ResearchGate 请求全文**（登录后 Request full-text） | 需账号；负责人可直接操作 |

**建议**：由负责人通过学校图书馆或作者索取；本 Agent 无法绕过付费墙。

## 6. 诚实声明

1. 本文件**未读到全文**，仅核验摘要（多个独立源一致）；
2. **不得**据本文件对其内容作超出摘要的论断；
3. 摘要中"turning flight"一词**已足以约束本项目的一项表述**（D18）；
4. 全文获取失败**不阻塞**本项目实验，但**阻塞**"首次性"主张的最终确认。
