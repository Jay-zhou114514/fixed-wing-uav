"""P1：逆风方向 tau_crit 对风速比 w 的**非单调性**来源分析（解释性）。

背景（EXP-26 臂 I / 臂 R 的既有观察，不得重新解释为"新发现"）：
    位置 = 矩形边中点外 1R（A1R 区）；航向 psi0 = 180 度（**逆风**，风沿 +x）。
    w:      0.0     0.1     0.3     0.5
    tau_crit: 6.041   5.233   6.148   7.698   <-- 先降后升，非单调

============================================================
预注册（写在此处，先于任何计算；本脚本的运行结果不得修改本节）
============================================================

候选机制（两个方向相反的效应）：
  (E1) **推进速率变慢 -> tau 变长**：逆风使 |v_g| = Va(1-w) 减小，
       故单位延迟消耗的余量更少，tau_crit = room / rate_e 因而**随 w 增大**。
  (E2) **转弯段风致外摆 -> room 变小**：延迟结束后要执行一次最大速率转弯；
       有风时该转弯的地面轨迹是旋轮线（不是半径为 R 的圆），其外摆幅度
       随 w 变化。若转弯段把圆心到某条边的距离压到更小，则
       room = min(d0, dmin_turn) - R 减小，tau_crit 因而**随 w 减小**。

**H-P1**：非单调性来自 E1 与 E2 的竞争——
  小 w 时 E2 占优（转弯外摆使 room 下降快于 rate 下降）-> tau_crit 下降；
  大 w 时 E1 占优（rate 趋于 0，room/rate 发散）-> tau_crit 上升。

**H-P1b（更锐利的版本）**：在 w 的"下降段"，约束边（argmin 边）
  与"室温的来源"会**发生切换**：w=0 时 room 由 d0 决定（初始几何），
  进入下降段后由 dmin_turn 决定（转弯外摆）。

判定方式（三可值，不做单向预设）：
  - 若 dmin_turn 从未成为 min(d0, dmin_turn) 的取值者 -> H-P1b **否证**；
  - 若在某 w 切换 -> 记录切换点，并检查切换点是否落在下降段内；
  - 若 argmin 边发生切换，同样记录。

不做的事：不修改 EXP-26 主扫描的任何数值；不产生新 claim；
仅在结论成立且经文献核查后，才考虑登记为解释性结果（等级待定）。
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

R = J.R
VA = J.VA_DEFAULT
OMEGA = J.OMEGA
PSI_UPWIND = np.pi   # 180 度：逆风（风沿 +x）


def decompose(w, psi0=PSI_UPWIND):
    """返回该 (w, psi0) 下 tau_crit 的完整分解。"""
    V, ns, cs, shifts, V_s = J.setup_rect(w)
    e = 0
    mid = J.edge_midpoint(V_s, ns, cs, e)
    x0 = mid + 1.0 * R * (-ns[e])

    vg = J.v_ground(psi0, w, VA, 0.0)
    rates = ns @ vg

    rows = []
    for sign in (+1, -1):
        c0 = J.rolling_center(x0, psi0, sign, R)
        d0 = cs - ns @ c0
        dmin = np.array([
            J._turn_segment_min_de(x0, psi0, sign, ns[k], cs[k], w, R, VA, 0.0)
            for k in range(len(ns))
        ])
        m = np.minimum(d0, dmin)
        for k in range(len(ns)):
            room0 = d0[k] - R
            roomt = dmin[k] - R
            room = m[k] - R
            rate = rates[k]
            t_cand = room / rate if rate > 1e-9 else np.inf
            rows.append(dict(
                sign=sign, edge=k, rate=rate, d0=d0[k], dmin=dmin[k],
                room0=room0, roomt=roomt, room=room,
                source="d0" if d0[k] <= dmin[k] else "dmin_turn",
                t_cand=t_cand,
            ))
    ana, per = J.tau_crit_analytic_joint(x0, psi0, ns, cs, w, R)
    return dict(w=w, x0=x0, vg=vg, rows=rows, ana=ana, per=per,
                ns=ns, cs=cs, V_s=V_s)


def binding_of(d):
    """在主导 sign 上找 argmin（tau_crit = max over sign）。"""
    best_sign = max(d["per"], key=lambda s: d["per"][s])
    cands = [r for r in d["rows"] if r["sign"] == best_sign and np.isfinite(r["t_cand"])]
    if not cands:
        return best_sign, None
    b = min(cands, key=lambda r: r["t_cand"])
    return best_sign, b


print("=" * 100)
print("P1 逆风非单调性分析：位置 = 边中点外 1R；psi0 = 180 deg（逆风）")
print("=" * 100)
print(f"R = {R:.4f} m, Va = {VA}, omega = {np.degrees(OMEGA):.1f} deg/s")
print()

W_LIST = [0.0, 0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.6]

print("A. 复现既有观察（与 EXP-26 记录对比）")
print(f"{'w':>6}{'|v_g|':>9}{'tau_crit':>11}{'主导sign':>10}{'argmin边':>9}"
      f"{'room来源':>10}{'rate_e':>9}{'room':>9}")
print("-" * 100)
summary = []
for w in W_LIST:
    d = decompose(w)
    sign, b = binding_of(d)
    vgmag = float(np.linalg.norm(d["vg"]))
    if b is None:
        print(f"{w:>6.2f}{vgmag:>9.3f}{d['ana']:>11.4f}{sign:>10}{'--':>9}{'--':>10}"
              f"{'--':>9}{'--':>9}")
        summary.append((w, d["ana"], sign, None, None, None, None, vgmag))
        continue
    print(f"{w:>6.2f}{vgmag:>9.3f}{d['ana']:>11.4f}{sign:>10}{b['edge']:>9}"
          f"{b['source']:>10}{b['rate']:>9.3f}{b['room']:>9.2f}")
    summary.append((w, d["ana"], sign, b["edge"], b["source"], b["rate"],
                    b["room"], vgmag))

print()
print("B. H-P1b 判定：room 来源是否切换（d0 -> dmin_turn）")
srcs = [s[4] for s in summary]
if all(s == "d0" for s in srcs):
    print("   room 来源**始终为 d0**（初始几何）-> H-P1b **否证**（无切换）")
    verdict_switch = "no-switch"
elif all(s == "dmin_turn" for s in srcs):
    print("   room 来源**始终为 dmin_turn** -> 与 H-P1b 的'切换'预测不符")
    verdict_switch = "always-turn"
else:
    print("   room 来源**发生切换**：", end="")
    prev = None
    for w, _, _, _, src, _, _, _ in summary:
        if src != prev:
            print(f"w={w:g} 起为 {src}  ", end="")
            prev = src
    print()
    verdict_switch = "switch"

print()
print("C. 逐项分解（w=0.0 / 0.1 / 0.3 / 0.5，仅列有限候选，按 t_cand 升序前 4）")
print("=" * 100)
for w in (0.0, 0.1, 0.3, 0.5):
    d = decompose(w)
    sign, b = binding_of(d)
    print(f"\nw = {w:.2f}   tau_crit = {d['ana']:.4f} s   主导 sign = {sign:+d}"
          f"   |v_g| = {np.linalg.norm(d['vg']):.3f} m/s")
    cands = [r for r in d["rows"]
             if r["sign"] == sign and np.isfinite(r["t_cand"])]
    cands.sort(key=lambda r: r["t_cand"])
    print(f"   {'边':>4}{'rate':>9}{'d0':>10}{'dmin_turn':>11}{'room':>9}"
          f"{'来源':>10}{'t_cand':>10}")
    for r in cands[:4]:
        mark = " <== 约束" if (b is not None and r is b) else ""
        print(f"   {r['edge']:>4}{r['rate']:>9.3f}{r['d0']:>10.2f}"
              f"{r['dmin']:>11.2f}{r['room']:>9.2f}{r['source']:>10}"
              f"{r['t_cand']:>10.4f}{mark}")

print()
print("D. 两个效应的分离（在同一约束边 e 上，若约束边不变）")
print("=" * 100)
edges_used = {s[3] for s in summary if s[3] is not None}
print(f"   被用到的约束边集合 = {sorted(edges_used)}")
print()
print(f"   {'w':>6}{'约束边':>7}{'room(w)':>10}{'rate(w)':>10}{'room/Va(1-w)':>14}"
      f"{'若 room 恒为 room(0)':>20}")
print("-" * 100)
room0 = None
for w, tau, sign, e, src, rate, room, vgmag in summary:
    if e is None:
        continue
    if room0 is None:
        room0 = room
    counterfactual = room0 / rate if rate and rate > 1e-9 else float("inf")
    print(f"   {w:>6.2f}{e:>7}{room:>10.2f}{rate:>10.3f}{tau:>14.4f}"
          f"{counterfactual:>20.4f}")
print()
print("   判读：若 '若 room 恒为 room(0)' 一列单调上升，则 E1 单独作用为单调；")
print("         实际 tau_crit 的下降段只能由 room 自身随 w 下降（即 E2）解释。")
