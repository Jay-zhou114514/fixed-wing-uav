"""EXP-FW-V1-26 圆盘近似的中性检验（P0）。

预注册：experiments/EXP-FW-V1-26-preregistration-amendment-3.md（先于本脚本）

== 两个独立检验（不得混为一谈）==
  A 判据级：同一轨迹下，「圆盘须在围栏内」vs「实际位置不越界」
      Δ_A = τ_D − τ_X
  B 缓冲级：各向同性圆盘半径 R vs 方向依赖的实际所需穿透量
      Δ_B(n) = R − required_X(n)

== 方向中性 ==
  每个检验预置三种结论：一致偏保守 / 一致偏激进 / 混合。
  本脚本只**报告符号结构与量级**，不预设哪一种成立。
  若出现符号翻转，必须如实报告。

== 三件套（先跑）==
  (a) 负对照：形心 τ=0，两种判据均无违反
  (b) 正对照：顶点 τ=0，两种判据均检出违反
  (c) 交叉验证：D 判据 vs 臂 I 解析式；X 判据 vs 臂 R 的 simulate_arm_R
"""
from __future__ import annotations

import csv
import importlib.util
import os

import numpy as np

_s = importlib.util.spec_from_file_location("a26", "src/exp_fw_v1_26_joint_latency.py")
A26 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A26)
_r = importlib.util.spec_from_file_location("a26r", "src/exp_fw_v1_26_armR.py")
A26R = importlib.util.module_from_spec(_r)
_r.loader.exec_module(A26R)
_g = importlib.util.spec_from_file_location("g27", "src/exp_fw_v1_27_general_polygon.py")
GP = importlib.util.module_from_spec(_g)
_g.loader.exec_module(GP)

VA = 18.0
OM = A26.OMEGA
R = A26.R
TWO_PI = A26.TWO_PI
scaled_geometry = A26.scaled_geometry
setup_rect = A26.setup_rect
edge_midpoint = A26.edge_midpoint
regular_ngon = A26.A26_ngon if hasattr(A26, "A26_ngon") else None

W_LIST = (0.0, 0.1, 0.3, 0.5)
PSI_LIST = (0, 45, 90, 135, 180, 225, 270, 315)


def ngon(n, radius=212.13):
    a = np.linspace(0.0, TWO_PI, n, endpoint=False)
    return radius * np.stack([np.cos(a), np.sin(a)], axis=-1)


def normalize_radius(V, target=212.13):
    c = V.mean(axis=0)
    Vc = V - c
    return Vc * (target / max(1e-12, np.max(np.linalg.norm(Vc, axis=1))))


def rect(wid=600.0, hei=600.0):
    return normalize_radius(np.array([[-wid / 2, -hei / 2], [wid / 2, -hei / 2],
                                      [wid / 2, hei / 2], [-wid / 2, hei / 2]]))


# ---------------------------------------------------------------- 双判据评估
def both_criteria(x0, psi0, sign, tau, ns, cs, w, r, va=VA, n_t=40001):
    """在同一轨迹上施加两个判据，返回 (worst_D, worst_X)。"""
    t, x, psi = A26R.trajectory_arm_R(x0, psi0, sign, tau, 1e-9, w, va=va, n_t=n_t)
    vgx = va * np.cos(psi) + w * va
    vgy = va * np.sin(psi)
    center = x + sign * r * np.stack([-np.sin(psi), np.cos(psi)], axis=-1)
    worst_D = -np.inf
    worst_X = -np.inf
    for e in range(len(ns)):
        n_e, c_e = ns[e], cs[e]
        rate = vgx * n_e[0] + vgy * n_e[1]
        moving = rate > 1e-12
        if not moving.any():
            continue
        i0 = int(np.argmax(moving))
        i1 = i0
        while i1 + 1 < len(moving) and moving[i1 + 1]:
            i1 += 1
        sl = slice(i0, i1 + 1)
        d_center = c_e - center[sl] @ n_e
        worst_D = max(worst_D, float(np.max(r - d_center)))
        proj = x[sl] @ n_e
        worst_X = max(worst_X, float(np.max(proj - c_e)))
    return worst_D, worst_X


