# 会议论文正文草稿 V0.1

> **目标会议**：DASC（首选）→ ICUAS → AIAA SciTech → CCC/CCDC（保底）
> **目标投稿**：2027-03
> **证据依据**：`RESEARCH_QUESTION_FREEZE_V2.4.md`（claim 边界唯一依据）
> **纪律**：不得出现 D1–D19；不主张"首次"；Thomas 2024 / Ahn 2011 须正面引用
>
> **给负责人的中文导读（不属于论文正文）**：
> - 正文用**英文**撰写（DASC 要求），结构为 6 页会议论文。
> - **核心结论单一**：该围栏构造的安全裕度是**方向依赖**的，
>   且**在拐角处必然失效**——两者都有闭式解。
> - 每条结论后标注 **`[EXP-xx, 等级 A]`**，便于你核对与替换措辞。
> - 第 VII 节"Limitations"把未闭合项（有风 `d*`、凹多边形）全部写明，
>   **不得删除**——这是本项目最经得起审稿的部分。

---

## Title

**Characterizing Directional Safety Margins and Corner Failures of
Wind-Aware Fixed-Wing UAV Geofences**

*Alternative (shorter):* Directional Margins and Corner Dead Zones in
Wind-Aware Fixed-Wing Geofencing

**Authors / affiliation:** *[待填]*

---

## Abstract

Geofencing provides the last line of defense for low-altitude uncrewed
aircraft, and for fixed-wing vehicles the fence must be inflated outward by a
safety buffer because they cannot stop or turn instantaneously. Analytical
buffer constructions exist that scale a polygon fence outward using a uniform
turn-radius term and a wind-dependent directional term. What those
constructions do *not* provide is a characterization of the **remaining safety
margin** — where, and in which directions, the inflated fence still holds, and
where it does not.

This paper characterizes that margin for the analytical wind-aware
construction of [JAIS 2020]. Under a joint (simultaneous) feasibility model we
report three results. First, the margin is **strongly direction-dependent**:
along the wind the margin equals the turn radius `R`, perpendicular to the
wind it is **exactly zero**, and the zero-margin directions are set by the
existence of a polygon edge whose normal is perpendicular to the wind —
independent of polygon complexity `[EXP-27, grade A]`. Second, **per-edge
sufficiency does not imply joint sufficiency**: satisfying the buffer against
each edge separately can still admit a violation of `0.87 R` at an acute
vertex, and the corner overshoot has the closed form `R cos(θ/2)` for interior
angle `θ` `[EXP-27A, grade A]`. Third, each corner carries a **dead zone**
along its interior bisector of length `d* = R cot(θ/2)`, a function of the
interior angle alone `[EXP-26, grade A]`. We further translate these geometric
facts into a task-level **handover-latency budget**, show that the admissible
latency varies by a factor of **5.1** with approach direction, that it is
**exactly independent of airspeed**, and that roll-in transients act as one
additional roll time constant of delay.

*Index Terms* — geofencing, uncrewed aircraft, safety margins, turn radius,
handover latency, wind.

---

## I. Introduction

Low-altitude airspace is becoming populated, and geofencing — a virtual volume
an aircraft must not leave — is a primary containment mechanism. Fixed-wing
aircraft complicate the problem: they possess a minimum turn radius and cannot
arrest their motion, so a keep-in fence must be inflated outward by a buffer if
the vehicle is to have room to turn back.

Analytical buffer constructions for this purpose are available. [JAIS 2020]
scales a polygon fence by a uniform buffer `δ_u = V_a/ω` (the turn radius) plus
a directional buffer `δ_d` whose magnitude depends on the wind ratio and whose
direction is the wind direction. The construction is verified in that work by
the *success rate of layered-fence generation* — a geometric feasibility
property.

What is not established is the complementary question: given a fence built this
way, **how much safety margin actually remains, and where does it run out?**
The distinction matters operationally. A designer who knows only that the
construction is geometrically realizable cannot tell which approach directions
are tight, whether a corner behaves like a straight edge, or how much latency
the guidance layer may consume before the margin is gone.

This paper answers those questions for the analytical wind-aware construction.
We treat the buffer as given and characterize the margin it leaves, both
geometrically (Sections IV–V) and at the task level (Section VI).

**Contributions.**

