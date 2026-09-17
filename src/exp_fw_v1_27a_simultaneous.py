"""EXP-FW-V1-27A: 多边同时约束复核（v2：机动判据 + 阳性对照）。

预注册：experiments/EXP-FW-V1-27A-preregistration.md
修订 1：experiments/EXP-FW-V1-27A-preregistration-amendment-1.md（位置规定）
首版诊断：experiments/EXP-FW-V1-27A-diagnostic-void-first-run.md（结果作废）

== 前几版的错误（均作废，记录在案）==
v0（作废）：对每条边各自用 τ_e = "首个 v·n_e ≤ 0 的时刻"，把不同轨迹混在一起取 max。
v1（作废）：同一时间网格下的累积最大，但对 T 取最小值时 T=0（不转弯）总是可行，
            判据**平凡通过**（maxV = −R 恒成立）。
v2（作废）：加入"转弯后直飞需 ∀e: n_e·v_g ≤ 0"的可行性条件。该条件对有界多边形
            等价于 v_g = 0（有界凸集的退化锥只有零向量），**永不满足** → 全为 +∞。

== 本版判据（v3）==
机动模型：**持续盘旋**——以最大速率按 sign 连续转弯（有界区域内唯一可持续的运动，
          也正是 δu = 转弯半径所针对的情形）。无 T 参数、无可行性附加条件。
穿透量：  pen_e(sign;ψ0) = max_{t ∈ [0, 一周]} n_e·d_sign(t;ψ0)
          （因 d·n 在首个 v·n=0 之前单调增，故等价于 EXP-21/27 的 τ_e 口径）
越界量：  viol(sign;x0,ψ0) = max_e [ pen_e − room_e(x0) ]
同时充分 ⟺ 对所有 (x0,ψ0)：V = min over sign of viol ≤ 0

== 自检（含阳性对照，缺一不可）==
P1  负对照：直线边界 + 边中点 → 应无违反
P1b 正对照：贴边、朝外 → **必须报违反**（否则判据无检出能力，v1 的教训）
P2  w=0 对齐矩形：given_e 应全为 R
P3  maxV 对 ψ0 网格的收敛性
"""
from __future__ import annotations

import csv
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

VA = 18.0
OMEGA = np.deg2rad(25.0)
R = VA / OMEGA
TURN_PERIOD = 2.0 * np.pi / OMEGA
TWO_PI = 2.0 * np.pi
N_PSI = 3601
N_T = 3601          # 转弯时段的时间网格（[0, 一周]）
EDGE_SAMPLES = 100


def delta_d(w: float) -> float:
    return 0.0 if w <= 0 else R * np.sqrt(1 - w**2) + w * R * np.arccos(-w)


# --------------------------------------------------------------- 多边形工具
def hrep_from_verts(V):
    ns, cs = [], []
    m = len(V)
    for i in range(m):
        a, b = V[i], V[(i + 1) % m]
        e = b - a
        n = np.array([e[1], -e[0]])
        n = n / np.linalg.norm(n)
        ns.append(n)
        cs.append(float(n @ a))
    return np.array(ns), np.array(cs)


def verts_from_hrep(ns, cs, tol=1e-9):
    m = len(ns)
    scale = max(1.0, float(np.abs(cs).max()))
    V = []
    for i in range(m):
        for j in range(i + 1, m):
            A = np.array([ns[i], ns[j]])
            det = A[0, 0] * A[1, 1] - A[0, 1] * A[1, 0]
            if abs(det) < 1e-12:
                continue
            x = np.linalg.solve(A, np.array([cs[i], cs[j]]))
            if np.all(ns @ x <= cs + tol * scale):
                V.append(x)
    if not V:
        return np.zeros((0, 2))
    keep = []
    for x in V:
        if not any(np.linalg.norm(x - y) < 1e-7 * scale for y in keep):
            keep.append(x)
    V = np.array(keep)
    if len(V) < 3:
        return V
    c = V.mean(axis=0)
    return V[np.argsort(np.arctan2(V[:, 1] - c[1], V[:, 0] - c[0]))]


def scaled_geometry(V, w, phi_wind=0.0):
    ns, cs = hrep_from_verts(V)
    d_wind = np.array([np.cos(phi_wind), np.sin(phi_wind)])
    shifts = R + delta_d(w) * np.maximum(0.0, ns @ d_wind)
    return ns, cs, shifts, verts_from_hrep(ns, cs - shifts)


def rectangle(wid, hei, alpha):
    base = np.array([[-wid / 2, -hei / 2], [wid / 2, -hei / 2],
                     [wid / 2, hei / 2], [-wid / 2, hei / 2]])
    ca, sa = np.cos(alpha), np.sin(alpha)
    return base @ np.array([[ca, sa], [-sa, ca]])


