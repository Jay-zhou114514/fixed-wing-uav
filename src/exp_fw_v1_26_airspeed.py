"""EXP-FW-V1-26 空速扫描：检验 H2（τ_crit 与空速无关）。

预注册：experiments/EXP-FW-V1-26-preregistration.md 判据 P3
依据：H2："同一 w、同一 φ 下，τ_crit 与 Va 无关"

== 理论预判（本脚本要检验的）==
整个问题的几何是**尺度不变**的：
  R = Va/ω        ∝ Va
  δu = R, δd = R·(√(1−w²)+w·arccos(−w))   ∝ R ∝ Va
  风漂移项 w·Va·t = w·Va·(τ_ang/ω) = w·R·τ_ang   ∝ R
  ⇒ 所有长度量 ∝ R ∝ Va
  v_g·n = Va·(n·e(ψ)) + w·Va·(n·e_wind)   ∝ Va
  ⇒ τ_crit = margin/(v_g·n) ∝ Va/Va = 1/ω  **与 Va 严格无关**

**验证要求**：无量纲几何必须固定 —— 即多边形尺寸须随 R 缩放。
若固定绝对尺寸而改 Va，则比较的是不同形状，H2 的检验无效。

== 三件套（FROZEN_PROTOCOL 12.1，先跑）==
(a) 负对照：形心（远离各边）→ 应无越界
(b) 正对照：顶点越界量应 ∝ Va（即越界量/R 与 Va 无关）——
    该项确认 **Va 确实进入了计算**（否则"无关"可能是"没生效"）
(c) 交叉验证：解析式 vs 数值（每个 Va 独立）
"""
from __future__ import annotations

import csv
import importlib.util
import os

import numpy as np

_s = importlib.util.spec_from_file_location("a26", "src/exp_fw_v1_26_joint_latency.py")
A26 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A26)

OM = A26.OMEGA
TWO_PI = A26.TWO_PI
rectangle = A26.rectangle
scaled_geometry = A26.scaled_geometry
edge_midpoint = A26.edge_midpoint
simulate_arm_I = A26.simulate_arm_I
tau_crit_analytic_joint = A26.tau_crit_analytic_joint
tau_crit_measured = A26.tau_crit_measured

VA_LIST = (15.0, 18.0, 25.0)
HALF_R = 3.0          # 多边形半宽 = HALF_R · R（无量纲几何固定）


def shape_for_va(va, w, half_r=HALF_R):
    """构造**无量纲几何固定**的多边形：半宽 = half_r·R，R = va/ω。"""
    r = va / OM
    V = rectangle(2.0 * half_r * r, 2.0 * half_r * r, 0.0)
    ns, cs, shifts, V_s = scaled_geometry(V, w, va=va)
    return r, ns, cs, shifts, V_s


def c_neg():
    """(a) 负对照：形心（远离各边）应无越界。"""
    print("")
    print("[三件套 a] 负对照：形心（远离各边）应无越界")
    bad = tot = 0
    for va in VA_LIST:
        for w in (0.0, 0.3):
            r, ns, cs, shifts, V_s = shape_for_va(va, w)
            c = V_s.mean(axis=0)
            for psd in range(0, 360, 45):
                for sign in (+1, -1):
                    _, vi = simulate_arm_I(c, np.deg2rad(psd), sign, 0.0,
                                           ns, cs, w, r, va=va)
                    tot += 1
                    bad += int(vi)
    ok = bad == 0
    print(f"   {tot} 组合，越界 {bad} 个 -> {'通过' if ok else '不通过'}")
    return ok


def c_pos():
    """(b) 正对照：顶点越界量应 ∝ Va（即 越界量/R 恒定）。

    该项确认 Va 确实进入了计算；否则"τ_crit 与 Va 无关"可能只是"Va 没生效"。
    """
    print("")
    print("[三件套 b] 正对照：顶点越界量应 ∝ Va（越界量/R 恒定）")
    pred_ratio = np.cos(np.pi / 4)      # 内角 90° → cos(45°)
    print(f"   {'w':>5} {'Va':>6} {'R(m)':>9} {'越界量(m)':>11} {'越界量/R':>10} {'与 cos45° 差':>12}")
    worst = 0.0
    for w in (0.0, 0.3):
        for va in VA_LIST:
            r, ns, cs, shifts, V_s = shape_for_va(va, w)
            x0 = V_s[0]
            # 朝顶点外
            j = int(np.argmin([np.linalg.norm(x0 - v) for v in
                               rectangle(2 * HALF_R * r, 2 * HALF_R * r, 0.0)]))
            Vb = rectangle(2 * HALF_R * r, 2 * HALF_R * r, 0.0)
            j = int(np.argmin([np.linalg.norm(x0 - v) for v in Vb]))
            psi = float(np.arctan2(Vb[j][1] - x0[1], Vb[j][0] - x0[0]))
            best = -np.inf
            for sign in (+1, -1):
                m_, _ = simulate_arm_I(x0, psi, sign, 0.0, ns, cs, w, r, va=va)
                best = max(best, m_)
            ratio = best / r
            worst = max(worst, abs(ratio - pred_ratio))
            print(f"   {w:>5.1f} {va:>6.0f} {r:>9.4f} {best:>11.4f} "
                  f"{ratio:>10.6f} {abs(ratio-pred_ratio):>12.2e}")
    ok = worst < 1e-9
    print(f"   -> 最大差 {worst:.2e} -> {'通过（Va 确实生效，且越界量 ∝ Va）' if ok else '不通过'}")
    return ok