1. **Directional margin structure.** The margin along the wind equals `R`;
   perpendicular to the wind it is exactly zero. Zero-margin directions are
   determined by the presence of an edge normal perpendicular to the wind and
   are independent of shape complexity (§IV).
2. **Per-edge is not joint.** Per-edge satisfaction does not imply simultaneous
   feasibility of the turning disk. A violation of `0.87 R` is demonstrated at
   an acute vertex, with closed form `R cos(θ/2)` (§V).
3. **Corner dead zones.** Each vertex has a dead zone of length
   `d* = R cot(θ/2)` along its interior bisector, depending only on the
   interior angle (§V).
4. **Latency budget.** Admissible handover latency varies 5.1× with approach
   direction, is exactly airspeed-independent, and is reduced by one roll time
   constant when roll-in dynamics are included (§VI).

---

## II. Model and Definitions

### A. Vehicle and wind model

We use a three-degree-of-freedom point-mass model in the horizontal plane with
constant wind. Let `V_a` be airspeed and `ω` the maximum turn rate. The turn
radius is

```
R = V_a / ω.                                  (1)
```

Wind is characterized by the ratio `w = V_w / V_a` and direction `φ_w`. Ground
velocity for heading `ψ` is `v_g = V_a e(ψ) + w V_a e(φ_w)`.

**Parameters used throughout:** `V_a = 18 m/s`, `ω = 25 °/s`, hence
`R = 41.2530 m`. Wind ratios `w ∈ {0, 0.1, 0.3, 0.5}` unless stated.

### B. The fence construction under study

We analyze the analytical construction of [JAIS 2020]. Each edge `e`, with
outward unit normal `n_e` and offset `c_e` in the half-plane representation
`n_e · x ≤ c_e`, is shifted to

```
c'_e = c_e − δ_u − δ_d · max(0, n_e · d_wind),          (2)

δ_u = R,                                                (3)
δ_d = R √(1−w²) + w R arccos(−w).                        (4)
```

The scaled polygon is the intersection of the shifted half-planes. Vertices of
the scaled polygon are obtained as intersections of adjacent shifted edges.

*Remark on `w = 0`.* The construction is parameterized by the wind direction,
which is undefined at `w = 0`. We treat `w = 0` as a degenerate boundary and
report it separately; see §VII.

### C. Maneuver model and horizon

Because the margin depends on what the vehicle is assumed to do, we fix the
maneuver model explicitly.

1. **Handover latency `τ`.** During `τ` the aircraft flies straight at its
   initial heading `ψ_0`.
2. **Maneuver.** At `τ`, a single maximum-rate turn is initiated in one of the
   two directions; the maneuver is evaluated until the first excursion.
3. **Horizon.** The evaluation horizon is the **first excursion**, defined as
   the first time the ground-velocity component along some edge normal turns
   non-positive. Continuous circling under steady wind drifts out of any
   bounded region, so infinite-horizon containment is not a meaningful target
   for this construction.

### D. Joint (simultaneous) condition

With the maneuver initiated at `τ`, the turning disk has center

```
c(τ) = x(τ) + s R (−sin ψ_τ, cos ψ_τ),   s ∈ {+1, −1},   (5)
```

and joint feasibility requires

```
c_e − n_e · c(τ) ≥ R   for all edges e simultaneously.   (6)
```

Requiring (6) **for all `e` at once** — rather than edge-by-edge — is the
distinction that Section V shows to be load-bearing.

### E. Margin and admissible latency, as defined quantities

```
margin(n)    = given(n) − required(n)               (7)
τ_crit(x_0, ψ_0) = sup { τ : no excursion within the horizon, joint feasible }
                                                     (8)
```

Both are defined only in conjunction with the maneuver model of §II-C; results
are not comparable across different maneuver models.

---

## III. Verification Protocol

Because the quantities above are easy to mis-implement, every reported result
passed a three-part self-check before being treated as a result.

* **(a) Negative control.** The criterion must pass where it should pass — e.g.
  a centroid position far from every edge must admit `τ = 0` without violation.
* **(b) Positive control.** The criterion must be able to *detect* a fault. A
  configuration known to violate must be reported as violating, with the
  predicted magnitude.
* **(c) Independent cross-validation.** An independently implemented
  formulation must agree.

A result whose self-check fails is void and is not discussed. We report two
instances in which this protocol caught errors in our own work (§VII).