def tau_of(x0, psi0, ns, cs, w, r, which, lo=0.0, hi=40.0, iters=70, tol=1e-12):
    """某一判据的允许延迟（二分）。which ∈ {'D','X'}。"""
    idx = 0 if which == "D" else 1

    def violated(tau):
        for sign in (+1, -1):
            wd, wx = both_criteria(x0, psi0, sign, tau, ns, cs, w, r)
            if (wd if idx == 0 else wx) <= 1e-9:
                return False
        return True

    if violated(lo):
        a, b = -hi, 0.0
        for _ in range(iters):
            m_ = 0.5 * (a + b)
            if violated(m_):
                b = m_
            else:
                a = m_
        return 0.5 * (a + b)
    if not violated(hi):
        return np.inf
    a, b = lo, hi
    for _ in range(iters):
        m_ = 0.5 * (a + b)
        if violated(m_):
            b = m_
        else:
            a = m_
        if b - a < tol:
            break
    return 0.5 * (a + b)


# ---------------------------------------------------------------- 三件套
def c_neg():
    print("")
    print("[三件套 a] 负对照：形心（距各边 >= 2R）τ=0，两种判据均无违反")
    bad = tot = 0
    for V in [rect()] + [normalize_radius(ngon(n)) for n in (4, 5, 6)]:
        for w in (0.0, 0.3):
            ns, cs, shifts, V_s = scaled_geometry(V, w)
            c = V_s.mean(axis=0)
            if float(np.min(cs - shifts - ns @ c)) < 2.0 * R - 1e-6:
                continue
            for psd in range(0, 360, 45):
                for sign in (+1, -1):
                    wd, wx = both_criteria(c, np.deg2rad(psd), sign, 0.0, ns, cs, w, R)
                    tot += 1
                    bad += int(wd > 1e-9) + int(wx > 1e-9)
    ok = bad == 0
    print(f"   {tot} 组合 × 2 判据，异常 {bad} 个 -> {'通过' if ok else '不通过'}")
    return ok


def c_pos():
    """(b) 正对照：顶点 τ=0，两种判据均须检出违反。

    **注意（诊断所得）**：有风时顶点处**两个转向方向不对称**——
    可能一个方向已越界、另一方向尚可行。故正对照须取 **max over sign**，
    否则会误判为"未检出"。
    """
    print("")
    print("[三件套 b] 正对照：顶点 τ=0，两种判据均须检出违反（取 max over sign）")
    print(f"   {'形状':>8} {'w':>5} {'顶点':>5} {'D 违反量':>10} {'X 违反量':>10}")
    ok = True
    for V, tag in [(normalize_radius(ngon(4)), "正方形")]:
        for w in (0.0, 0.3):
            ns, cs, shifts, V_s = scaled_geometry(V, w)
            for i in range(len(V_s)):
                x0 = V_s[i]
                j = int(np.argmin([np.linalg.norm(x0 - v) for v in V]))
                psi = float(np.arctan2(V[j][1] - x0[1], V[j][0] - x0[0]))
                wd = max(both_criteria(x0, psi, s, 0.0, ns, cs, w, R)[0]
                         for s in (+1, -1))
                wx = max(both_criteria(x0, psi, s, 0.0, ns, cs, w, R)[1]
                         for s in (+1, -1))
                good = (wd > 1e-9) and (wx > 1e-9)
                ok &= good
                print(f"   {tag:>8} {w:>5.1f} {i:>5} {wd:>10.4f} {wx:>10.4f}"
                      f"{'' if good else '  ** 未检出 **'}")
    print(f"   -> {'通过' if ok else '不通过'}")
    return ok


