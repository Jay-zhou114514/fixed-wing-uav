"""EXP-FW-V1-26 C 区扫描：临界距离 d*（判据 P7）。

预注册：experiments/EXP-FW-V1-26-preregistration.md 判据 P7
依据：V2.3 的 H1 形式（`τ_crit = min_e [min(d0,d_turn) − R]/rate`）

== P7 要检验的结构 ==
存在临界距离 d*，使   d < d*: τ_crit < 0  且   d > d*: τ_crit > 0
（把"三区"从经验划分变为数学分类）

**前置条件（本脚本先查）**：τ_crit(d) 必须在 d 上**单调**
——否则"d<d* 负 / d>d* 正"的二分结构不成立。

== 理论预言（本脚本要证伪或确认）==
取**沿分角线向内**的参数化，航向 = 朝分角线外（最不利）。
设 s 为自缩放层顶点的向内距离。顶点处两相邻边的法线与分角线夹角为 θ/2，故

  n_e·b_out = sin(θ/2)   （b_out 为向外分角线单位向量）
  n_e·perp(ψ0) = cos(θ/2)（ψ0 沿 b_out）
  d_e(center) − R = s·sin(θ/2) − sign·R·cos(θ/2)
  rate_e = n_e·v_g = Va·sin(θ/2) + w·Va·(n_e·e_wind)

⟹ τ_crit(s) = [ s·sin(θ/2) − sign·R·cos(θ/2) ] / rate_e

设 τ_crit(s) = 0 ⟹ s = R·cot(θ/2)

> **预言：d* = R·cot(θ/2) = R / tan(θ/2)**
> （w=0 时精确；w>0 时因几何偏移与速率改变而偏离）

**首次预言勘误**：本文件初版曾预言 `d* = R`（误用 `n_e·b = cos(θ/2)`），
与实测在 θ≠90° 时不符；正确式为上式。

== 三件套（FROZEN_PROTOCOL 12.1，先跑）==
(a) 负对照：d = 2R（深内部）→ τ=0 时无越界，且 τ_crit > 0
(b) 正对照：d = 0（顶点）→ τ_crit < 0；且扫描须**找到符号变化**（否则无 d*）
(c) 交叉验证：解析式 vs 数值二分（多个 d）
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
scaled_geometry = A26.scaled_geometry
tau_crit_analytic_joint = A26.tau_crit_analytic_joint
tau_crit_measured = A26.tau_crit_measured
simulate_arm_I = A26.simulate_arm_I

VA_LIST = (15.0, 18.0, 25.0)
N_LIST = (3, 4, 5, 6)
W_LIST = (0.0, 0.1, 0.3, 0.5)


def regular_ngon(n, radius=212.13, alpha=0.0):
    a = np.linspace(0.0, TWO_PI, n, endpoint=False) + alpha
    return radius * np.stack([np.cos(a), np.sin(a)], axis=-1)


def vertex_frame(ns, cs_s, xv, tol=1e-6):
    """返回 (向内分角线, 向外分角线, 相邻边索引)。

    **注意**：`verts_from_hrep` 会**按极角重排**顶点，故 `V_s[j]` 与 `ns[e]`
    的索引**不对应**。相邻边必须按"哪些半平面约束在顶点处取紧"来判定：
        |c'_e − n_e·x_v| ≈ 0  的 e 即相邻边。
    （同族错误此前已犯过两次：EXP-27 顶点配对、corner-law 复核配对。）
    """
    m = len(ns)
    adj = [e for e in range(m) if abs(cs_s[e] - ns[e] @ xv) < tol]
    if len(adj) < 2:
        raise ValueError(f"顶点处未找到两条紧约束（找到 {len(adj)} 条）")
    adj = adj[:2]
    b_out = ns[adj[0]] + ns[adj[1]]
    b_out = b_out / np.linalg.norm(b_out)
    return -b_out, b_out, adj


def setup(n, w, va, j=0, dmax_factor=3.0, k=121):
    r = va / OM
    V = regular_ngon(n)
    ns, cs, shifts, V_s = scaled_geometry(V, w, va=va)
    cs_s = cs - shifts
    xv = V_s[j]
    u_in, u_out, adj = vertex_frame(ns, cs_s, xv)
    psi0 = float(np.arctan2(u_out[1], u_out[0]))     # 朝分角线外（最不利）
    ds = np.linspace(0.0, dmax_factor * r, k)
    taus = np.array([tau_crit_analytic_joint(xv + d * u_in, psi0, ns, cs, w, r,
                                             va=va)[0] for d in ds])
    return dict(r=r, ns=ns, cs=cs, cs_s=cs_s, shifts=shifts, V_s=V_s, xv=xv,
                u_in=u_in, u_out=u_out, adj=adj, psi0=psi0, ds=ds, taus=taus,
                n=n, w=w, va=va)


def find_zero(ds, taus):
    """找 τ_crit 的首个上升零交点（线性插值）。"""
    for i in range(len(ds) - 1):
        t0, t1 = taus[i], taus[i + 1]
        if np.isfinite(t0) and np.isfinite(t1) and t0 <= 0 < t1:
            return float(ds[i] + (0 - t0) * (ds[i + 1] - ds[i]) / (t1 - t0))
    return None


def is_monotone_increasing(taus, tol=1e-9):
    """在 τ_crit < 0 的区段之后是否单调不减（允许起点无穷）。"""
    finite = np.isfinite(taus)
    t = taus[finite]
    if len(t) < 2:
        return True
    return bool(np.all(np.diff(t) >= -tol))


# ---------------------------------------------------------------- 三件套
def c_neg():
    """(a) 负对照：形心（距各边 >= 2R，圆盘任何朝向都放得下）应无越界。

    **限制 n >= 4**：对正三角形，缩放层内半径 = 1.57R < 2R，
    故**不存在**任何位置/朝向使半径 R 的圆盘完全在围栏内（几何事实），
    三角形不能用作负对照。该事实本身已记录。
    """
    print("")
    print("[三件套 a] 负对照：形心（n>=4，距各边 >= 2R）应无越界")
    bad = tot = 0
    for n in (4, 5, 6):
        for w in (0.0, 0.3):
            for va in VA_LIST:
                S = setup(n, w, va)
                r = S["r"]
                c = S["V_s"].mean(axis=0)
                dmin = float(np.min(S["cs_s"] - S["ns"] @ c))
                if dmin < 2.0 * r - 1e-6:
                    print(f"   [跳过] n={n} w={w} Va={va}：形心距边 {dmin:.3f} < 2R")
                    continue
                for psd in range(0, 360, 45):
                    for sign in (+1, -1):
                        _, vi = simulate_arm_I(c, np.deg2rad(psd), sign, 0.0,
                                               S["ns"], S["cs"], w, r, va=va)
                        tot += 1
                        bad += int(vi)
    ok = bad == 0
    print(f"   {tot} 组合，越界 {bad} 个 -> {'通过' if ok else '不通过'}")
    return ok


def c_pos():
    """(b) 正对照：d=0 处 τ_crit<0，且扫描须找到符号变化。"""
    print("")
    print("[三件套 b] 正对照：d=0（顶点）τ_crit < 0；且 d 扫描须找到符号变化")
    print(f"   {'n':>3} {'w':>5} {'Va':>5} {'τ(d=0)':>10} {'d* 存在':>9} {'d*/R':>9}")
    ok = True
    n_found = 0
    for n in N_LIST:
        for w in W_LIST:
            for va in (18.0,):
                S = setup(n, w, va)
                t0 = S["taus"][0]
                dz = find_zero(S["ds"], S["taus"])
                good = (np.isfinite(t0) and t0 < 0) and (dz is not None)
                ok &= good
                if dz is not None:
                    n_found += 1
                print(f"   {n:>3} {w:>5.1f} {va:>5.0f} {t0:>10.5f} "
                      f"{str(dz is not None):>9} "
                      f"{(dz/S['r'] if dz else float('nan')):>9.4f}")
    print(f"   -> d* 找到 {n_found} 组；{'通过' if ok else '不通过'}")
    return ok


def c_cross():
    """(c) 交叉验证：解析 vs 数值二分（多个 d）。"""
    print("")
    print("[三件套 c] 交叉验证：解析式 vs 数值二分")
    print(f"   {'n':>3} {'w':>5} {'d/R':>6} {'解析τ':>10} {'数值τ':>10} {'差':>10}")
    worst = 0.0
    for n in (4, 6):
        for w in (0.0, 0.3):
            S = setup(n, w, 18.0)
            r = S["r"]
            for dk in (0.0, 0.5, 1.0, 1.5, 2.0):
                x0 = S["xv"] + dk * r * S["u_in"]
                ana = tau_crit_analytic_joint(x0, S["psi0"], S["ns"], S["cs"],
                                              w, r, va=18.0)[0]
                meas, _ = tau_crit_measured(x0, S["psi0"], S["ns"], S["cs"],
                                            w, r, va=18.0)
                # 负 τ 区间：数值二分的下界为人工值（−30），不构成有效比较
                if ana < -1e-9:
                    continue
                if np.isfinite(ana) and np.isfinite(meas):
                    d = abs(ana - meas)
                    worst = max(worst, d)
                    print(f"   {n:>3} {w:>5.1f} {dk:>6.1f} {ana:>10.5f} "
                          f"{meas:>10.5f} {d:>10.2e}")
    ok = worst < 1e-3
    print(f"   -> 最大差 {worst:.2e} -> {'通过' if ok else '不通过'}"
          f"（仅比较 τ_crit >= 0 的区间；负区间数值法受人工下界限制）")
    return ok


def main():
    print("=" * 78)
    print("EXP-FW-V1-26 C 区扫描：临界距离 d*（判据 P7）")
    print("=" * 78)
    print(f"参数化：沿**向内分角线**自缩放层顶点；航向 = 朝分角线外（最不利）")
    print(f"预言（见文件头推导）：d* = R，与 θ、w、Va 无关 ⟹ d*/R ≡ 1")
    print("")

    ok_n = c_neg()
    ok_p = c_pos()
    ok_c = c_cross()

    print("")
    print("=" * 78)
    print("三件套总判（C 区）")
    print("=" * 78)
    all_ok = ok_n and ok_p and ok_c
    print(f"  a 负对照   : {'通过' if ok_n else '不通过'}")
    print(f"  b 正对照   : {'通过' if ok_p else '不通过'}")
    print(f"  c 交叉验证 : {'通过' if ok_c else '不通过'}")
    if not all_ok:
        print("")
        print("  ** 三件套未全过 -> P7 判定不得讨论。**")
        return

    print("")
    print("[单调性检查] τ_crit(d) 在 d 上是否单调（P7 二分结构的前提）")
    mono_all = True
    for n in N_LIST:
        for w in W_LIST:
            S = setup(n, w, 18.0)
            mono = is_monotone_increasing(S["taus"])
            mono_all &= mono
            if not mono:
                print(f"   ** 非单调：n={n}, w={w}")
    print(f"   -> {'全部单调' if mono_all else '存在非单调（P7 结构需修正）'}")

    print("")
    print("[P7 判定] d*/R ?= cot(θ/2)（跨 θ、w、Va）")
    print(f"   {'n':>3} {'θ(deg)':>7} {'w':>5} {'Va':>5} {'d*(m)':>9} {'d*/R':>9} "
          f"{'cot(θ/2)':>10} {'差':>10}")
    os.makedirs("outputs", exist_ok=True)
    rows = []
    ratios = []
    for n in N_LIST:
        th = 180.0 - 360.0 / n
        for w in W_LIST:
            for va in VA_LIST:
                S = setup(n, w, va)
                dz = find_zero(S["ds"], S["taus"])
                if dz is None:
                    continue
                ratio = dz / S["r"]
                ratios.append(ratio)
                rows.append({"n": n, "theta_deg": th, "w": w, "va": va,
                             "d_star_m": dz, "R_m": S["r"], "ratio": ratio})
                if va == 18.0:
                    print(f"   {n:>3} {th:>7.1f} {w:>5.1f} {va:>5.0f} {dz:>9.4f} "
                          f"{S['r']:>9.4f} {ratio:>9.6f}")
    ratios = np.array([r["ratio"] for r in rows])
    preds = np.array([1.0 / np.tan(np.deg2rad(r["theta_deg"] / 2.0)) for r in rows])
    ws = np.array([r["w"] for r in rows])
    dev = np.abs(ratios - preds)
    dev_w0 = float(np.max(dev[np.isclose(ws, 0.0)])) if np.any(np.isclose(ws, 0.0)) else float("nan")
    dev_wnz = float(np.max(dev[~np.isclose(ws, 0.0)])) if np.any(~np.isclose(ws, 0.0)) else float("nan")
    print("")
    print(f"   共 {len(ratios)} 组")
    print(f"   w=0    组：与 cot(θ/2) 最大偏差 = {dev_w0:.3e}")
    print(f"   w>0    组：与 cot(θ/2) 最大偏差 = {dev_wnz:.3e}")
    if dev_w0 < 1e-6:
        print("   -> **P7 成立且给出闭式：d* = R·cot(θ/2)（w=0 精确）**")
        print("      w>0 时 d* 偏离该式（因几何偏移与速率改变），属已知依赖")
    else:
        print(f"   -> 预言与实测不符（w=0 偏差 {dev_w0:.2e}）")

    with open("outputs/exp_fw_v1_26_critical_distance.csv", "w", newline="",
              encoding="utf-8-sig") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        wr.writeheader()
        wr.writerows(rows)
    print("")
    print(f"wrote outputs/exp_fw_v1_26_critical_distance.csv（{len(rows)} 行）")


if __name__ == "__main__":
    main()