---

## IV. Directional Margin Structure

We evaluate (7) on convex polygons normalized to a common circumscribed size,
for 125 configurations (rectangles over three aspect ratios and nineteen
orientations; regular `n`-gons for `n = 3…10` at seven orientations; and twelve
random convex polygons) across three wind ratios. `[EXP-27, grade A]`

### A. Result

```
margin(along wind)      = δ_u = R        (independent of w)     (9)
margin(⊥ wind)          = 0              (exactly tight)        (10)
```

The zero-margin direction is **not** a property of shape complexity. It is set
by whether the polygon possesses an edge whose outward normal is perpendicular
to the wind, because such an edge receives no directional shift in (2) and its
available margin is therefore exactly the uniform term minus the turn
requirement.

### B. Consequence

The construction is **exactly tight in the perpendicular-to-wind direction**:
there is no slack. Any effect not modeled in the buffer — latency, wind
estimate error, tracking error, roll transient — must produce a deficit in that
direction rather than being absorbed by margin. This is the motivation for the
dynamic analysis of Section VI.

---

## V. Corners: Per-Edge Sufficiency Is Not Joint

### A. The per-edge criterion is insufficient

Checking (6) edge-by-edge admits configurations in which the joint condition
fails. In our scan of the acute-vertex configuration the joint condition yields
a maximum admissible value of `35.726 m = 0.87 R`, violating in **215 of 215**
tested combinations of initial position and heading. `[EXP-27A, grade A]`

### B. Closed-form corner overshoot

For a vertex with interior angle `θ`, the overshoot beyond the scaled fence at
the first excursion is

```
violation = R cos(θ/2).                                  (11)
```

Verified against an independent geometric construction to `2.84e-14 m`. For
`θ = 90°` this gives `29.1702 m`; the same value appears independently as the
zero-latency overshoot in the task-level experiment of Section VI, where
`τ_crit < 0` confirms that **no positive latency is admissible** at a vertex.
`[EXP-27A, EXP-26 arm I, grade A]`

### C. Corner dead zones

Along the interior bisector of a vertex, there is a dead zone: positions closer
to the scaled vertex than

```
d* = R cot(θ/2)                                          (12)
```

admit no positive latency. The distance depends on the interior angle and `R`
alone, not on edge lengths, other vertex angles, or overall shape.

| `n` (regular) | `θ` | `d*/R` | `d*` (m) |
| --- | --- | --- | --- |
| 3 | 60° | 1.732051 | 71.4522 |
| 4 | 90° | 1.000000 | 41.2530 |
| 5 | 108° | 0.726543 | 29.9720 |
| 6 | 120° | 0.577350 | 23.8174 |

Verified on independent samples (new `θ`, and a new shape family of wedge
triangles with `θ = 70…130°` and edge lengths `10R…40R`), with maximum
deviation `6.1e-16` and shape-independence spread of exactly zero.
`[EXP-26 zone C, grade A]`

### D. Relation to prior work

The failure mechanism at acute vertices is already identified in
[Thomas & Sarhadi 2024, §3.4]: the turning circle does not fit, the vehicle is
driven toward the vertex and "will eventually penetrate the fence", and a turn
initiated at the standard trigger leaves the turning circle outside the
geozone. That work gives a straight-edge trigger-distance closed form
`s_min = r(cscθ − cotθ) = r·tan(θ/2)` with a transient term `s_t`, and handles
acute corners by testing **both** turning circles against the approaching fence
and its two neighbours. We therefore make **no claim of first discovery of the
mechanism, nor of a joint test**. Its treatment of the corner is **qualitative**
— it reports that penetration occurs and may be unavoidable, but gives no
penetration depth and no dead-zone extent (`depth`, `overshoot`, `margin`,
`buffer size` each occur zero times in the full text). Our increment is
therefore the **closed-form quantification**: the overshoot (11) and the dead
zone (12), together with the demonstration in §V-A that the per-edge criterion
underlying the construction studied here is not sufficient. The joint-feasibility
test itself is the disk-filling feasibility long established in computational
geometry [Ahn et al. 2011]; we apply it rather than introduce it.

---

## VI. Task-Level Latency Budget

We now translate the geometric findings into the quantity a guidance designer
actually budgets: the admissible handover latency.

### A. Direction dependence

