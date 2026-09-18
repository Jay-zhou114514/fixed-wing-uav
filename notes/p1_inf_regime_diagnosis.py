"""P1 附：w 较大时 tau_crit = -inf 的精确机制与边界（诊断）。

目的：
  1. 找出使 `tau_crit_analytic_joint` 返回 -inf 的**具体边**与分支；
  2. 用二分定出 -inf 出现的精确 w 边界；
  3. 判定该 -inf 是"几何不可行"（合法）还是"分支顺序伪影"。
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
PSI = np.pi
_V0, *_ = J.setup_rect(0.0)
L_HALF = float(np.abs(_V0[:, 0]).max())


def setup(w):
    V, ns, cs, shifts, V_s = J.setup_rect(w)
    mid = J.edge_midpoint(V_s, ns, cs, 0)
    x0 = mid + 1.0 * R * (-ns[0])
    return V, ns, cs, shifts, V_s, x0


def explain(w):
    """逐 sign 逐边展开 tau_crit 的决策分支。"""
    V, ns, cs, shifts, V_s, x0 = setup(w)
    vg = J.v_ground(PSI, w, VA, 0.0)
    rates = ns @ vg
    info = {}
    for sign in (+1, -1):
        c0 = J.rolling_center(x0, PSI, sign, R)
        d0 = cs - ns @ c0
        dmin = np.array([J._turn_segment_min_de(x0, PSI, sign, ns[k], cs[k], w, R, VA, 0.0)
                         for k in range(len(ns))])
        m = np.minimum(d0, dmin)
        best = np.inf
        decided_by = None
        for e in range(len(ns)):
            room = m[e] - R
            if rates[e] > 1e-9:
                t_e = room / rates[e]
                if t_e < best:
                    best = t_e
                    decided_by = ("push", e, room, rates[e])
            elif room < 0:
                best = -np.inf
                decided_by = ("graze_infeasible", e, room, rates[e])
                break
        info[sign] = dict(best=best, decided_by=decided_by, rates=rates,
                          d0=d0, dmin=dmin, m=m, c0=c0)
    tau, per = J.tau_crit_analytic_joint(x0, PSI, ns, cs, w, R)
    return dict(tau=tau, per=per, info=info, x0=x0, ns=ns, cs=cs, V_s=V_s,
                shifts=shifts, rates=rates)


print("=" * 104)
print("P1 附：-inf 的机制诊断")
print("=" * 104)
print(f"{'w':>6}{'sign':>6}{'判定':>20}{'边':>5}{'room':>11}{'rate':>11}"
      f"{'该 sign 的 tau':>15}")
for w in (0.60, 0.65, 0.68, 0.70, 0.80):
    d = explain(w)
    print("-" * 104)
    for sign in (+1, -1):
        i = d["info"][sign]
        db = i["decided_by"]
        tag = f"{db[0]}" if db else "--"
        e = db[1] if db else -1
        room = db[2] if db else float("nan")
        rt = db[3] if db else float("nan")
        b = i["best"]
        bs = f"{b:>15.6f}" if np.isfinite(b) else f"{'-inf':>15}"
        print(f"{w:>6.2f}{sign:>+6}{tag:>20}{e:>5}{room:>11.4f}{rt:>11.6f}{bs}")
    t = d["tau"]
    ts = f"{t:.6f}" if np.isfinite(t) else "-inf"
    print(f"{'':>6} -> tau_crit = {ts}   (x0 = ({d['x0'][0]:.4f}, {d['x0'][1]:.4f}))")

print()
print("=" * 104)
print("边界二分：tau_crit 首次变为非有限 / 负值的 w")
print("=" * 104)


def tau_at(w):
    V, ns, cs, shifts, V_s, x0 = setup(w)
    t, _ = J.tau_crit_analytic_joint(x0, PSI, ns, cs, w, R)
    return t


lo, hi = 0.60, 0.75
for _ in range(60):
    mid = 0.5 * (lo + hi)
    t = tau_at(mid)
    if np.isfinite(t):
        lo = mid
    else:
        hi = mid
print(f"  tau 由有限变为 -inf 的边界 w* = {hi:.12f}（区间 [{lo:.12f}, {hi:.12f}]）")
print(f"  该 w* 处：迎风墙闭式预测 tau = "
      f"{(L_HALF - R - J.delta_d(hi)/2)/(VA*(1-hi)):.6f} s")
print(f"            整圈转弯下风漂移 = {hi*VA*(2*np.pi/OMEGA):.4f} m")
print()

# 判定 -inf 是否为"真正的几何不可行"：检查两条边的最小距离
print("=" * 104)
print("独立性核查：-inf 是否等价于'转弯圆盘无法同时放进原多边形'？")
print("=" * 104)
print("  做法：对每个 sign，直接检验转弯段（含延迟 tau=0）中 **圆心到每条原多边形边**")
print("        的最小距离是否 < R。若某 sign 为真 → 该 sign 确实不可行（-inf 合法）。")
print()
print(f"  {'w':>6}{'sign':>6}{'min over turn (d_e)':>21}{'< R ?':>8}{'臂 I 判定':>12}{'一致?':>8}")
for w in (0.60, 0.65, 0.68, 0.70, 0.80, 0.90):
    d = explain(w)
    for sign in (+1, -1):
        i = d["info"][sign]
        mn = float(np.min(i["m"]))          # min(d0, dmin_turn) 全边最小
        infeasible = mn < R
        code_infeas = (not np.isfinite(i["best"])) or (i["best"] < 0)
        agree = (infeasible == code_infeas)
        print(f"  {w:>6.2f}{sign:>+6}{mn:>21.4f}{str(infeasible):>8}"
              f"{('不可行' if code_infeas else '可行'):>12}{str(agree):>8}")
print()
print("  注：'min over turn' 取 min(d0_e, dmin_turn_e) 对所有边的最小值；")
print("      < R 表示某个时刻圆盘已越出原多边形 → 该 sign 在任何延迟下都不可行。")

# 有限但为负的情形
print()
print("=" * 104)
print("补充：tau_crit 为**有限负值**的区间（'零延迟即越界'）")
print("=" * 104)
for w in np.linspace(0.0, 0.65, 14):
    t = tau_at(float(w))
    if np.isfinite(t):
        mark = "  <-- 零延迟即越界（tau<0）" if t < 0 else ""
        print(f"   w={w:>5.3f}  tau = {t:>10.6f} s{mark}")
