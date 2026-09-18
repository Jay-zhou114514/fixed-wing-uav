"""EXP-FW-V1-26 独立验证：临界距离闭式 d* = R·cot(θ/2)（C 区，独立样本）。

预注册：experiments/EXP-FW-V1-26-preregistration-amendment-2.md（先于本脚本）
目的：C 区扫描的公式属**事后识别**（辨识与确认同源），须在**独立样本**上做预测检验。

== 冻结的预测 ==
  w = 0 时 d* = R·cot(θ/2)，且 d* **只**由 θ 与 R 决定（与边长、其他顶点、整体形状无关）

== 独立样本（不得使用 n = 3,4,5,6）==
  T-A 新 θ：规则多边形 n = 7,8,9,10,12,16
  T-B 新形状：楔形三角，顶点角 θ ∈ {70,90,110,130}°，射线长 L ∈ {10R,20R,40R}
              —— 检验"θ 充分性"（同 θ 不同 L 应给同一 d*/R）

== 三件套（先跑）==
  (a) 负对照：深内部（距各边 >= 2R）τ=0 无越界
  (b) 正对照：d=0 处 τ_crit<0，且扫描须找到符号变化
  (c) 交叉验证：解析 vs 数值二分（τ >= 0 区间）
"""
from __future__ import annotations

import csv
import importlib.util
import os

import numpy as np

_s = importlib.util.spec_from_file_location("a26", "src/exp_fw_v1_26_joint_latency.py")
A26 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A26)

_c = importlib.util.spec_from_file_location("cd", "src/exp_fw_v1_26_critical_distance.py")
CD = importlib.util.module_from_spec(_c)
_c.loader.exec_module(CD)

OM = A26.OMEGA
TWO_PI = A26.TWO_PI
VA = 18.0
R = VA / OM
tau_crit_analytic_joint = A26.tau_crit_analytic_joint
tau_crit_measured = A26.tau_crit_measured
simulate_arm_I = A26.simulate_arm_I
find_zero = CD.find_zero

N_NEW = (7, 8, 9, 10, 12, 16)          # 新 θ
THETA_WEDGE = (70.0, 90.0, 110.0, 130.0)
L_FACTORS = (10.0, 20.0, 40.0)


# ---------------------------------------------------------------- 楔形三角
def wedge_scaled(theta_deg, L, w=0.0, va=VA):
    """楔形三角（顶点角 = theta）的缩放层顶点与半平面表示。

    半平面： n1=(-s,c), c1=0 ; n2=(-s,-c), c2=0 ; n3=(1,0), c3=L
    顶点角位于原点；缩放层顶点的 x 坐标 = R/sin(theta/2)。
    """
    r = va / OM
    th = np.deg2rad(theta_deg)
    s, c = np.sin(th / 2.0), np.cos(th / 2.0)
    ns = np.array([[-s, c], [-s, -c], [1.0, 0.0]])
    cs = np.array([0.0, 0.0, L])
    d_wind = np.array([1.0, 0.0])
    dd = 0.0 if w <= 0 else r * (np.sqrt(1 - w ** 2) + w * np.arccos(-w))
    shifts = r + dd * np.maximum(0.0, ns @ d_wind)
    cs_s = cs - shifts
    apex = np.linalg.solve(np.array([ns[0], ns[1]]), np.array([cs_s[0], cs_s[1]]))
    return r, ns, cs, shifts, apex


def poly_max_clearance(ns, cs_s):
    """缩放层内离各边的最大最小距离（近似用缩放层顶点与形心）。"""
    V_s = A26.verts_from_hrep(ns, cs_s)
    if len(V_s) < 3:
        return 0.0
    cand = [V_s.mean(axis=0)] + [p for p in V_s]
    best = -np.inf
    for p in cand:
        best = max(best, float(np.min(cs_s - ns @ p)))
    return best


# ---------------------------------------------------------------- 采样 d*
def dstar_for_vertex(xv, u_in, u_out, ns, cs, w=0.0, va=VA, dmax_factor=3.0, k=241):
    r = va / OM
    psi0 = float(np.arctan2(u_out[1], u_out[0]))
    ds = np.linspace(0.0, dmax_factor * r, k)
    taus = np.array([tau_crit_analytic_joint(xv + d * u_in, psi0, ns, cs, w, r,
                                             va=va)[0] for d in ds])
    return find_zero(ds, taus), ds, taus, psi0


