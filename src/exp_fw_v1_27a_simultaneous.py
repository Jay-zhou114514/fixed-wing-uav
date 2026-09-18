"""EXP-FW-V1-27A: 多边同时约束复核（v4：修正 τ + 三件套）。

预注册：experiments/EXP-FW-V1-27A-preregistration.md
修订 1：experiments/EXP-FW-V1-27A-preregistration-amendment-1.md（位置规定）
失败诊断：experiments/EXP-FW-V1-27A-failure-diagnosis.md（四次失败 + τ bug）

== 核心问题 ==
EXP-27 的逐边充分性，是否蕴含多边同时充分性？

  逐边（EXP-27 口径）：**每条边各自**可选最优转弯方向 sign
      ALL_PER_EDGE(x0,ψ0) ⇔ ∀e: min_sign [ pen_e(sign;ψ0) − room_e(x0) ] ≤ 0
  同时（闭环要求）：**单一** sign 须满足所有边
      SIMUL(x0,ψ0) ⇔ min_sign max_e [ pen_e(sign;ψ0) − room_e(x0) ] ≤ 0

若逐边全过但同时不过 → **H-B 成立**（EXP-27 的逐边判据不足）。

== τ 口径（复用，不重写）==
从 notes/verify_tau_fix.py 导入 tau_fixed（模式 A），并做交叉验证。
本脚本内的向量化实现 pen_vec 必须与 tau_fixed 逐点一致（三件套之 c）。

== 三件套（先跑，再跑主扫描）==
(a) 负对照：直线边界 + 边中点 → maxV ≤ 0
(b) 正对照：距边界距离扫描 → 须同时出现"违反"与"不违反"
(c) 交叉验证：pen_vec vs tau_fixed（标量 golden）vs EXP-27 required_at
"""
from __future__ import annotations

import csv
import importlib.util
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# ---------------------------------------------------------------- 载入 golden τ
_s = importlib.util.spec_from_file_location("tv", "notes/verify_tau_fix.py")
_TAU = importlib.util.module_from_spec(_s)
_s.loader.exec_module(_TAU)

VA = _TAU.VA
OM = _TAU.OM
R = _TAU.R
TWO_PI = _TAU.TWO_PI
delta_d = _TAU.delta_d if hasattr(_TAU, "delta_d") else (
    lambda w: 0.0 if w <= 0 else R * np.sqrt(1 - w**2) + w * R * np.arccos(-w))
N_PSI = 3601
GRAZE_TOL = _TAU.GRAZE_TOL


def delta_d_(w):
    return 0.0 if w <= 0 else R * np.sqrt(1 - w**2) + w * R * np.arccos(-w)


def _first_pos(x):
    r = np.mod(x, TWO_PI)
    return np.where(r > 1e-13, r, TWO_PI)


# ---------------------------------------------------------------- 向量化 pen
def pen_vec(psi0s, sign, w, phi_e):
    """pen[psi0, e]：修正 τ 口径下的首次外摆穿透（向量化）。

    与 _TAU.tau_fixed 的标量逻辑一致（由三件套 c 交叉验证）。
    """
    psi0s = np.atleast_1d(psi0s)[:, None]           # (P,1)
    phi = np.asarray(phi_e)[None, :]                # (1,E)
    # v(0)·n_e
    vn0 = (VA * np.cos(psi0s) + w * VA) * np.cos(phi) + VA * np.sin(psi0s) * np.sin(phi)
    backward = vn0 < -GRAZE_TOL                     # (P,E)
    A = np.arccos(np.clip(-w * np.cos(phi), -1.0, 1.0))     # (1,E)
    th0 = psi0s - phi                                        # (P,E)
    if sign > 0:
        tau_ang = np.minimum(_first_pos(A - th0), _first_pos(-A - th0))
    else:
        tau_ang = np.minimum(_first_pos(th0 + A), _first_pos(th0 - A))
    t = tau_ang / OM
    psi = psi0s + sign * OM * t
    dx = sign * R * (np.sin(psi) - np.sin(psi0s)) + w * VA * t
    dy = -sign * R * (np.cos(psi) - np.cos(psi0s))
    pen = dx * np.cos(phi) + dy * np.sin(phi)
    return np.where(backward, 0.0, pen)             # t=0 已后退 → 穿透 0


# ---------------------------------------------------------------- 多边形工具
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
    shifts = R + delta_d_(w) * np.maximum(0.0, ns @ d_wind)
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


