"""P1 附：几何口径诊断（先确认 A 区位置到底站在哪条线旁边）。

动机：手推 `room = 108.747 - delta_d(w)/2` 时符号与数值表不符，
且 `verts_from_hrep` 会按极角重排顶点（本项目已四次踩到"索引配对"错误），
故必须先确认 `edge_midpoint(V_s, ns, cs, 0)` 与 `ns[0]` 是否真配对。

本脚本只做**诊断打印**，不产生结论。
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

R, VA = J.R, J.VA_DEFAULT


def dump(w, e=0):
    V, ns, cs, shifts, V_s = J.setup_rect(w)
    print("=" * 92)
    print(f"w = {w}")
    print("=" * 92)
    print("原始顶点 V:")
    for i, v in enumerate(V):
        print(f"   V[{i}] = ({v[0]:>9.3f}, {v[1]:>9.3f})")
    print("原始半平面 (ns, cs) 与 shifts:")
    for k in range(len(ns)):
        print(f"   e={k}  n=({ns[k][0]:>7.3f},{ns[k][1]:>7.3f})  c={cs[k]:>9.3f}"
              f"  shift={shifts[k]:>8.3f}  c-shift={cs[k]-shifts[k]:>9.3f}")
    print("缩放后顶点 V_s（注意：verts_from_hrep 按极角重排）:")
    for i, v in enumerate(V_s):
        print(f"   V_s[{i}] = ({v[0]:>9.3f}, {v[1]:>9.3f})")

    mid = J.edge_midpoint(V_s, ns, cs, e)
    x0 = mid + 1.0 * R * (-ns[e])
    print(f"\n   edge_midpoint(e={e}) = ({mid[0]:.3f}, {mid[1]:.3f})"
          f"   [由 V_s[0],V_s[1] 构造]")
    print(f"   x0(e={e})            = ({x0[0]:.3f}, {x0[1]:.3f})")

    # 逐线核对：x0 到 "约束线 cs" 与 "围栏线 cs-shift" 的有向距离
    print(f"\n   {'边k':>4}{'n_k·x0':>12}{'cs_k-n·x0':>13}{'(cs-sh)-n·x0':>15}"
          f"{'  对 cs 的余量':>15}{'对围栏的余量':>15}")
    for k in range(len(ns)):
        d_cs = cs[k] - ns[k] @ x0
        d_sc = (cs[k] - shifts[k]) - ns[k] @ x0
        star = " <==" if k == e else ""
        print(f"   {k:>4}{ns[k]@x0:>12.3f}{d_cs:>13.3f}{d_sc:>15.3f}"
              f"{d_cs - R:>15.3f}{d_sc - R:>15.3f}{star}")

    # 哪条线离 x0 恰为 R？
    print("\n   判定：x0 到哪条线的有向距离恰为 R？")
    for k in range(len(ns)):
        for tag, cc in (("cs", cs[k]), ("cs-shift", cs[k] - shifts[k])):
            d = cc - ns[k] @ x0
            if abs(d - R) < 1e-6:
                print(f"     -> 到 边{k} 的 {tag} 线 = {d:.6f} = R  <== 精确相等")
    print()


for w in (0.0, 0.1, 0.3):
    dump(w)

print("=" * 92)
print("补充：delta_d 在 w=0 的分支")
print("=" * 92)
for w in (0.0, 1e-9, 1e-6, 0.001, 0.05, 0.1):
    print(f"   w={w:<10g} code delta_d = {J.delta_d(w):>10.6f}"
          f"   物理式 R*sqrt(1-w^2)+wR*arccos(-w) = "
          f"{R*np.sqrt(max(0.0,1-w*w)) + w*R*np.arccos(-w):>10.6f}")
print(f"\n   R = {R:.6f}")
print("   -> code 在 w<=0 时强制 delta_d=0；物理式的极限为 R。")
print("      这是**w=0 处的分支不连续**（参数化选择，非物理）。")