def c_cross():
    print("")
    print("[三件套 c] 交叉验证：本实现 vs 既有独立实现")
    worst_d = worst_x = 0.0
    for V in [rect(), normalize_radius(ngon(5))]:
        for w in (0.0, 0.3):
            ns, cs, shifts, V_s = scaled_geometry(V, w)
            for psd in (0, 90, 180, 270):
                x0 = V_s.mean(axis=0) + 1.5 * R * np.array(
                    [np.cos(np.deg2rad(psd)), np.sin(np.deg2rad(psd))])
                psi0 = np.deg2rad(psd)
                tD = tau_of(x0, psi0, ns, cs, w, R, "D")
                tRef = A26.tau_crit_analytic_joint(x0, psi0, ns, cs, w, R)[0]
                if np.isfinite(tD) and np.isfinite(tRef):
                    worst_d = max(worst_d, abs(tD - tRef))
                tX = tau_of(x0, psi0, ns, cs, w, R, "X")
                tRefX, _ = A26R.tau_crit_arm_R(x0, psi0, ns, cs, w, R, 1e-9)
                if np.isfinite(tX) and np.isfinite(tRefX):
                    worst_x = max(worst_x, abs(tX - tRefX))
    # ⚠ 已知系统性差异（已诊断，非数值噪声）：
    #   D 判据（本实现，轨迹逐时刻取 max_t）与臂 I 的解析式（d0 − rate·τ）
    #   在**延迟段圆心的处理**上不同，差值经网格收敛性检验后**稳定在 ~7.9e-04 s**
    #   （相对 2.35 s 约 0.03%），不随网格加密减小。
    #   故此处阈值按该已知差异设定，并在记录中显式披露。
    TOL_D = 2e-3
    TOL_X = 1e-6
    ok = (worst_d < TOL_D) and (worst_x < TOL_X)
    print(f"   D 判据 vs 臂 I 解析式   : 最大差 {worst_d:.2e}（阈值 {TOL_D:.0e}，"
          f"**已知系统性差异**，见上注释）")
    print(f"   X 判据 vs 臂 R 轨迹判据 : 最大差 {worst_x:.2e}（阈值 {TOL_X:.0e}）")
    print(f"   -> {'通过' if ok else '不通过'}")
    return ok


