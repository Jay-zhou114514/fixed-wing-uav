"""P2 诊断：有风时 d* 的结构（K9 的 w>0 推广）。

先做**结构诊断**，不预设闭式：

  Q1 沿向内分角线移动时，τ_crit(s) 的符号变化（dead zone）由**哪条边**触发？
     - 相邻边（rate>0，"推"边）？
     - 还是**对侧边**（rate<0，其 room 随 s 下降，先变负 → τ=-inf）？

  Q2 顶点 0 的向外分角线是否与风向对齐（正则 n 边、alpha=0）？
     若对齐，则 δd 对两条相邻边的平移**相同**，几何保持对称。

  Q3 有风时 d* 是否仍只由 (θ, w) 决定（K9 的"局部性"）？
     做 w 固定、顶点与风向**相对角**变化的对照。

本脚本只诊断，不给结论。
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np

SRC = Path(__file__).resolve().parent.parent / "src"
spec = importlib.util.spec_from_file_location("cd", SRC / "exp_fw_v1_26_critical_distance.py")
M = importlib.util.module_from_spec(spec)
sys.modules["cd"] = M
spec.loader.exec_module(M)

spec2 = importlib.util.spec_from_file_location("j26", SRC / "exp_fw_v1_26_joint_latency.py")
J = importlib.util.module_from_spec(spec2)
sys.modules["j26"] = J
spec2.loader.exec_module(J)

R = J.R
VA = J.VA_DEFAULT


def probe(n, w, va=VA, verbose=True):
    S = M.setup(n, w, va)
    xv, u_in, u_out, ns, cs, psi0 = S["xv"], S["u_in"], S["u_out"], S["ns"], S["cs"], S["psi0"]
    adj = S["adj"]
    r = S["r"]
    print("=" * 92)
    print(f"n={n} (theta={180-360/n:.2f} deg)  w={w}  va={va}")
    print(f"  R={r:.4f}  顶点 xv=({xv[0]:.3f},{xv[1]:.3f})  |xv|={np.linalg.norm(xv):.3f}")
    print(f"  分角线 out=({u_out[0]:.4f},{u_out[1]:.4f})  相对风向(+x)夹角="
          f"{np.degrees(np.arctan2(u_out[1], u_out[0])):.4f} deg")
    print(f"  相邻边索引 adj={adj}")
    vg = J.v_ground(psi0, w, va, 0.0)
    rates = ns @ vg
    print(f"  地速 vg=({vg[0]:.3f},{vg[1]:.3f})  |vg|={np.linalg.norm(vg):.3f}")
    print(f"  各边 rate = {np.round(rates,3)}")
    print(f"  相邻边 rate = {np.round(rates[adj],3)}   (正=推边)")
    print(f"  排序后 rate: 正 {np.sum(rates>1e-9)} 条，负 {np.sum(rates<-1e-9)} 条")
    if verbose:
        ds = np.linspace(0, 3 * r, 13)
        print(f"  {'s':>9}{'tau':>12}{'room_min':>11}{'binding边':>10}{'该边rate':>10}")
        for d in ds:
            x0 = xv + d * u_in
            tau, per = J.tau_crit_analytic_joint(x0, psi0, ns, cs, w, r, va=va)
            # 找 binding 边（主导 sign）
            bs = max(per, key=lambda s: per[s])
            c0 = J.rolling_center(x0, psi0, bs, r)
            d0 = cs - ns @ c0
            dmin = np.array([J._turn_segment_min_de(x0, psi0, bs, ns[k], cs[k], w, r, va, 0.0)
                             for k in range(len(ns))])
            m = np.minimum(d0, dmin)
            k = int(np.argmin(m))
            ts = f"{tau:>12.4f}" if np.isfinite(tau) else f"{'-inf':>12}"
            print(f"  {d:>9.2f}{ts}{m[k]:>11.3f}{k:>10}{rates[k]:>10.3f}")
    print()


for n in (3, 4, 5, 6):
    for w in (0.0, 0.3):
        probe(n, w)