# ---------------------------------------------------------------- 三件套
def c_neg():
    print("")
    print("[三件套 a] 负对照：深内部（距各边 >= 2R）τ=0 应无越界")
    bad = tot = 0
    for n in (7, 8, 10, 12, 16):
        S = CD.setup(n, 0.0, VA)
        c = S["V_s"].mean(axis=0)
        clr = float(np.min(S["cs_s"] - S["ns"] @ c))
        if clr < 2.0 * S["r"] - 1e-6:
            print(f"   [跳过] n={n}：形心净空 {clr:.2f} < 2R")
            continue
        for psd in range(0, 360, 45):
            for sign in (+1, -1):
                _, vi = simulate_arm_I(c, np.deg2rad(psd), sign, 0.0,
                                       S["ns"], S["cs"], 0.0, S["r"], va=VA)
                tot += 1
                bad += int(vi)
    for thd in THETA_WEDGE:
        r, ns, cs, shifts, apex = wedge_scaled(thd, 20.0 * R)
        cs_s = cs - shifts
        clr = poly_max_clearance(ns, cs_s)
        if clr < 2.0 * r - 1e-6:
            print(f"   [跳过] 楔形 θ={thd}：净空 {clr:.2f} < 2R")
            continue
        x0 = apex + 2.5 * r * np.array([1.0, 0.0])
        for psd in range(0, 360, 60):
            for sign in (+1, -1):
                _, vi = simulate_arm_I(x0, np.deg2rad(psd), sign, 0.0,
                                       ns, cs, 0.0, r, va=VA)
                tot += 1
                bad += int(vi)
    ok = bad == 0
    print(f"   {tot} 组合，越界 {bad} 个 -> {'通过' if ok else '不通过'}")
    return ok


def c_pos():
    print("")
    print("[三件套 b] 正对照：d=0 处 τ_crit<0，且须找到符号变化")
    print(f"   {'样本':>16} {'τ(d=0)':>10} {'d* 存在':>8}")
    ok = True
    for n in N_NEW:
        S = CD.setup(n, 0.0, VA)
        t0 = S["taus"][0]
        dz = find_zero(S["ds"], S["taus"])
        good = np.isfinite(t0) and t0 < 0 and dz is not None
        ok &= good
        print(f"   {'规则 n=%d' % n:>16} {t0:>10.5f} {str(dz is not None):>8}")
    for thd in THETA_WEDGE:
        r, ns, cs, shifts, apex = wedge_scaled(thd, 20.0 * R)
        dz, ds, taus, _ = dstar_for_vertex(apex, np.array([1.0, 0.0]),
                                           np.array([-1.0, 0.0]), ns, cs)
        good = np.isfinite(taus[0]) and taus[0] < 0 and dz is not None
        ok &= good
        print(f"   {'楔形 θ=%.0f' % thd:>16} {taus[0]:>10.5f} {str(dz is not None):>8}")
    print(f"   -> {'通过' if ok else '不通过'}")
    return ok


def c_cross():
    print("")
    print("[三件套 c] 交叉验证：解析 vs 数值（τ >= 0 区间）")
    worst = 0.0
    for n in (8, 12):
        S = CD.setup(n, 0.0, VA)
        r = S["r"]
        for dk in (1.0, 1.5, 2.0):
            x0 = S["xv"] + dk * r * S["u_in"]
            ana = tau_crit_analytic_joint(x0, S["psi0"], S["ns"], S["cs"], 0.0, r, va=VA)[0]
            if ana < -1e-9:
                continue
            meas, _ = tau_crit_measured(x0, S["psi0"], S["ns"], S["cs"], 0.0, r, va=VA)
            if np.isfinite(ana) and np.isfinite(meas):
                worst = max(worst, abs(ana - meas))
    ok = worst < 1e-3
    print(f"   最大差 = {worst:.2e} -> {'通过' if ok else '不通过'}")
    return ok


