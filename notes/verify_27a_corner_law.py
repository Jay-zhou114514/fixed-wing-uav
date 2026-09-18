"""EXP-FW-V1-27A 的独立复核：转弯圆几何法 + 候选解析律。

目的：用**完全不依赖 τ 与轨迹积分**的方法重算违规量，与轨迹法交叉比对。

== 独立方法（转弯圆几何）==
飞机在 x0、初始航向 ψ0，以最小半径 R 转弯（sign = ±1）。
转弯圆圆心：center = x0 + sign·R·(−sin ψ0, cos ψ0)
该圆（半径 R）在方向 n_e 上的最远延伸 = n_e·center + R
越出边 e（半平面 n_e·x ≤ c_e）的量：

    pen_e = (n_e·center + R) − c_e = R − (c_e − n_e·center) = R − d_e

其中 d_e = c_e − n_e·center 为圆心到边的（有向）距离。
故 **pen_e = R − d_e**，纯几何，无 τ、无积分。

`circle_violation(x0,ψ0,sign) = max_e pen_e`；取 min over sign 得 V_circle。

== 候选解析律 ==
在缩放层顶点（距相邻两边各为 R）朝顶点方向飞行时：

    violation = R · cos(θ/2),   θ = 多边形内角

推导（一句话）：圆心相对顶点的偏移垂直于分角线，
使圆心到相邻边的距离减少 R·cos(θ/2)…

== 本脚本做三件事 ==
1. 用几何法重算，与轨迹法（core_V）逐例比对；
2. 检验候选律 violation = R·cos(θ/2)；
3. 扫内角 θ ∈ (0°,180°) 给出完整规律。
"""
from __future__ import annotations

import importlib.util

import numpy as np

VA = 18.0
OM = np.deg2rad(25.0)
R = VA / OM
TWO_PI = 2 * np.pi


def _load(path, name):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


GP = _load("src/exp_fw_v1_27_general_polygon.py", "gp")     # 几何工具
A27 = _load("src/exp_fw_v1_27a_simultaneous.py", "a27")     # 轨迹法（含 core_V）

hrep_from_verts = GP.hrep_from_verts
verts_from_hrep = GP.verts_from_hrep
scale_inward = GP.scale_inward
regular_ngon = GP.regular_ngon
rectangle = GP.rectangle
normalize_radius = GP.normalize_radius
delta_d = GP.delta_d


def scaled_geometry(V, w, phi_wind=0.0):
    """与 27A 一致：c'_e = c_e − δu − δd·max(0, n_e·d_wind)。"""
    ns, cs = hrep_from_verts(V)
    d_wind = np.array([np.cos(phi_wind), np.sin(phi_wind)])
    shifts = R + delta_d(w) * np.maximum(0.0, ns @ d_wind)
    return ns, cs, shifts, verts_from_hrep(ns, cs - shifts)


# ---------------------------------------------------------------- 独立几何法
def circle_violation(ns, cs, x0, psi0, sign):
    """转弯圆几何法的违规量：max_e (R − d_e)，d_e = c_e − n_e·center。"""
    center = np.asarray(x0) + sign * R * np.array([-np.sin(psi0), np.cos(psi0)])
    d = cs - ns @ center
    return float(np.max(R - d)), center, d


def V_circle(ns, cs, x0, psi0):
    vp, _, _ = circle_violation(ns, cs, x0, psi0, +1)
    vm, _, _ = circle_violation(ns, cs, x0, psi0, -1)
    return min(vp, vm)


# ---------------------------------------------------------------- 轨迹法
def V_traj(ns, cs, x0, psi0, w=0.0):
    """轨迹法（core_V）：min_sign max_e [pen_e − room_e]。"""
    pos = np.asarray(x0, float)[None, :]
    Vm = A27.core_V(np.array([psi0]), ns, cs, pos, w)
    return float(Vm[0, 0])


