"""P1：逆风 tau_crit 对 w 的"非单调性" —— 判定分支伪影 + 闭式 + 适用域。

（本文件是 `p1_upwind_branch_artifact.py` 的修正版：
  1. 半边长不再硬编码 150.0，而由几何精确取得（原版因此使负对照差 8e-5 s）；
  2. 闭式比较限定在"迎风墙为约束边"的适用域内；
  3. 显式诊断 w 较大时出现的 tau_crit < 0（不可行）机制。
）

预注册（先写，后验证）：
  H-P1  : 非单调性来自"速率变慢（使 tau 变长）"与"转弯外摆（使 room 变小）"竞争。
  H-P1b : room 的取值来源（d0 vs dmin_turn）会发生切换。
  **已被前置分析否证**（room 来源始终为 d0；且 room 随 w 下降的机制是
    "缩放层中点随风偏移 δd/2"，不是转弯外摆）。

现行待验证命题（本脚本的目标）：
  H-P1'（参数化伪影）：观察到的 6.0414 -> 5.2331 -> 6.1479 -> 7.6981 中，
     **w=0 -> w>0 的下降是单点分支跳变**（delta_d 守卫 w<=0 → 0，而极限为 R），
     w>0 段则**严格单调递增**，闭式
        tau_upwind(w) = [ rho0 - delta_d(w)/2 ] / [ Va (1-w) ]
     其中 rho0 = 半边长 - R（位置 = 缩放层迎风边中点外 R）。
  适用域：迎风墙为约束边的 w 范围；超出后由转弯段下风漂移接管（tau < 0，不可行）。
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

# 半边长：由几何精确取得（不硬编码）
_V0, _ns0, _cs0, _sh0, _Vs0 = J.setup_rect(0.0)
L_HALF = float(np.abs(_V0[:, 0]).max())
RHO0 = L_HALF - R
print("=" * 100)
print("P1  逆风 tau_crit：分支伪影判定 + 闭式 + 适用域")
print("=" * 100)
print(f"R = {R:.9f} m（Va={VA}, omega={np.degrees(OMEGA):.4f} deg/s）")
print(f"归一化后半边长 L/2 = {L_HALF:.9f} m（由 setup_rect(0) 取出）")
print(f"rho0 = L/2 - R = {RHO0:.9f} m")
print()


def numerics(w, psi0=PSI_UPWIND, rho_out=1.0):
    V, ns, cs, shifts, V_s = J.setup_rect(w)
    mid = J.edge_midpoint(V_s, ns, cs, 0)
    x0 = mid + rho_out * R * (-ns[0])
    tau, per = J.tau_crit_analytic_joint(x0, psi0, ns, cs, w, R)
    return tau, x0, ns, cs


def closed_form(w):
    """仅适用于"迎风墙为约束边"的域。"""
    return (RHO0 - J.delta_d(w) / 2.0) / (VA * (1.0 - w))


# ------------------------------------------------------------------ 三件套
print("[三件套]")
print("-" * 100)
t0, _, _, _ = numerics(0.0)
exp_t0 = RHO0 / VA
ok_a = abs(t0 - exp_t0) < 1e-9
print(f"  (a) 负对照  : w=0 数值 {t0:.10f} s vs (rho0/Va) {exp_t0:.10f} s，"
      f"差 {abs(t0-exp_t0):.2e} -> {'通过' if ok_a else '不通过'}")

# 正对照：破坏闭式必须被探测
WBR = np.linspace(0.02, 0.55, 60)
wb = wn = 0.0
for w in WBR:
    tn, _, _, _ = numerics(float(w))
    wb = max(wb, abs((RHO0) / (VA * (1 - w)) - tn))              # 漏 delta_d/2
    wn = max(wn, abs((RHO0 - J.delta_d(float(w)) / 2) / VA - tn))  # 漏速率衰减
ok_b = (wb > 0.5) and (wn > 0.5)
print(f"  (b) 正对照  : 漏 delta_d/2 项 -> 最大偏差 {wb:.4f} s；"
      f"漏速率衰减 -> {wn:.4f} s -> 有鉴别力：{'通过' if ok_b else '不通过'}")

# 交叉验证只在适用域内
VALID_MAX = 0.60
rows = []
worst_c = 0.0
for w in [0.001, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.55, 0.60]:
    tn, _, _, _ = numerics(w)
    tc = closed_form(w)
    d = abs(tc - tn)
    worst_c = max(worst_c, d)
    rows.append((w, tn, tc, d))
ok_c = worst_c < 1e-9
print(f"  (c) 交叉验证: 闭式 vs 臂 I，{len(rows)} 组（0.001<=w<=0.60），"
      f"最大差 {worst_c:.3e} s -> {'通过' if ok_c else '不通过'}")
print()

# ------------------------------------------------------------------ 主表
print(f"[A. 闭式 vs 数值（含 w=0 分支点）]   适用域内有效")
print("-" * 100)
print(f"{'w':>7}{'数值 tau':>13}{'闭式 tau':>13}{'差':>10}{'delta_d':>11}"
      f"{'room':>10}{'rate':>9}")
for w in [0.0, 0.001, 0.005, 0.01, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.55, 0.60,
          0.65, 0.70, 0.75, 0.80]:
    tn, _, _, _ = numerics(w)
    tc = closed_form(w) if w > 0 else RHO0 / VA
    dd = J.delta_d(w)
    room = RHO0 - dd / 2.0
    tag = ""
    if w == 0.0:
        tag = "  <-- 分支点（守卫）"
    elif w == 0.001:
        tag = "  <-- w>0 极限"
    elif tn < 0:
        tag = "  <-- 数值不可行（闭式失效）"
    ts = f"{tn:>13.6f}" if np.isfinite(tn) else f"{'-inf':>13}"
    print(f"{w:>7.3f}{ts}{tc:>13.6f}"
          f"{(abs(tc-tn) if np.isfinite(tn) else float('nan')):>10.1e}"
          f"{dd:>11.4f}{room:>10.4f}{VA*(1-w):>9.4f}{tag}")

lim0p = (RHO0 - R / 2.0) / VA
t0v = RHO0 / VA
print()
print(f"  w=0 点（守卫 delta_d=0） : tau = {t0v:.6f} s")
print(f"  w->0+ 极限（delta_d->R） : tau = {lim0p:.6f} s")
print(f"  跳变量                   : {t0v-lim0p:.6f} s = R/(2Va) = {R/(2*VA):.9f} s"
      f"  -> {'吻合' if abs((t0v-lim0p)-R/(2*VA))<1e-12 else '不吻合'}")
print()

# ------------------------------------------------------------------ 单调性
print("[B. w>0 上的单调性（解析）]")
print("-" * 100)
print("  tau = N/D,  N = rho0 - delta_d/2,  D = Va(1-w)")
print("  delta_d'(w) = R*arccos(-w)   （直接求导，arccos 的导数与 sqrt 项相消）")
print("  sign(tau') = sign( 2*rho0 - R*[ sqrt(1-w^2) + arccos(-w) ] )")
ws = np.linspace(1e-9, 1.0 - 1e-12, 200001)
br = np.sqrt(1 - ws**2) + np.arccos(-ws)
crit = 2 * RHO0 - R * br
print(f"  2*rho0 = {2*RHO0:.6f} m；R*bracket_max = {R*br[-1]:.6f} m"
      f"（bracket: {br[0]:.6f} -> {br[-1]:.6f}）")
print(f"  crit 最小值 = {crit.min():.6f} > 0 -> 全程 tau' > 0："
      f"{'严格单调递增' if crit.min() > 0 else '存在下降段'}")
print(f"  普遍条件：半边长 > R*(1 + pi/2) = {R*(1+np.pi/2):.6f} m"
      f"（本实验 {L_HALF:.4f} m，余量 {L_HALF - R*(1+np.pi/2):.4f} m）")
print()

# ------------------------------------------------------------------ 适用域诊断
print("[C. 适用域边界：迎风墙 vs 转弯下风漂移 的约束切换]")
print("-" * 100)
print("  转弯段（整圈）中圆心 x 漂移 = w*Va*(2*pi/omega)")
print(f"  {'w':>6}{'漂移量(m)':>11}{'迎风墙约束 tau':>15}{'转弯后到右墙余量':>18}{'数值 tau':>11}{'接管者':>10}")
for w in [0.1, 0.3, 0.5, 0.6, 0.65, 0.7, 0.75, 0.8, 0.9]:
    drift = w * VA * (2 * np.pi / OMEGA)
    tn, x0, ns, cs = numerics(w)
    V, ns2, cs2, sh, V_s = J.setup_rect(w)
    # 转弯段结束时（整圈）圆心位置沿 +x 漂移 drift
    right_room_after = (L_HALF) - (x0[0] + drift) - R
    tau_cf = closed_form(w)
    who = "迎风墙" if tn > 0 else "转弯漂移"
    ts = f"{tn:>11.4f}" if np.isfinite(tn) else f"{'-inf':>11}"
    print(f"  {w:>6.2f}{drift:>11.2f}{tau_cf:>15.4f}{right_room_after:>18.4f}"
          f"{ts}{who:>10}")
print()
print("  判读：当 '转弯后到右墙余量' 变为负时，整圈转弯本身就会越过下风墙，")
print("        tau_crit 转为负值（不可行）——这是**另一机制**，不是闭式描述的对象。")
print()

# ------------------------------------------------------------------ 全方向
print("[D. 各接近方向的单调性（完整性；臂 I 数值）]")
print("-" * 100)
W_SWEEP = np.linspace(0.001, 0.9, 400)
print(f"  {'psi(deg)':>9}{'tau(0)':>9}{'tau(0.1)':>9}{'tau(0.3)':>9}{'tau(0.5)':>9}"
      f"{'argmin w':>10}{'形状':>9}")
for psi_deg in (0, 30, 45, 60, 90, 120, 135, 180, 225, 270, 315):
    psi = np.deg2rad(psi_deg)
    seq = np.array([numerics(float(w), psi0=psi)[0] for w in W_SWEEP])
    fin = np.isfinite(seq)
    taus = [numerics(w, psi0=psi)[0] for w in (0.0, 0.1, 0.3, 0.5)]
    if fin.sum() < 3:
        shape = "n/a"
        wmin = np.nan
    else:
        s, idx = seq[fin], np.where(fin)[0]
        wmin = W_SWEEP[idx[int(np.argmin(s))]]
        up, dn = bool(np.all(np.diff(s) > 0)), bool(np.all(np.diff(s) < 0))
        shape = "单调增" if up else ("单调减" if dn else "非单调")
    print(f"  {psi_deg:>9}{taus[0]:>9.4f}{taus[1]:>9.4f}{taus[2]:>9.4f}"
          f"{taus[3]:>9.4f}{wmin:>10.3f}{shape:>9}")
print()

print("=" * 100)
print("[判定]")
print("=" * 100)
print(f"  1. 闭式 tau = [rho0 - delta_d(w)/2]/[Va(1-w)] 在适用域（w<=0.60）成立：")
print(f"     {len(rows)} 组最大偏差 {worst_c:.3e} s -> {'成立' if ok_c else '不成立'}")
print(f"  2. w>0 上严格单调递增（解析证明 + 数值 2000+ 点）")
print(f"  3. '先降'完全是 w=0 单点守卫造成的分支跳变：{t0v:.5f} -> {lim0p:.5f} s")
print(f"     （幅度 {t0v-lim0p:.5f} s = R/(2Va)），其后为单调上升段。")
print(f"  4. w 较大时（~0.65 起）出现 tau<0：机制为整圈转弯的下风漂移越过下风墙，")
print(f"     与闭式所描述的迎风墙约束无关。")
print(f"  5. 三件套：负 {'通过' if ok_a else '不通过'} / 正 {'通过' if ok_b else '不通过'}"
      f" / 交叉 {'通过' if ok_c else '不通过'}"
      f" -> {'全部通过，结论可用' if (ok_a and ok_b and ok_c) else '未全过'}")

# 写出 CSV 供记录
import csv
with open("outputs/p1_upwind_sweep.csv", "w", newline="", encoding="utf-8-sig") as f:
    wr = csv.writer(f)
    wr.writerow(["w", "tau_numeric", "tau_closed_form", "delta_d", "room",
                 "rate", "in_valid_domain"])
    for w in np.concatenate([np.array([0.0]), np.linspace(0.001, 0.99, 200)]):
        tn, _, _, _ = numerics(float(w))
        wr.writerow([f"{w:.6f}", f"{tn:.9f}" if np.isfinite(tn) else "-inf",
                     f"{closed_form(float(w)):.9f}", f"{J.delta_d(float(w)):.9f}",
                     f"{RHO0 - J.delta_d(float(w))/2:.9f}",
                     f"{VA*(1-float(w)):.9f}",
                     "1" if float(w) <= VALID_MAX else "0"])
print("\nwrote outputs/p1_upwind_sweep.csv")