# ---------------------------------------------------------------- 核心评估
def core_V(psi0s, ns, cs, positions, w):
    """返回 (P,X)：同时条件的违逆量 V(ψ0, x0) = min_sign max_e [pen_e − room_e]。"""
    phi_e = np.arctan2(ns[:, 1], ns[:, 0])
    psi0s = np.atleast_1d(psi0s)
    pen_p = pen_vec(psi0s, +1, w, phi_e)          # (P,E)
    pen_m = pen_vec(psi0s, -1, w, phi_e)
    if pen_p.ndim == 1:                            # 单点情形
        pen_p = pen_p[None, :]
        pen_m = pen_m[None, :]
    room = cs[None, :] - positions @ ns.T          # (X,E)
    vp = np.max(pen_p[:, None, :] - room[None, :, :], axis=2)   # (P,X)
    vm = np.max(pen_m[:, None, :] - room[None, :, :], axis=2)
    return np.minimum(vp, vm)


def core_per_edge(psi0s, ns, cs, positions, w):
    """逐边口径（EXP-27）：允许每条边各选最优 sign。返回 (P,X,E)。"""
    phi_e = np.arctan2(ns[:, 1], ns[:, 0])
    psi0s = np.atleast_1d(psi0s)
    pen_p = pen_vec(psi0s, +1, w, phi_e)
    pen_m = pen_vec(psi0s, -1, w, phi_e)
    if pen_p.ndim == 1:
        pen_p = pen_p[None, :]
        pen_m = pen_m[None, :]
    room = cs[None, :] - positions @ ns.T
    return np.minimum(pen_p[:, None, :] - room[None, :, :],
                      pen_m[:, None, :] - room[None, :, :])