def c_cross():
    """(c) 交叉验证：每个 Va 下解析式 vs 数值。"""
    print("")
    print("[三件套 c] 交叉验证：解析式 vs 数值（每个 Va 独立）")
    print(f"   {'Va':>6} {'w':>5} {'psi':>5} {'解析τ':>10} {'数值τ':>10} {'差':>10}")
    worst = 0.0
    n_cmp = 0
    for va in VA_LIST:
        for w in (0.0, 0.1, 0.3, 0.5):
            r, ns, cs, shifts, V_s = shape_for_va(va, w)
            x0 = edge_midpoint(V_s, ns, cs, 0) + 1.0 * r * (-ns[0])
            for psd in (0, 90, 180, 270):
                psi = np.deg2rad(psd)
                ana, _ = tau_crit_analytic_joint(x0, psi, ns, cs, w, r, va=va)
                meas, _ = tau_crit_measured(x0, psi, ns, cs, w, r, va=va)
                if np.isfinite(ana) and np.isfinite(meas):
                    d = abs(ana - meas)
                    worst = max(worst, d)
                    n_cmp += 1
                    if psd in (0, 90) and w == 0.3:
                        print(f"   {va:>6.0f} {w:>5.1f} {psd:>5} {ana:>10.5f} "
                              f"{meas:>10.5f} {d:>10.2e}")
    ok = worst < 1e-3
    print(f"   -> 共 {n_cmp} 组；最大差 {worst:.2e} -> {'通过' if ok else '不通过'}")
    return ok


def main():
    print("=" * 78)
    print("EXP-FW-V1-26 空速扫描：检验 H2（τ_crit 与 Va 无关）")
    print("=" * 78)
    print(f"ω = {np.degrees(OM):.1f}°/s 固定；Va ∈ {VA_LIST} m/s")
    print(f"多边形半宽 = {HALF_R}·R（**无量纲几何固定**，H2 检验的前提）")
    print("")

    ok_n = c_neg()
    ok_p = c_pos()
    ok_c = c_cross()

    print("")
    print("=" * 78)
    print("三件套总判（空速扫描）")
    print("=" * 78)
    all_ok = ok_n and ok_p and ok_c
    print(f"  a 负对照   : {'通过' if ok_n else '不通过'}")
    print(f"  b 正对照   : {'通过' if ok_p else '不通过'}")
    print(f"  c 交叉验证 : {'通过' if ok_c else '不通过'}")
    if not all_ok:
        print("")
        print("  ** 三件套未全过 -> H2 判定不得讨论。**")
        return

    print("")
    print("[H2 判定] 同一 w、同一 φ 下，τ_crit 跨 Va 的变异系数应 < 1e-3")
    print(f"   {'w':>5} {'psi':>5} {'Va=15':>10} {'Va=18':>10} {'Va=25':>10} "
          f"{'均值':>10} {'变异系数':>10}")
    os.makedirs("outputs", exist_ok=True)
    rows = []
    worst_cv = 0.0
    for w in (0.0, 0.1, 0.3, 0.5):
        for psd in (0, 45, 90, 135, 180, 270):
            vals = {}
            for va in VA_LIST:
                r, ns, cs, shifts, V_s = shape_for_va(va, w)
                x0 = edge_midpoint(V_s, ns, cs, 0) + 1.0 * r * (-ns[0])
                t, _ = tau_crit_analytic_joint(x0, np.deg2rad(psd), ns, cs, w, r, va=va)
                vals[va] = t
            arr = np.array([vals[v] for v in VA_LIST], dtype=float)
            if not np.all(np.isfinite(arr)) or np.any(arr <= 0):
                continue
            mean = float(arr.mean())
            cv = float(arr.std(ddof=1) / mean)
            worst_cv = max(worst_cv, cv)
            rows.append({"w": w, "psi_deg": psd,
                         "tau_Va15": vals[15.0], "tau_Va18": vals[18.0],
                         "tau_Va25": vals[25.0], "mean": mean, "cv": cv})
            print(f"   {w:>5.1f} {psd:>5} {vals[15.0]:>10.5f} {vals[18.0]:>10.5f} "
                  f"{vals[25.0]:>10.5f} {mean:>10.5f} {cv:>10.2e}")

    print("")
    print(f"   全部 {len(rows)} 组的最大变异系数 = {worst_cv:.3e}")
    verdict = ("支持（CV < 1e-3）" if worst_cv < 1e-3 else
               "部分支持（CV < 1e-2）" if worst_cv < 1e-2 else "不支持")
    print(f"   -> H2 判定：{verdict}")

    with open("outputs/exp_fw_v1_26_airspeed.csv", "w", newline="",
              encoding="utf-8-sig") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        wr.writeheader()
        wr.writerows(rows)
    print("")
    print(f"wrote outputs/exp_fw_v1_26_airspeed.csv（{len(rows)} 行）")


if __name__ == "__main__":
    main()