def regular_ngon(n, alpha=0.0, radius=212.13):
    a = np.linspace(0, TWO_PI, n, endpoint=False) + alpha
    return radius * np.stack([np.cos(a), np.sin(a)], axis=-1)


def normalize_radius(V, target=212.13):
    c = V.mean(axis=0)
    Vc = V - c
    return Vc * (target / max(1e-12, np.max(np.linalg.norm(Vc, axis=1))))


# --------------------------------------------------------------- 核心
_T_GRID = None


def t_grid():
    global _T_GRID
    if _T_GRID is None or len(_T_GRID) != N_T:
        _T_GRID = np.linspace(0.0, TURN_PERIOD, N_T)
    return _T_GRID


def t_grid_with_crit(psi0, sign, phi_e, w):
    """均匀网格 + 各边 v·n_e = 0 的**精确**时刻。

    最大值必在 v·n_e = 0 处取得（此前 d·n 单调增），
    故把临界时刻插入网格可使 max 精确（消除离散化误差）。
    注意：这是**同一条**轨迹上的采样点（不存在轨迹混用）。
    """
    t = t_grid()
    crit = []
    for phi in phi_e:
        A = np.arccos(np.clip(-w * np.cos(phi), -1.0, 1.0))   # v·n=0 时 psi−φ = ±A
        for sgn in (+1.0, -1.0):
            target = phi + sgn * A
            # psi0 + sign*omega*t = target (mod 2π)
            dpsi = (target - psi0) * sign
            k = np.arange(-2, 3)
            tc = (dpsi + TWO_PI * k) / OMEGA
            crit.extend([x for x in tc if -1e-12 <= x <= TURN_PERIOD + 1e-12])
    if crit:
        t = np.unique(np.concatenate([t, np.clip(np.array(crit), 0.0, TURN_PERIOD)]))
    return t


def V_of_psi0(psi0, sign, ns, cs, x0s, w):
    """返回每个 x0 的 viol（**持续盘旋**模型，无 T 参数，临界时刻精确）。

    轨迹：以最大速率按 sign 连续转弯一整个周期。
    pen_e = max over t of n_e·d(t)，t 含各边临界时刻 → 与 EXP-21/27 的 τ_e 口径一致。
    """
    phi_e = np.arctan2(ns[:, 1], ns[:, 0])
    t = t_grid_with_crit(psi0, sign, phi_e, w)
    wx, wy = w * VA, 0.0
    psi = psi0 + sign * OMEGA * t
    d = np.stack([sign * R * (np.sin(psi) - np.sin(psi0)) + wx * t,
                  -sign * R * (np.cos(psi) - np.cos(psi0)) + wy * t], axis=-1)  # (T,2)
    g = d @ ns.T                                     # (T,E)
    pen = np.max(g, axis=0)                          # (E,) 整周期最大穿透（精确）
    room = cs[None, :] - x0s @ ns.T                  # (X,E)
    return np.max(pen[None, :] - room, axis=1)       # (X,)


def evaluate_positions(V, w, positions, psi_extra_deg=()):
    ns, cs, shifts, V_s = scaled_geometry(V, w)
    if len(V_s) < 3:
        return None
    base = np.linspace(0.0, TWO_PI, N_PSI, endpoint=False)
    psi0s = np.concatenate([base, np.deg2rad(np.asarray(psi_extra_deg, float))]) \
        if len(psi_extra_deg) else base

    maxV = -np.inf
    argmax = None
    n_pos = 0
    n_tot = 0
    n_infeasible = 0
    for psi0 in psi0s:
        best = np.minimum(V_of_psi0(psi0, +1, ns, cs, positions, w),
                          V_of_psi0(psi0, -1, ns, cs, positions, w))
        j = int(np.argmax(best))
        if best[j] > maxV:
            maxV = float(best[j])
            argmax = (positions[j].copy(), float(psi0), float(best[j]))
        n_pos += int(np.sum(best > 1e-9))
        n_tot += len(best)
        n_infeasible += int(np.sum(~np.isfinite(best)))
    return {"maxV": maxV, "argmax": argmax, "n_pos": n_pos, "n_tot": n_tot,
            "n_infeasible": n_infeasible, "n_edges": len(ns),
            "given_min": float(shifts.min()), "given_max": float(shifts.max())}


def vertex_directions(V, x0):
    d = V - x0
    return np.degrees(np.arctan2(d[:, 1], d[:, 0]))


# --------------------------------------------------------------- 自检
def check_negative_control(w=0.3):
    """P1 负对照：直线边界 + 缩放层边中点 → 应无违反。"""
    print("[P1 负对照] 直线边界（大矩形），位置=缩放层边中点")
    V = rectangle(4000.0, 4000.0, 0.0)
    _, _, _, V_s = scaled_geometry(V, w)
    mids = np.array([(V_s[i] + V_s[(i + 1) % len(V_s)]) / 2 for i in range(len(V_s))])
    res = evaluate_positions(V, w, mids)
    ok = res["maxV"] <= 1e-9
    print(f"   maxV = {res['maxV']:.6e} m → {'通过（无违反）' if ok else '不通过'}")
    return res["maxV"]