At `w = 0.3`, position one turn radius outside an edge midpoint, the admissible
latency varies with approach direction by a factor of **5.1**:

| `ψ_0` (deg) | 0 | 45 | 90 | 135 | 180 | 225 | 270 | 315 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `τ_crit` (s) | 4.99 | 8.59 | 9.79 | 11.55 | 6.15 | 5.53 | **2.29** | 4.30 |

`[EXP-26 arm I, grade A]` The admissible latency is therefore **not a system
constant** and cannot be specified as a single number.

### B. Latency law and airspeed independence

Along the wind, the latency law is

```
τ_L* = 1 / (ω (1 + w)).                                  (13)
```

`[EXP-23, grade A]` Scanning airspeed, `τ_crit` at fixed position and heading is
**exactly** independent of `V_a`: across 24 combinations the maximum coefficient
of variation is `2.792e-16`, i.e. machine precision. `[EXP-26 airspeed, grade A]`

**Engineering consequence:** the latency budget need not be calibrated against
airspeed; it must be specified against **direction**.

### C. Roll-in dynamics as an equivalent delay

Replacing the instantaneous-turn assumption with a first-order roll response of
time constant `τ_roll` gives

```
τ_crit(roll) = τ_base − τ_roll,                          (14)
```

with a maximum relative deviation of `2.4%` over 72 combinations.
`[EXP-26 arm R, grade A]` Equation (14) is a **good approximation rather than an
identity**: during the roll-in the turn rate ramps rather than being constant.

### D. Conservatism of the disk criterion

The disk criterion (6) is strictly tighter than the direct-trajectory criterion
in wind: the gap grows from `0` at `w = 0` to `3.014 m` at `w = 0.5`. The disk
criterion therefore yields a **conservative** (lower) estimate of admissible
latency. `[EXP-26 arm R, grade A]`

### E. Two-level behaviour of the isotropic approximation

Treating the required buffer as a single isotropic radius — as opposed to
treating the disk as a criterion — behaves differently. Tests split cleanly:

| Test | What is being tested | Result |
| --- | --- | --- |
| **A — criterion level** | disk-inside ⟹ aircraft-inside | **uniformly conservative**, 96/96 |
| **B — buffer level** | isotropic radius as the *required* buffer | **mixed**, 63 positive / 63 negative |

`[EXP-26-P0, grade A]` **Both must be reported together.** Reporting only
Test A would support the incorrect reading that an isotropic approximation is
always safe; Test B shows it fails in both directions under wind: **insufficient
downwind** (required `δd > R`) and **excessive upwind** (required `< R`).
*(Direction corrected 2026-09-19: the direction convention of `required(n)`
places `n=0` along the wind, where `required = δd`.)*

---

## VII. Limitations and Negative Results

We state the boundaries of these results explicitly.

1. **Wind-free closed form only for `d*`.** Equation (12) is exact at `w = 0`.
   Closed form under wind is **not established**; an analysis of the structure
   (the rolling center drifts downwind at `w V_a` independent of turn rate) is
   partial and is not claimed as a result.
2. **Convex polygons only.** Concave polygons and vertex flattening were
   scoped out; no claim is made there.
3. **Constant wind, 3-DOF, single-turn horizon.** Gusts, tracking error, and
   sustained circling are outside the model. The horizon is the first
   excursion, as defined in §II-C.
4. **`w = 0` is a degenerate boundary.** The construction is parameterized by
   the wind direction, which is undefined at `w = 0`. Reported trends across
   `w = 0` must therefore be read with the boundary reported separately; we
   corrected one such reading in our own analysis (below).
5. **Errors caught by our own protocol.** Two implementation faults were
   intercepted by the self-check of Section III and did not enter any
   conclusion: (i) a hard-coded polygon half-width that biased a control by
   `8.0e-05 s`; (ii) a closed form compared outside its domain of validity,
   returning non-finite values. We also retract a `w ≈ 0.32` threshold from
   earlier work in this project, found to be a criterion artifact, and retain
   the retraction in the record.