# ---------------------------------------------------------------- 主检验
def main():
    print("=" * 78)
    print("EXP-FW-V1-27A 独立复核：转弯圆几何法")
    print("=" * 78)
    print(f"\nVa={VA} m/s，ω=25°/s，R={R:.6f} m\n")

    # ---------- 1. 两个方法逐例比对 ----------
    print("[1] 几何法 vs 轨迹法（w=0，缩放层顶点，朝顶点方向）")
    print(f"   {'构型':>10} {'内角':>7} {'V_circle':>12} {'V_traj':>12} {'差':>10}")
    cases = []
    for n in (3, 4, 5, 6, 8, 10):
        V = normalize_radius(regular_ngon(n, 0.0))
        cases.append((f"正{n}边形", V))
    cases.append(("矩形1:1", normalize_radius(rectangle(300.0, 300.0, 0.0))))
    cases.append(("矩形2:1", normalize_radius(rectangle(600.0, 300.0, 0.0))))

    worst_diff = 0.0
    law_rows = []
    # 自检：配对必须用"最近原始顶点"，不能按索引（两者顶点顺序可能不同）
    pair_err = 0.0
    for name, V in cases:
        ns, cs, shifts, V_s = scaled_geometry(V, 0.0)
        m = len(V)
        interior = []
        for i in range(m):
            a, b, c = V[(i - 1) % m], V[i], V[(i + 1) % m]
            u = a - b
            w_ = c - b
            ang = np.arccos(np.clip(u @ w_ / (np.linalg.norm(u) * np.linalg.norm(w_)), -1, 1))
            interior.append(np.degrees(ang))
        for i in range(len(V_s)):
            x0 = V_s[i]
            # 最近原始顶点（沿角平分线朝外）
            j = int(np.argmin([np.linalg.norm(x0 - v) for v in V]))
            pair_err = max(pair_err, min(np.linalg.norm(x0 - v) for v in V))
            psi0 = float(np.arctan2(V[j][1] - x0[1], V[j][0] - x0[0]))
            vc = V_circle(ns, cs, x0, psi0)
            vt = V_traj(ns, cs, x0, psi0, 0.0)
            d = abs(vc - vt)
            worst_diff = max(worst_diff, d)
            law_rows.append((name, float(interior[j]), vc))
            print(f"   {name:>10} {interior[j]:>7.2f} {vc:>12.6f} {vt:>12.6f} {d:>10.2e}")
    print(f"\n   配对自检：最近原始顶点距离 = {pair_err:.3f} m（应一致且合理）")
    print(f"   两法最大差 = {worst_diff:.3e} m → "
          f"{'一致（独立推导互证）' if worst_diff < 1e-6 else '不一致'}")

    # ---------- 2. 候选律 ----------
    print("\n[2] 候选解析律：violation = R·cos(θ/2)")
    print(f"   {'构型':>10} {'θ内角':>7} {'θ/2':>7} {'实测 V':>12} {'R·cos(θ/2)':>12} {'差':>10}")
    worst_law = 0.0
    seen = set()
    for name, th, vc in law_rows:
        if name in seen:
            continue
        seen.add(name)
        pred = R * np.cos(np.deg2rad(th / 2))
        d = abs(vc - pred)
        worst_law = max(worst_law, d)
        print(f"   {name:>10} {th:>7.2f} {th/2:>7.2f} {vc:>12.6f} {pred:>12.6f} {d:>10.2e}")
    print(f"\n   候选律最大偏差 = {worst_law:.3e} m → "
          f"{'成立（解析律确认）' if worst_law < 1e-6 else '不成立'}")

    # ---------- 3. 内角扫描 ----------
    print("\n[3] 内角扫描：违规量随内角的变化（规则n边形 θ=180−360/n）")
    print(f"   {'n':>4} {'θ(deg)':>9} {'V实测':>12} {'V/R':>9} {'cos(θ/2)':>10}")
    for n in (3, 4, 5, 6, 7, 8, 10, 12, 16, 24, 36, 60, 120):
        V = normalize_radius(regular_ngon(n, 0.0))
        ns, cs, shifts, V_s = scaled_geometry(V, 0.0)
        th = 180.0 - 360.0 / n
        x0 = V_s[0]
        j = int(np.argmin([np.linalg.norm(x0 - v) for v in V]))
        psi0 = float(np.arctan2(V[j][1] - x0[1], V[j][0] - x0[0]))
        vc = V_circle(ns, cs, x0, psi0)
        print(f"   {n:>4} {th:>9.2f} {vc:>12.6f} {vc/R:>9.5f} {np.cos(np.deg2rad(th/2)):>10.5f}")

    # ---------- 4. 直边对照 ----------
    print("\n[4] 直边对照（应无违规）")
    V = rectangle(4000.0, 4000.0, 0.0)
    ns, cs, shifts, V_s = scaled_geometry(V, 0.0)
    mids = [(V_s[i] + V_s[(i + 1) % len(V_s)]) / 2 for i in range(len(V_s))]
    for x0 in mids:
        # 沿边方向
        for psi_deg in (0.0, 90.0, 180.0):
            psi0 = np.deg2rad(psi_deg)
            vc = V_circle(ns, cs, x0, psi0)
            if vc > 1e-9:
                print(f"   x0={np.round(x0,2)} ψ={psi_deg}° → V={vc:.6f}  ← 违规!")
    print("   （仅打印正值违规；无输出 = 无违规。负值=安全余量，属正常）")
    for x0 in mids[:1]:
        for psi_deg in (0.0, 90.0):
            psi0 = np.deg2rad(psi_deg)
            vc = V_circle(ns, cs, x0, psi0)
            print(f"   例：x0={np.round(x0,2)} ψ={psi_deg}° → V={vc:.9f}")

    print("\n" + "=" * 78)
    print("结论（待与文献比对）")
    print("=" * 78)
    print(f"  几何法与轨迹法最大差 {worst_diff:.2e} → 独立互证")
    print(f"  候选律 R·cos(θ/2) 最大偏差 {worst_law:.2e}")


if __name__ == "__main__":
    main()
