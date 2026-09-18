"""P1：逆风 tau_crit 对 w 的"非单调性" —— 判定其为参数化分支伪影，并给出闭式。

========================= 首轮记录（三件套未通过，保留不删除） =========================
本脚本是 P1 的**首轮**实现。三件套首轮**未通过**：

  (a) 负对照  : 不通过（差 7.99e-05 s）
     原因：半边长**硬编码 150.0**，而几何实际为 149.998561493 m。
  (b) 正对照  : 通过，但输出含 inf
  (c) 交叉验证: 不通过（inf）
     原因：闭式的比较区间越出**适用域**（闭式在 w>0.6949 后失效，
     因整圈转弯的下风漂移越过下风墙），却仍按全域比较。

**保留本脚本的理由**：它记录了"跳过适用域检查会把'闭式域外失效'与
'闭式本身有误'混为一谈"这一错误模式。修正版为
`notes/p1_upwind_nonmonotonicity_v2.py`（三件套全过），结论见
`experiments/EXP-FW-V1-26-P1-upwind-monotonicity.md`。

=============================== 原始设计（未改） ===============================
结论目标（先写下来，后验证）：
  **在 w > 0 上，逆风方向的 tau_crit 是 w 的严格单调递增函数**，闭式为

      tau_upwind(w) = [ rho0 - delta_d(w)/2 ] / [ Va (1 - w) ]        (w > 0)

  其中 rho0 = (L/2) - R 为该位置在 w=0 时的 room（L 为围栏边长，位置取
  迎风边中点外 R）。**观察到的"先降后升"完全来自 w=0 单点上的分支不连续**：
  各实现均采用 `delta_d(w<=0) = 0`，而 JAIS 式在 w→0+ 的极限为 R
  （delta_d/R = sqrt(1-w^2) + w*arccos(-w) -> 1），故

      tau(0)  = rho0 / Va                      = 6.0414 s
      tau(0+) = (rho0 - R/2) / Va              = 4.8956 s

  两者之差恰为 R/(2Va) = 1.1458 s。

三件套（本核查自身也要自检）：
  (a) 负对照：闭式在 w=0 必须复现既有 6.0414 s；且 w=0 处 room 必须等于 L/2-R；
  (b) **正对照（可探测性）**：人为破坏闭式（漏掉 delta_d/2 项）后，
      与数值的偏差必须显著超出容差 —— 否则本核查无鉴别力；
  (c) 交叉验证：闭式 vs `tau_crit_analytic_joint`（臂 I 的独立实现）。

============================= 适用域（首轮遗漏，导致 (c) 失败） =============================
  闭式**仅在该位置由"迎风墙"约束时成立**。w 大到整圈转弯的下风漂移
  (w*Va*2*pi/omega) 越过下风墙后，tau_crit 转负（不可行），闭式不再描述该情形。
  实测边界 w* = 0.694883301078。修正版把比较区间限定为 0.001 <= w <= 0.60。
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np

SRC = Path(__file__).resolve().parent.parent / "src" / "exp_fw_v1_26_joint_latency.py"
spec = importlib.util.spec_from_file_location("j26", SRC)
J = importlib.util.module_from_spec(spec)
sys.modules["j26"] = J
spec.loader.exec_module(J)

R, VA, OMEGA = J.R, J.VA_DEFAULT, J.OMEGA
PSI_UPWIND = np.pi
L_HALF = 150.0          # <-- 首轮硬编码（错误来源）；实际 149.998561493
WIDTH = 2 * L_HALF


def numerics(w, psi0=PSI_UPWIND, edge=0, rho_out=1.0):
    """臂 I 数值：位置 = 缩放层边中点外 rho_out*R，返回 tau_crit 与 x0。"""
    V, ns, cs, shifts, V_s = J.setup_rect(w)
    mid = J.edge_midpoint(V_s, ns, cs, edge)
    x0 = mid + rho_out * R * (-ns[edge])
    tau, per = J.tau_crit_analytic_joint(x0, psi0, ns, cs, w, R)
    return tau, x0


def closed_form(w, rho_out=1.0):
    """P1 闭式（仅对轴对齐矩形 + 风平行于边 + 迎风边中点外 rho_out*R 成立）。

    room(w) = L_HALF - R - delta_d(w)/2
    速率    = Va(1-w)          （逆风航向 psi0=180 的地速沿 -x）
    """
    dd = J.delta_d(w)
    rho0 = L_HALF - R
    room = rho0 - dd / 2.0
    return room / (VA * (1.0 - w))


def closed_form_broken(w):
    """正对照：漏掉 delta_d/2 项（只保留初始 room），这是最易犯的错误版本。"""
    return (L_HALF - R) / (VA * (1.0 - w))


def closed_form_no_rate(w):
    """正对照 2：漏掉速率随风衰减（误用 Va 而非 Va(1-w)）。"""
    dd = J.delta_d(w)
    return (L_HALF - R - dd / 2.0) / VA


print("=" * 96)
print("P1  逆风 tau_crit 的非单调性：分支伪影判定 + 闭式 (首轮实现)")
print("=" * 96)
print(f"R = {R:.6f} m, Va = {VA} m/s, L/2 = {L_HALF} m（硬编码）, "
      f"rho0 = L/2 - R = {L_HALF-R:.4f} m")
print()

# ---------------------------------------------------------------- 三件套
print("[三件套]")
print("-" * 96)

# (a) 负对照：w=0 必须复现 6.0414，且 room = L/2 - R
t0_num, x0_0 = numerics(0.0)
expected_t0 = (L_HALF - R) / VA
ok_a = abs(t0_num - expected_t0) < 1e-9
print(f"  (a) 负对照  : w=0 数值 tau = {t0_num:.10f} s；期望 (L/2-R)/Va = "
      f"{expected_t0:.10f} s；差 {abs(t0_num-expected_t0):.2e}"
      f"  -> {'通过' if ok_a else '不通过'}")

# (b) 正对照：破坏闭式必须被探测到
worst_broken = 0.0
worst_norate = 0.0
for w in np.linspace(0.01, 0.95, 40):
    tn, _ = numerics(float(w))
    worst_broken = max(worst_broken, abs(closed_form_broken(float(w)) - tn))
    worst_norate = max(worst_norate, abs(closed_form_no_rate(float(w)) - tn))
ok_b = (worst_broken > 0.5) and (worst_norate > 0.5)
print(f"  (b) 正对照  : 漏 delta_d/2 项 -> 与数值最大偏差 {worst_broken:.4f} s；"
      f"漏速率衰减 -> {worst_norate:.4f} s")
print(f"                两者均 >> 容差 -> 本核查有鉴别力：{'通过' if ok_b else '不通过'}")

# (c) 交叉验证：闭式 vs 臂 I 数值  <-- 首轮未限定适用域，故失败
worst_c = 0.0
rows = []
for w in [0.001, 0.01, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99]:
    tn, _ = numerics(w)
    tc = closed_form(w)
    d = abs(tc - tn)
    worst_c = max(worst_c, d)
    rows.append((w, tn, tc, d))
ok_c = worst_c < 1e-9
print(f"  (c) 交叉验证: 闭式 vs 臂 I 独立实现，{len(rows)} 组，最大差 {worst_c:.3e} s"
      f"  -> {'通过' if ok_c else '不通过'}")
print()

# ---------------------------------------------------------------- 主表
print("[A. 闭式 vs 数值（含 w=0 单点与极限对比）]")
print("-" * 96)
print(f"{'w':>7}{'数值 tau':>13}{'闭式 tau':>13}{'差':>11}{'delta_d':>12}{'room':>10}")
for w in [0.0, 0.001, 0.01, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99]:
    tn, _ = numerics(w)
    tc = closed_form(w) if w > 0 else (L_HALF - R) / VA
    dd = J.delta_d(w)
    room = L_HALF - R - dd / 2.0
    d = abs(tc - tn)
    tag = "  <-- 分支点" if w == 0.0 else ("  <-- w>0 极限" if w == 0.001 else "")
    print(f"{w:>7.3f}{tn:>13.6f}{tc:>13.6f}{d:>11.1e}{dd:>12.4f}{room:>10.4f}{tag}")
print()
lim_0p = (L_HALF - R - R / 2.0) / VA
t0 = (L_HALF - R) / VA
print(f"  w=0 点      : tau = {t0:.6f} s   （delta_d 被守卫置 0）")
print(f"  w->0+ 极限  : tau = {lim_0p:.6f} s （delta_d -> R）")
print(f"  跳变量      : {t0 - lim_0p:.6f} s = R/(2Va) = {R/(2*VA):.6f} s"
      f"  -> {'吻合' if abs((t0-lim_0p) - R/(2*VA)) < 1e-12 else '不吻合'}")
print()

# ---------------------------------------------------------------- 单调性
print("[B. w>0 上的单调性（解析 + 数值）]")
print("-" * 96)
print("  tau(w) = N(w)/D(w),  N = rho0 - delta_d/2,  D = Va(1-w)")
print("  N' = -delta_d'/2 = -R*arccos(-w)/2,   D' = -Va")
print("  sign(tau') = sign( N'D - N D' ) = sign( 2*rho0 - R*[sqrt(1-w^2)+arccos(-w)] )")
ws = np.linspace(1e-6, 1.0 - 1e-12, 400001)
bracket = np.sqrt(1 - ws**2) + np.arccos(-ws)
crit = 2 * (L_HALF - R) - R * bracket
print(f"  括号项 sqrt(1-w^2)+arccos(-w) 在 (0,1) 上单调增："
      f"w->0+ 为 {bracket[0]:.6f}，w->1- 为 {bracket[-1]:.6f}")
print(f"  单调性条件 2*rho0 > R*bracket：2*rho0 = {2*(L_HALF-R):.4f} m；"
      f"R*bracket_max = {R*bracket[-1]:.4f} m")
print(f"  -> 全程满足：{'是' if crit.min() > 0 else '否'}（crit 最小值 = {crit.min():.4f}）")
tt = np.array([closed_form(float(w)) for w in np.linspace(0.001, 0.999, 2000)])
mono = bool(np.all(np.diff(tt) > 0))
print(f"  数值检验（2000 点）：tau' > 0 处处成立 -> {'严格单调递增' if mono else '存在下降段'}")
print(f"  单调性对围栏尺寸的条件：L/2 > R*(1 + pi/2) = {R*(1+np.pi/2):.4f} m"
      f"（本实验 L/2 = {L_HALF:.1f} m）")
print()

# ---------------------------------------------------------------- 全方向
print("[C. 其余接近方向的单调性（完整性检查）]")
print("-" * 96)
print(f"  {'psi(deg)':>9}{'tau(w=0)':>11}{'tau(0.1)':>10}{'tau(0.3)':>10}"
      f"{'tau(0.5)':>10}{'最小w':>9}{'单调?':>8}")
W_SWEEP = np.linspace(0.001, 0.9, 300)
for psi_deg in (0, 30, 45, 60, 90, 120, 135, 180, 225, 270, 315):
    psi = np.deg2rad(psi_deg)
    seq = []
    for w in W_SWEEP:
        t, _ = numerics(float(w), psi0=psi)
        seq.append(t if np.isfinite(t) else np.nan)
    seq = np.array(seq)
    taus = []
    for w in (0.0, 0.1, 0.3, 0.5):
        t, _ = numerics(w, psi0=psi)
        taus.append(t)
    finite = np.isfinite(seq)
    if finite.sum() < 3:
        print(f"  {psi_deg:>9}{taus[0]:>11.4f}{taus[1]:>10.4f}{taus[2]:>10.4f}"
              f"{taus[3]:>10.4f}{'--':>9}{'n/a':>8}")
        continue
    s = seq[finite]
    idx = np.where(finite)[0]
    mono_up = bool(np.all(np.diff(s) > 0))
    mono_dn = bool(np.all(np.diff(s) < 0))
    wmin = W_SWEEP[idx[int(np.argmin(s))]]
    print(f"  {psi_deg:>9}{taus[0]:>11.4f}{taus[1]:>10.4f}{taus[2]:>10.4f}"
          f"{taus[3]:>10.4f}{wmin:>9.3f}"
          f"{('单调增' if mono_up else ('单调减' if mono_dn else '非单调')):>8}")
print()
print("  说明：本表用臂 I 数值实现；psi=180 行对应本次分析对象。")
print()

# ---------------------------------------------------------------- 判定
print("=" * 96)
print("[判定]")
print("=" * 96)
print(f"  1. 闭式 tau_upwind(w) = [rho0 - delta_d(w)/2]/[Va(1-w)] 对 w>0 成立：")
print(f"     {len(rows)} 组最大偏差 {worst_c:.3e} s -> {'成立' if ok_c else '不成立'}")
print(f"  2. w>0 上严格单调递增 -> 逆风方向**不存在物理非单调性**")
print(f"  3. 观察到的 6.0414 -> 5.2331 -> 6.1479 -> 7.6981 的'下降'，")
print(f"     实际是 w=0 单点的分支跳变（{t0:.4f} -> {lim_0p:.4f} s，幅度 {t0-lim_0p:.4f} s）")
print(f"     + 其后的单调上升段。")
print(f"  4. 三件套：负对照 {'通过' if ok_a else '不通过'} / "
      f"正对照 {'通过' if ok_b else '不通过'} / 交叉 {'通过' if ok_c else '不通过'}")
print(f"     -> {'全部通过，结论可用' if (ok_a and ok_b and ok_c) else '未全过，结论不得使用'}")
print()
print("  ** 首轮三件套未全过 -> 本脚本输出不得用于结论 **")
print("  ** 已由 notes/p1_upwind_nonmonotonicity_v2.py 修正并重跑（全过） **")