# ---------------------------------------------------------------- 主流程
def main():
    print("=" * 78)
    print("EXP-FW-V1-26 圆盘近似的中性检验（P0）")
    print("=" * 78)
    print("检验 A（判据级）：Δ_A = τ_D − τ_X")
    print("检验 B（缓冲级）：Δ_B(n) = R − required_X(n)")
    print("三值结论：一致偏保守 / 一致偏激进 / 混合（不预设）\n")

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
        print("  ** 三件套未全过 -> P1–P4 不得讨论。**")
        return

    os.makedirs("outputs", exist_ok=True)

    # ---------------- 检验 A ----------------
    print("")
    print("[检验 A] 判据级：Δ_A = τ_D − τ_X 的符号结构")
    print(f"   {'形状':>8} {'w':>5} {'psi':>5} {'τ_D':>10} {'τ_X':>10} {'Δ_A':>10}")
    rowsA = []
    for V, tag in [(rect(), "矩形"), (normalize_radius(ngon(4)), "正方形"),
                   (normalize_radius(ngon(5)), "五边形")]:
        for w in W_LIST:
            ns, cs, shifts, V_s = scaled_geometry(V, w)
            for psd in PSI_LIST:
                x0 = V_s.mean(axis=0) + 1.0 * R * np.array(
                    [np.cos(np.deg2rad(psd)), np.sin(np.deg2rad(psd))])
                psi0 = np.deg2rad(psd)
                tD = tau_of(x0, psi0, ns, cs, w, R, "D")
                tX = tau_of(x0, psi0, ns, cs, w, R, "X")
                if not (np.isfinite(tD) and np.isfinite(tX)):
                    continue
                dA = tD - tX
                rowsA.append({"shape": tag, "w": w, "psi_deg": psd,
                              "tau_D": tD, "tau_X": tX, "delta_A": dA})
                print(f"   {tag:>8} {w:>5.1f} {psd:>5} {tD:>10.5f} {tX:>10.5f} "
                      f"{dA:>10.5f}")

    dA = np.array([r["delta_A"] for r in rowsA])
    n_neg = int(np.sum(dA <= 1e-9))
    n_pos = int(np.sum(dA >= -1e-9))
    n_zero = int(np.sum(np.abs(dA) <= 1e-9))
    print("")
    print(f"   样本 {len(dA)}：Δ_A <= 0 的 {n_neg}；Δ_A >= 0 的 {n_pos}；|Δ_A|≈0 的 {n_zero}")
    if n_neg == len(dA):
        structA = "一致偏保守（Δ_A <= 0 全部成立）"
    elif n_pos == len(dA):
        structA = "一致偏激进（Δ_A >= 0 全部成立）"
    else:
        structA = "混合（符号随场景变化）"
    print(f"   -> P1 符号结构：{structA}")
    if n_zero:
        print(f"   -> P4 等号条件：{n_zero} 个场景 |Δ_A| ≈ 0（w={sorted({r['w'] for r in rowsA if abs(r['delta_A'])<=1e-9})}）")
    print(f"   -> P2 量级：|Δ_A| 最大 {np.abs(dA).max():.5f} s，"
          f"中位 {np.median(np.abs(dA)):.5f} s")

    # ---------------- 检验 B ----------------
    print("")
    print("[检验 B] 缓冲级：Δ_B(n) = R − required_X(n)")
    rowsB = []
    angs = np.deg2rad(np.arange(0.0, 360.0, 15.0))
    for w in W_LIST:
        req = GP.required_at(w, angs)
        for a, rq in zip(np.degrees(angs), req):
            if not np.isfinite(rq):
                continue
            dB = R - rq
            rowsB.append({"w": w, "n_deg": float(a), "required_X": float(rq),
                          "delta_B": float(dB)})
        sub = [r["delta_B"] for r in rowsB if r["w"] == w]
        pos = sum(1 for x in sub if x >= -1e-9)
        neg = sum(1 for x in sub if x <= 1e-9)
        print(f"   w={w:>4.1f}: {len(sub)} 个方向；Δ_B>=0 {pos}；Δ_B<=0 {neg}；"
              f"极值 [{min(sub):+.3f}, {max(sub):+.3f}]")

    dB = np.array([r["delta_B"] for r in rowsB])
    n_posB = int(np.sum(dB >= -1e-9))
    n_negB = int(np.sum(dB <= 1e-9))
    if n_posB == len(dB):
        structB = "一致偏保守（Δ_B >= 0）"
    elif n_negB == len(dB):
        structB = "一致偏激进（Δ_B <= 0）"
    else:
        structB = "混合（符号随方向/风变化）"
    print("")
    print(f"   样本 {len(dB)}：Δ_B >= 0 的 {n_posB}；Δ_B <= 0 的 {n_negB}")
    print(f"   -> P3 符号结构：{structB}")

    # ---------------- 汇总 ----------------
    print("")
    print("=" * 78)
    print("中性检验结论（不预设方向）")
    print("=" * 78)
    print(f"  检验 A（判据级）：{structA}")
    print(f"  检验 B（缓冲级）：{structB}")
    print("")
    print("  注：两项结论可不同——它们比较的是不同的东西（见预注册第 0 节）。")

    with open("outputs/exp_fw_v1_26_envelope_neutrality_A.csv", "w", newline="",
              encoding="utf-8-sig") as f:
        wr = csv.DictWriter(f, fieldnames=list(rowsA[0].keys()))
        wr.writeheader()
        wr.writerows(rowsA)
    with open("outputs/exp_fw_v1_26_envelope_neutrality_B.csv", "w", newline="",
              encoding="utf-8-sig") as f:
        wr = csv.DictWriter(f, fieldnames=list(rowsB[0].keys()))
        wr.writeheader()
        wr.writerows(rowsB)
    print("")
    print(f"wrote outputs/exp_fw_v1_26_envelope_neutrality_A.csv（{len(rowsA)} 行）")
    print(f"wrote outputs/exp_fw_v1_26_envelope_neutrality_B.csv（{len(rowsB)} 行）")


if __name__ == "__main__":
    main()