def check_positive_control(w=0.3, dists=(1.0, 5.0, 20.0, 41.25, 60.0, 82.5, 120.0, 200.0)):
    """P1b 正对照：**离边界距离扫描**。

    持续盘旋模型下，飞机总是转圈，因此"朝外"不构成违反；
    真正出事的是**离边界太近、转弯圆盘放不下**。
    故用距边界不同距离的直线边界场景扫描，应出现一个阈值：
    距离小 → 违反（正）；距离大 → 无违反（负）。
    """
    print("\n[P1b 正对照] 直线边界 + 距边界距离扫描（应出现阈值）")
    V = rectangle(4000.0, 4000.0, 0.0)        # 右边界：n≈(1,0)，c≈2000
    ns, cs, shifts, _ = scaled_geometry(V, w)
    # 找出沿 +x 方向的边（n·(1,0) 最大者）
    i = int(np.argmax(ns @ np.array([1.0, 0.0])))
    n_e, c_e = ns[i], cs[i]
    print(f"   取边 i={i}：n=({n_e[0]:.4f},{n_e[1]:.4f})，c={c_e:.2f}，"
          f"该边 given={shifts[i]:.4f} m")
    print(f"   {'距边界 d(m)':>12} {'room(m)':>10} {'maxV(m)':>12} {'判定':>10}")
    results = []
    for d in dists:
        x0 = (c_e - d) * n_e
        res = evaluate_positions(V, w, x0[None, :])
        v = res["maxV"]
        results.append((d, v))
        verdict = "违反" if v > 1e-9 else "无违反"
        print(f"   {d:>12.2f} {d:>10.2f} {v:>12.4f} {verdict:>10}")
    n_pos = sum(1 for _, v in results if v > 1e-9)
    n_neg = sum(1 for _, v in results if v <= 1e-9)
    ok = n_pos >= 1 and n_neg >= 1
    print(f"   → {'通过（同时检出违反与不违反，判据有区分能力）' if ok else '不通过'}")
    return results


def check_w0_rectangle():
    print("\n[P2] w=0 对齐矩形：given_e 应全为 R")
    ns, cs, shifts, _ = scaled_geometry(rectangle(300.0, 300.0, 0.0), 0.0)
    dev = float(np.max(np.abs(shifts - R)))
    print(f"   given_e = {np.round(shifts, 6)}；偏差 = {dev:.3e} → "
          f"{'通过' if dev < 1e-6 else '不通过'}")
    return dev


def check_convergence(V, w, positions, n_list=(901, 1801, 3601, 7201)):
    print("\n[P3] maxV 对 ψ0 网格的收敛性")
    global N_PSI
    old = N_PSI
    out = []
    for n in n_list:
        N_PSI = n
        out.append(evaluate_positions(V, w, positions)["maxV"])
    N_PSI = old
    for n, v in zip(n_list, out):
        print(f"   N_PSI={n:>5}: maxV = {v:.9f}")
    drift = abs(out[-1] - out[-2])
    print(f"   最密两档之差 = {drift:.3e} → {'稳定' if drift < 1e-6 else '未收敛'}")
    return out, drift