def refine_max_psi(core_fn, psi0s, g, args, k=6, rounds=6, pts=81):
    """局部精化 max_psi0 f(psi0)：网格粗搜 → 取 top-k 候选 → 逐轮收缩。

    必要性：max-over-ψ0 的极值点在折点处（min_sign 的尖点），
    均匀网格收敛慢（O(1/N)，实测 N=200001 仍有 5e-4），
    不精化无法满足判据 P4 的 1e-9 阈值。

    注：core_fn 可能返回 (P,X)（同时口径）或 (P,X,E)（逐边口径），
    故对最后一维之后的所有维取 max 得到每个 ψ0 的标量。
    """
    def to_psi_profile(arr):
        a = np.asarray(arr)
        if a.ndim == 1:
            return a
        return a.reshape(a.shape[0], -1).max(axis=1)

    width = float(psi0s[1] - psi0s[0])
    cands = list(np.atleast_1d(psi0s[np.argsort(g)[-k:]]))
    best = float(np.max(g))
    for _ in range(rounds):
        new = []
        for c in cands:
            loc = c + np.linspace(-width, width, pts)
            gi = to_psi_profile(core_fn(loc, *args))
            j = int(np.argmax(gi))
            best = max(best, float(gi[j]))
            new.append(loc[j])
        cands = new
        width /= (pts // 2)
    return best


def evaluate(V, w, positions, psi_extra_deg=(), refine=True):
    ns, cs, shifts, V_s = scaled_geometry(V, w)
    if len(V_s) < 3:
        return None
    base = np.linspace(0.0, TWO_PI, N_PSI, endpoint=False)
    psi0s = np.concatenate([base, np.deg2rad(np.asarray(psi_extra_deg, float))]) \
        if len(psi_extra_deg) else base

    Vm = core_V(psi0s, ns, cs, positions, w)                # (P,X)
    Pe = core_per_edge(psi0s, ns, cs, positions, w)         # (P,X,E)
    nX = Vm.shape[1]

    Pe_worst = Pe.max(axis=2)                               # (P,X) 逐边最差
    g_sim = Vm.max(axis=1)                                  # (P,)
    g_per = Pe_worst.max(axis=1)                            # (P,)
    maxV_sim = float(g_sim.max())
    maxV_per = float(g_per.max())
    if refine:
        maxV_sim = refine_max_psi(core_V, psi0s, g_sim, (ns, cs, positions, w))
        maxV_per = refine_max_psi(core_per_edge, psi0s, g_per, (ns, cs, positions, w))

    both = (Pe_worst <= 1e-9) & (Vm > 1e-9)                 # (P,X)
    n_p6 = int(np.sum(both))
    p6_example = None
    if n_p6:
        p, x = np.argwhere(both)[0]
        p6_example = (positions[x].copy(), float(psi0s[p]), float(Vm[p, x]))
    return {"maxV_sim": maxV_sim, "maxV_per": maxV_per,
            "n_p6": n_p6, "p6_example": p6_example,
            "n_pos_sim": int(np.sum(Vm > 1e-9)), "n_tot": int(Vm.size),
            "n_edges": len(ns), "n_verts_scaled": len(V_s)}


def vertex_directions(V, x0):
    d = V - x0
    return np.degrees(np.arctan2(d[:, 1], d[:, 0]))


# ---------------------------------------------------------------- 三件套
def c1_negative(w=0.3):
    print("[三件套 a] 负对照：直线边界（大矩形）+ 缩放层边中点 → 应无违反")
    V = rectangle(4000.0, 4000.0, 0.0)
    _, _, _, V_s = scaled_geometry(V, w)
    mids = np.array([(V_s[i] + V_s[(i + 1) % len(V_s)]) / 2 for i in range(len(V_s))])
    res = evaluate(V, w, mids)
    ok = res["maxV_sim"] <= 1e-9
    print(f"   maxV_sim={res['maxV_sim']:.3e}  maxV_per={res['maxV_per']:.3e} "
          f"→ {'通过' if ok else '不通过'}")
    return res, ok


def c2_positive(w=0.3, dists=(1.0, 20.0, 41.25, 55.0, 62.56, 70.0, 90.0, 150.0)):
    print("\n[三件套 b] 正对照：距边界距离扫描 → 须同时出现'违反'与'不违反'")
    V = rectangle(4000.0, 4000.0, 0.0)
    ns, cs, shifts, _ = scaled_geometry(V, w)
    i = int(np.argmax(ns @ np.array([1.0, 0.0])))
    n_e, c_e = ns[i], cs[i]
    print(f"   边 i={i}：given={shifts[i]:.4f} m")
    print(f"   {'d(m)':>9} {'maxV_sim':>12} {'判定':>8}")
    out = []
    for d in dists:
        x0 = ((c_e - d) * n_e)[None, :]
        res = evaluate(V, w, x0)
        v = res["maxV_sim"]
        out.append((d, v))
        print(f"   {d:>9.2f} {v:>12.4f} {'违反' if v > 1e-9 else '安全':>8}")
    n_pos = sum(1 for _, v in out if v > 1e-9)
    n_neg = sum(1 for _, v in out if v <= 1e-9)
    ok = n_pos >= 1 and n_neg >= 1
    print(f"   → {'通过（有区分能力）' if ok else '不通过'}")
    return out, ok


def _g_single(psi0s, w, phi):
    """单方向辅助：返回 (P,1) 以复用 refine_max_psi。"""
    pv = pen_vec(psi0s, +1, w, np.array([phi]))[:, 0]
    pm = pen_vec(psi0s, -1, w, np.array([phi]))[:, 0]
    return np.minimum(pv, pm)[:, None]


def c3_crossvalidate(w_list=(0.1, 0.3), n_probe=120, seed=20260918):
    print("\n[三件套 c] 交叉验证：向量化 pen_vec vs golden tau_fixed vs EXP-27")
    rng = np.random.default_rng(seed)
    worst_g = 0.0
    for w in w_list:
        for _ in range(n_probe):
            phi = rng.uniform(0, TWO_PI)
            psi0 = rng.uniform(0, TWO_PI)
            if abs(_TAU.vdotn0(psi0, w, phi)) < 1e-6:
                continue
            for sign in (+1, -1):
                g, _, _ = _TAU.tau_fixed(psi0, sign, w, phi)
                v = pen_vec(np.array([psi0]), sign, w, np.array([phi]))[0, 0]
                worst_g = max(worst_g, abs(g - v))
    print(f"   vs golden tau_fixed：最大差 = {worst_g:.3e} m → "
          f"{'一致' if worst_g < 1e-9 else '不一致'}")

    _s2 = importlib.util.spec_from_file_location("gp", "src/exp_fw_v1_27_general_polygon.py")
    GP = importlib.util.module_from_spec(_s2)
    _s2.loader.exec_module(GP)
    worst_r = 0.0
    print(f"   {'w':>5} {'n(deg)':>7} {'EXP-27':>12} {'本实现(精化)':>14} {'差':>10}")
    for w in (0.0, 0.1, 0.3, 0.5):
        for nd in (0, 45, 90, 135, 180, 270):
            ph = np.deg2rad(nd)
            ref = GP.required_at(w, np.array([ph]))[0]
            grid = np.linspace(0.0, TWO_PI, 721, endpoint=False)
            est = refine_max_psi(_g_single, grid, _g_single(grid, w, ph).max(axis=1),
                                 (w, ph))
            d = abs(est - ref)
            worst_r = max(worst_r, d)
            if d > 1e-9:
                print(f"   {w:>5.1f} {nd:>7} {ref:>12.6f} {est:>14.6f} {d:>10.2e}  <-- 超差")
    print(f"   vs EXP-27 required_at：最大差 = {worst_r:.3e} m → "
          f"{'一致（机器精度）' if worst_r < 1e-9 else '不一致'}")
    return worst_g, worst_r


def c4_convergence(V, w, positions, n_list=(451, 901, 1801, 3601)):
    """收敛性：**精化后**结果应对网格密度不敏感（粗网格+精化 = 同一值）。"""
    print("\n[三件套 补充] 精化后 maxV_sim 对 ψ0 网格的鲁棒性")
    global N_PSI
    old = N_PSI
    vals = []
    for n in n_list:
        N_PSI = n
        vals.append(evaluate(V, w, positions)["maxV_sim"])
    N_PSI = old
    for n, v in zip(n_list, vals):
        print(f"   N_PSI={n:>5}: {v:.9f}")
    spread = max(vals) - min(vals)
    print(f"   跨网格极差 = {spread:.3e} → {'稳定' if spread < 1e-6 else '未收敛'}")
    return spread


# ---------------------------------------------------------------- 主流程
def main():
    os.makedirs("outputs", exist_ok=True)
    os.makedirs("outputs/figures", exist_ok=True)
    print("=" * 78)
    print("EXP-FW-V1-27A：多边同时约束复核（v4）")
    print("=" * 78)
    print(f"\nVa={VA} m/s，ω=25°/s，R={R:.4f} m；ψ0 网格 {N_PSI}\n")

    res_neg, ok_a = c1_negative(0.3)
    res_pos, ok_b = c2_positive(0.3)
    wg, wr = c3_crossvalidate()
    Vc = normalize_radius(rectangle(300.0, 300.0, 0.0))
    _, _, _, Vs_c = scaled_geometry(Vc, 0.3)
    drift = c4_convergence(Vc, 0.3, Vs_c)

    print("\n" + "=" * 78)
    print("三件套总判")
    print("=" * 78)
    all_ok = ok_a and ok_b and (wg < 1e-9) and (wr < 1e-9) and (drift < 1e-6)
    print(f"  a 负对照     : {'通过' if ok_a else '不通过'}")
    print(f"  b 正对照     : {'通过' if ok_b else '不通过'}")
    print(f"  c 交叉验证   : golden {wg:.1e} / EXP-27 {wr:.1e} → "
          f"{'通过' if (wg < 1e-9 and wr < 1e-9) else '不通过'}")
    print(f"    收敛性     : {drift:.1e} → {'通过' if drift < 1e-6 else '不通过'}")
    if not all_ok:
        print("\n  ** 三件套未全部通过 → 主扫描结果不得讨论。**")
        return

    # ---------------- 主扫描 ----------------
    configs = []
    for ar in (1.0, 2.0, 3.0):
        for a in np.arange(0.0, 45.0 + 1e-9, 5.0):
            configs.append((f"rect_ar{ar:g}",
                            normalize_radius(rectangle(300.0 * ar, 300.0, np.deg2rad(a)))))
    for n in range(3, 9):
        for a in np.arange(0.0, 45.0 + 1e-9, 15.0):
            configs.append((f"ngon{n}", normalize_radius(regular_ngon(n, np.deg2rad(a)))))

    print("\n" + "=" * 78)
    print("主扫描：位置 = 缩放层顶点，ψ0 含指向顶点的航向")
    print("=" * 78)
    rows = []
    for w in (0.0, 0.1, 0.3, 0.5):
        worst = None
        for name, V in configs:
            _, _, _, V_s = scaled_geometry(V, w)
            extra = []
            for x0 in V_s:
                extra.extend(vertex_directions(V, x0))
            res = evaluate(V, w, V_s, extra)
            if res is None:
                continue
            rows.append({"polygon": name, "w": w,
                         "maxV_sim": res["maxV_sim"],
                         "maxV_per": res["maxV_per"],
                         "n_p6": res["n_p6"],
                         "n_pos_sim": res["n_pos_sim"],
                         "n_tot": res["n_tot"],
                         "n_edges": res["n_edges"]})
            if worst is None or res["maxV_sim"] > worst[1]:
                worst = (name, res["maxV_sim"], res)
        print(f"\n  w = {w}：{len(configs)} 构型")
        print(f"    最差 {worst[0]}：maxV_sim = {worst[1]:.6f} m；"
              f"逐边 maxV_per = {worst[2]['maxV_per']:.6f} m")
        print(f"    同时违反位置 {worst[2]['n_pos_sim']}/{worst[2]['n_tot']}；"
              f"P6（逐边过但同时不过）计数 = {worst[2]['n_p6']}")
        if worst[2]["p6_example"]:
            x0, psi, v = worst[2]["p6_example"]
            print(f"    P6 例：x0=({x0[0]:.2f},{x0[1]:.2f})，ψ0={np.degrees(psi):.2f}°，"
                  f"同时违反 = {v:.4f} m")

    print("\n" + "=" * 78)
    print("判据")
    print("=" * 78)
    maxV_sim = max(r["maxV_sim"] for r in rows)
    maxV_per = max(r["maxV_per"] for r in rows)
    wr_ = max(rows, key=lambda r: r["maxV_sim"])
    n_p6_tot = sum(r["n_p6"] for r in rows)
    print(f"P1/P1b/P2/P3（三件套）: 全部通过")
    print(f"P4 判定：全局 maxV_sim = {maxV_sim:.6f} m"
          f"（{wr_['polygon']}, w={wr_['w']}）")
    print(f"   （对照：逐边口径 maxV_per = {maxV_per:.6f} m）")
    if maxV_sim <= 1e-9:
        print("   → **H-A 成立**：逐边 ⇒ 同时；几何基准可靠")
    else:
        print("   → **H-B 成立**：存在同时违反；EXP-27 的逐边判据不足")
    print(f"P5 几何定位：maxV_sim > 0 的构型 = "
          f"{sum(1 for r in rows if r['maxV_sim'] > 1e-9)}/{len(rows)}")
    print(f"P6 对照：逐边全通过但同时违反的 (x0,ψ0) 组合总数 = {n_p6_tot}")

    with open("outputs/exp_fw_v1_27a_simultaneous.csv", "w", newline="",
              encoding="utf-8-sig") as f:
        wr2 = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        wr2.writeheader()
        wr2.writerows(rows)
    print(f"\nwrote outputs/exp_fw_v1_27a_simultaneous.csv（{len(rows)} 行）")

    fig, ax = plt.subplots(1, 2, figsize=(12.5, 4.8))
    for w in (0.0, 0.1, 0.3, 0.5):
        sub = sorted([r for r in rows if r["w"] == w], key=lambda r: r["maxV_sim"])
        ax[0].plot(np.arange(len(sub)), [r["maxV_sim"] for r in sub], "o-", ms=3, label=f"w={w}")
    ax[0].axhline(0, color="k", lw=0.8)
    ax[0].set_xlabel("configurations (sorted)"); ax[0].set_ylabel("maxV_sim (m)")
    ax[0].set_title("simultaneous violation (positive ⇒ H-B)")
    ax[0].grid(alpha=0.3); ax[0].legend(fontsize=8)
    ws = [0.0, 0.1, 0.3, 0.5]
    for k, mk in (("rect", "s-"), ("ngon", "^-")):
        ys = [max([r["maxV_sim"] for r in rows if r["w"] == w and r["polygon"].startswith(k)]
                  or [0.0]) for w in ws]
        ax[1].plot(ws, ys, mk, ms=4, label=f"{k} (max)")
    ax[1].axhline(0, color="k", lw=0.8)
    ax[1].set_xlabel("wind ratio w"); ax[1].set_ylabel("maxV_sim (m)")
    ax[1].set_title("violation vs wind"); ax[1].grid(alpha=0.3); ax[1].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig("outputs/figures/exp_fw_v1_27a_simultaneous.png", dpi=160)
    print("wrote outputs/figures/exp_fw_v1_27a_simultaneous.png")


if __name__ == "__main__":
    main()