def main():
    print("=" * 78)
    print("EXP-FW-V1-26 独立验证：d* = R·cot(θ/2)（独立样本）")
    print("=" * 78)
    print(f"预注册：amendment-2（先于本脚本）")
    print(f"独立样本：规则 n={N_NEW}（新 θ）；楔形 θ={THETA_WEDGE}（新形状）")
    print(f"R = {R:.6f} m\n")

    ok_n = c_neg()
    ok_p = c_pos()
    ok_c = c_cross()

    print("")
    print("=" * 78)
    print("三件套总判")
    print("=" * 78)
    all_ok = ok_n and ok_p and ok_c
    print(f"  a 负对照   : {'通过' if ok_n else '不通过'}")
    print(f"  b 正对照   : {'通过' if ok_p else '不通过'}")
    print(f"  c 交叉验证 : {'通过' if ok_c else '不通过'}")
    if not all_ok:
        print("")
        print("  ** 三件套未全过 -> P1/P2/P3 不得讨论。**")
        return

    os.makedirs("outputs", exist_ok=True)
    rows = []

    print("")
    print("[P1] T-A：新 θ（规则多边形），d*/R ?= cot(θ/2)")
    print(f"   {'n':>4} {'θ(deg)':>9} {'d*(m)':>10} {'d*/R':>10} {'cot(θ/2)':>10} {'差':>10}")
    worst_a = 0.0
    for n in N_NEW:
        S = CD.setup(n, 0.0, VA)
        th = 180.0 - 360.0 / n
        dz = find_zero(S["ds"], S["taus"])
        pred = 1.0 / np.tan(np.deg2rad(th / 2.0))
        ratio = dz / S["r"]
        d_ = abs(ratio - pred)
        worst_a = max(worst_a, d_)
        rows.append({"test": "T-A", "n": n, "theta_deg": th, "L": np.nan,
                     "d_star_m": dz, "ratio": ratio, "pred": pred, "dev": d_})
        print(f"   {n:>4} {th:>9.3f} {dz:>10.4f} {ratio:>10.6f} {pred:>10.6f} {d_:>10.2e}")
    print(f"   -> 最大偏差 {worst_a:.2e} -> {'通过' if worst_a < 1e-6 else '不通过'}")

    print("")
    print("[P2/P3] T-B：楔形三角（同 θ 不同 L）")
    print(f"   {'θ(deg)':>8} {'L/R':>6} {'d*(m)':>10} {'d*/R':>10} {'cot(θ/2)':>10} {'差':>10}")
    worst_b = 0.0
    spread_max = 0.0
    for thd in THETA_WEDGE:
        ratios = []
        for Lf in L_FACTORS:
            r, ns, cs, shifts, apex = wedge_scaled(thd, Lf * R)
            dz, ds, taus, _ = dstar_for_vertex(apex, np.array([1.0, 0.0]),
                                               np.array([-1.0, 0.0]), ns, cs)
            if dz is None:
                continue
            ratio = dz / r
            ratios.append(ratio)
            pred = 1.0 / np.tan(np.deg2rad(thd / 2.0))
            d_ = abs(ratio - pred)
            worst_b = max(worst_b, d_)
            rows.append({"test": "T-B", "n": np.nan, "theta_deg": thd, "L": Lf,
                         "d_star_m": dz, "ratio": ratio, "pred": pred, "dev": d_})
            print(f"   {thd:>8.1f} {Lf:>6.0f} {dz:>10.4f} {ratio:>10.6f} "
                  f"{pred:>10.6f} {d_:>10.2e}")
        if ratios:
            spread_max = max(spread_max, max(ratios) - min(ratios))
    print(f"   -> P2 最大偏差 {worst_b:.2e} -> {'通过' if worst_b < 1e-6 else '不通过'}")
    print(f"   -> P3 跨 L 极差（最大） {spread_max:.2e} -> "
          f"{'通过' if spread_max < 1e-6 else '不通过'}")

    print("")
    print("=" * 78)
    print("独立验证结论")
    print("=" * 78)
    p1 = worst_a < 1e-6
    p2 = worst_b < 1e-6
    p3 = spread_max < 1e-6
    print(f"  P1（新 θ 满足闭式）        : {'通过' if p1 else '不通过'}")
    print(f"  P2（楔形顶点满足闭式）      : {'通过' if p2 else '不通过'}")
    print(f"  P3（d* 对 L 不敏感）        : {'通过' if p3 else '不通过'}")
    if p1 and p2 and p3:
        print("")
        print("  ** 闭式在独立样本上通过预测检验；")
        print("     'd* 只由 θ 与 R 决定' 得到支持（T-B 换形状仍成立）。**")
    else:
        print("")
        print("  ** 未通过 -> 原表述必须降级（公式不成立或需限定）。**")

    with open("outputs/exp_fw_v1_26_independent_dstar.csv", "w", newline="",
              encoding="utf-8-sig") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        wr.writeheader()
        wr.writerows(rows)
    print("")
    print(f"wrote outputs/exp_fw_v1_26_independent_dstar.csv（{len(rows)} 行）")


if __name__ == "__main__":
    main()