def main():
    os.makedirs("outputs", exist_ok=True)
    os.makedirs("outputs/figures", exist_ok=True)
    print("=" * 78)
    print("EXP-FW-V1-27A：多边同时约束复核（v2：机动判据 + 阳性对照）")
    print("=" * 78)
    print(f"\nVa={VA} m/s，ω=25°/s，R={R:.4f} m，一周 {TURN_PERIOD:.3f} s\n")

    m1 = check_negative_control(0.3)
    m1b_out, m1b_in = check_positive_control(0.3)
    m2 = check_w0_rectangle()

    # ---- 构型 ----
    configs = []
    for ar in (1.0, 2.0, 3.0):
        for a in np.arange(0.0, 45.0 + 1e-9, 5.0):
            configs.append((f"rect_ar{ar:g}",
                            normalize_radius(rectangle(300.0 * ar, 300.0, np.deg2rad(a)))))
    for n in range(3, 9):
        for a in np.arange(0.0, 45.0 + 1e-9, 15.0):
            configs.append((f"ngon{n}", normalize_radius(regular_ngon(n, np.deg2rad(a)))))

    Vc = normalize_radius(rectangle(300.0, 300.0, 0.0))
    _, _, _, Vs_c = scaled_geometry(Vc, 0.3)
    _, drift = check_convergence(Vc, 0.3, Vs_c)

    print("\n" + "=" * 78)
    print("主扫描：位置 = 缩放层顶点，ψ0 含指向顶点的航向")
    print("=" * 78)
    rows = []
    for w in (0.0, 0.1, 0.3, 0.5):
        worst = None
        for name, V in configs:
            ns, cs, shifts, V_s = scaled_geometry(V, w)
            extra = []
            for x0 in V_s:
                extra.extend(vertex_directions(V, x0))
            res = evaluate_positions(V, w, V_s, extra)
            if res is None:
                continue
            rows.append({"polygon": name, "w": w, "maxV": res["maxV"],
                         "n_pos": res["n_pos"], "n_tot": res["n_tot"],
                         "n_infeasible": res["n_infeasible"], "n_edges": res["n_edges"]})
            if worst is None or res["maxV"] > worst[1]:
                worst = (name, res["maxV"], res)
        print(f"\n  w = {w}：{len(configs)} 构型")
        print(f"    最差 {worst[0]}：maxV = {worst[1]:.6f} m；"
              f"正违反 {worst[2]['n_pos']}/{worst[2]['n_tot']}；"
              f"无可行机动 {worst[2]['n_infeasible']}")
        if worst[2]["argmax"]:
            x0, psi, v = worst[2]["argmax"]
            print(f"    argmax：x0=({x0[0]:.3f},{x0[1]:.3f})，ψ0={np.degrees(psi):.2f}°，V={v:.4f}")

    print("\n" + "=" * 78)
    print("判据")
    print("=" * 78)
    print(f"P1  负对照（直线边界）：maxV = {m1:.3e} → {'通过' if m1 <= 1e-9 else '不通过'}")
    print(f"P1b 正对照（贴边朝外）：maxV = {m1b_out:.4f} → "
          f"{'通过' if m1b_out > 1e-9 else '不通过（判据失效）'}")
    print(f"     朝内对照：maxV = {m1b_in:.4f}（应 ≤ 0）")
    print(f"P2  w=0 矩形 given_e 偏差 = {m2:.3e} → {'通过' if m2 < 1e-6 else '不通过'}")
    print(f"P3  收敛性 = {drift:.3e} → {'稳定' if drift < 1e-6 else '未收敛'}")
    maxV = max(r["maxV"] for r in rows)
    wr = max(rows, key=lambda r: r["maxV"])
    print(f"P4  全局 maxV = {maxV:.6f} m（{wr['polygon']}, w={wr['w']}）")
    if maxV <= 1e-9:
        print("    → **H-A 成立**：逐边 ⇒ 同时（几何基准可靠，EXP-26 可照原设计）")
    else:
        print("    → **H-B 成立**：存在同时违反；逐边判据不足")
    n_v = sum(1 for r in rows if r["maxV"] > 1e-9)
    print(f"P5  几何定位：maxV > 0 的构型 = {n_v}/{len(rows)}")

    with open("outputs/exp_fw_v1_27a_simultaneous.csv", "w", newline="",
              encoding="utf-8-sig") as f:
        wr2 = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        wr2.writeheader()
        wr2.writerows(rows)
    print(f"\nwrote outputs/exp_fw_v1_27a_simultaneous.csv（{len(rows)} 行）")

    fig, ax = plt.subplots(1, 2, figsize=(12.5, 4.8))
    for w in (0.0, 0.1, 0.3, 0.5):
        sub = sorted([r for r in rows if r["w"] == w], key=lambda r: r["maxV"])
        ax[0].plot(np.arange(len(sub)), [r["maxV"] for r in sub], "o-", ms=3, label=f"w={w}")
    ax[0].axhline(0, color="k", lw=0.8)
    ax[0].set_xlabel("configurations (sorted)"); ax[0].set_ylabel("maxV (m)")
    ax[0].set_title("simultaneous violation (positive ⇒ H-B)")
    ax[0].grid(alpha=0.3); ax[0].legend(fontsize=8)
    ws = [0.0, 0.1, 0.3, 0.5]
    for k, mk in (("rect", "s-"), ("ngon", "^-")):
        ys = [max([r["maxV"] for r in rows if r["w"] == w and r["polygon"].startswith(k)]
                  or [0.0]) for w in ws]
        ax[1].plot(ws, ys, mk, ms=4, label=f"{k} (max)")
    ax[1].axhline(0, color="k", lw=0.8)
    ax[1].set_xlabel("wind ratio w"); ax[1].set_ylabel("maxV (m)")
    ax[1].set_title("violation vs wind"); ax[1].grid(alpha=0.3); ax[1].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig("outputs/figures/exp_fw_v1_27a_simultaneous.png", dpi=160)
    print("wrote outputs/figures/exp_fw_v1_27a_simultaneous.png")


if __name__ == "__main__":
    main()