6. **Not claimed as contributions.** We do not claim first identification of
   acute-vertex failure, nor first use of a joint test, nor that prior work
   provides only binary corner tests — [Thomas & Sarhadi 2024] gives a
   straight-edge trigger closed form and a joint corner test [Sec. V-D]. We do
   not claim first use of a joint feasibility test (disk filling, [Ahn et al.
   2011]); nor the method of analytically defining a buffer and proving
   sufficiency [Narkawicz et al. 2013]; nor that prior geofencing work ignores
   direction dependence — the construction studied here is itself directional,
   and [Kim et al. 2022] uses an isotropic cross-section by construction in a
   different problem (sizing a buffer around one known trajectory), which is a
   design choice rather than a defect.
7. **Airspeed independence is model-conditional.** Result (2c) holds with the
   maximum turn rate ω held fixed, i.e. `R ∝ Va`. Under the coordinated-turn
   model `R = V²/(g·tan φ_max)` used in [Thomas & Sarhadi 2024], the turn radius
   scales as `V²` and `τ` scales as `V`, so the invariance does **not** hold in
   that model. We state (2c) as a property of the idealized constant-turn-rate
   model and do not present it as a general engineering law.

---

## VIII. Related Work

**Buffer construction.** [D'Souza 2016] initiated sizing keep-in fences from
vehicle performance and wind; [Stevens & Atkins 2018] scaled fence boundaries
by performance and environmental conditions; **[JAIS 2020]** provides the
analytical uniform and directional buffers analyzed here; [Stevens & Atkins
2021] addresses mission-level integration; [Abdul 2026] treats corridor-style
moving-cylinder fences with a different geometry.

**Buffer sizing under uncertainty.** **[Kim et al. 2022]** determines how large
a buffer must be, given vehicle dynamics, guidance–navigation–control
uncertainty, and a CFD wind field, achieving a statistical (3σ, 99.7%)
guarantee; the cross-section is isotropic by construction and the fence
encloses a single known trajectory. Their problem is *how much buffer is
needed*; ours is *what margin a given buffer leaves*. **[Kim et al. 2021]** and
the volumization line address airspace volume partitioning. We do not compare
the two approaches as better or worse; they answer different questions.

**Formal verification of buffers.** [Herencia-Zapana et al. 2010] and
**[Narkawicz et al. 2013]** define buffers analytically and prove properties of
them with mechanical theorem provers; [Kouskoulas et al. 2021] formalizes
violation prediction and safe maneuver selection, with flight tests. Our method
is an application of this tradition to the geofence construction of [JAIS
2020], not a new method.

**Curvature-constrained geometry.** The joint condition (6) is disk-filling
feasibility over a polygon, a mature notion in computational geometry:
**[Ahn et al. 2011]** characterizes reachability under bounded curvature using
exactly this tool, and [Agarwal et al. 2002] gives classical results for
curvature-constrained paths. This is the geometric basis for §V-A.

**Corner handling in geofencing.** **[Thomas & Sarhadi 2024]** (ARC) gives a
predictive range controller for arbitrary polygonal geozones, including concave
ones, with a straight-edge trigger closed form `s_min = r·tan(θ/2)` plus a
turn-transient term `s_t = V·t_c` derived from the roll response rise time.
At acute vertices (§3.4) it identifies the failure and handles it by testing
both turning circles jointly against the approaching fence and its two
neighbours; the corner treatment itself is qualitative. It does not model wind,
and states in §5.2 that compensating for it by slack on `t_c` leaves sideslip
able to "potentially push the vehicle outside of the geozone", requiring
additional modelling. Our contribution is the closed-form overshoot (11), the
dead-zone extent (12), and the formal statement that a per-edge criterion is
not sufficient — evaluated under steady wind on the analytic construction of
[JAIS 2020], which that work does not address.

**Positioning of this work.** Kim studies uncertainty-aware buffer sizing,
while the margin characteristics of analytical wind-aware geofence
constructions remain unclear. `[fixed wording]`

---

## IX. Conclusion

For the analytical wind-aware geofence buffer construction, the safety margin
is direction-dependent and exactly zero perpendicular to the wind, so that any
unmodeled effect produces a deficit rather than being absorbed. At corners the
construction fails in a way that per-edge checking does not reveal, with
overshoot `R cos(θ/2)` and a dead zone of length `R cot(θ/2)` determined by the
interior angle alone. At the task level, admissible handover latency varies
5.1× with approach direction, is exactly independent of airspeed, and is
reduced by one roll time constant under first-order roll dynamics. These
results are closed-form, independently cross-validated, and bounded by the
limitations of Section VII.

**Future work** is to extend the corner closed form to steady wind, to relax
the convexity assumption, and to quantify the asymmetric risk introduced by
wind-estimate error.

---

## References

*[主条目；终稿按目标会议要求补全 DOI 与页码]*

1. D'Souza, S., et al. "Developing a Geofencing Concept of Operations for UAS
   Traffic Management." *DASC*, 2016.
2. Stevens, M. N., Atkins, E. M. "Layered Geofences in Complex Airspace
   Environments." *AIAA AVIATION*, 2018.
3. **Stevens, M. N., Atkins, E. M. "Generating Airspace Geofence Boundary
   Layers in Wind." *Journal of Aerospace Information Systems*, 17(2),
   113–124, 2020.** DOI 10.2514/1.I010792. *[研究对象]*
4. Stevens, M. N., Atkins, E. M. "Geofence Definition and Deconfliction for UAS
   Traffic Management." *IEEE T-ITS*, 22(9), 5880–5889, 2020.
5. **Ahn, H.-K., Cheong, O., Matoušek, J., Vigneron, A. "Reachability by Paths
   of Bounded Curvature in a Convex Polygon." *Computational Geometry*, 2011.**
   *[联合判据的几何工具来源]*
6. Agarwal, P. K., et al. "Approximating Shortest Paths in Weighted Regions."
   *SIAM J. Comput.*, 2002.
7. **Kim, J., Liberko, N., Atkins, E. M. "Airspace Geofencing Volume Sizing with
   an Advanced Air Mobility Vehicle Performance Model." *DASC*, 2022.**
   DOI 10.1109/DASC55683.2022.9925807.
8. Kim, J. T., Mathur, A., Liberko, N., Atkins, E. M. "Volumization and Inverse
   Volumization for Low-Altitude Airspace Geofencing." *AIAA AVIATION*, 2021.
9. **Thomas, P. R., Sarhadi, P. "Geofencing Motion Planning for Unmanned
   Aerial Vehicles Using an Anticipatory Range Control Algorithm."
   *Machines* 12(1), 36, 2024.** DOI 10.3390/machines12010036.
   *[锐角顶点机制；须正面引用。标题已于 2026-09-19 按原文更正——此前误记为
   "Geofence Violation Prediction and Safe Maneuver Selection"]*
10. **Narkawicz, A., et al. "The MINIMUM-margin theorem..." / analytical buffer
    definition and formal proof. *Proc. IMechE Part G*, 2013.** *[方法学来源]*
11. Herencia-Zapana, H., et al. "PVS Verification of an Air Traffic Conflict
    Detection and Resolution Algorithm." *ICAS*, 2010.
12. Kouskoulas, Y., et al. "Formal Verification of Geofence Violation Prediction
    and Safe Maneuvers." *NFM*, 2021.
13. Abdul, et al. *Journal of Guidance, Control, and Dynamics*, 2026.

---

## 附：投稿前待办（中文，不属正文）

| # | 事项 | 状态 |
| --- | --- | --- |
| 1 | 补 `[JAIS 2020]` / `[Thomas 2024]` / `[Ahn 2011]` / `[Narkawicz 2013]` 的完整条目与 DOI | 待做 |
| 2 | 按 DASC 模板排版（IEEEtran，6 页） | 待做 |
| 3 | **补图 2–3 张**：① 拐角穿透示意（θ、`R·cos(θ/2)`）；② `τ_crit` vs 接近方向极坐标图；③ `d*/R` vs `θ` 曲线。数据已在 `outputs/`、`docs/figures/` | **待做（重要，审稿看得到）** |
| 4 | 补作者、单位、致谢、基金号 | 待做 |
| 5 | 交付前用 `peer-review` 类工具自审一轮（对照 §VII 的"不作主张"清单） | 待做 |
| 6 | **文献定界 G1 未完全通过**（IEEE 全文层、ICRA/IROS、CNKI 未覆盖）⟹ 正文**不得**出现任何"首次"表述 | **纪律，终稿须复核** |

---

## 版本记录

| 版本 | 日期 | 变化 |
| --- | --- | --- |
| **V0.1** | **2026-09-19** | **首版正文草稿：单一核心结论（方向依赖裕度 + 拐角必然失效），八节结构，全部数字标注 `[EXP-xx]`；Limitations 与"不作主张"清单齐备；附投稿前待办** |
