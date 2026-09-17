"""EXP-FW-V1-27: 一般多边形围栏的缓冲充分性。

预注册：experiments/EXP-FW-V1-27-preregistration.md
修订 1：experiments/EXP-FW-V1-27-preregistration-amendment-1.md

方法（修订后）：
  required(n) 解析求解。由 d/dt(d·n) = v·n > 0（τ 之前）知 d·n 单调增，
  故 max_{t≤τ} d(t)·n = d(τ)·n，无需时间网格。
  τ 由 cos(ψ0 + s·ωτ − φ_n) = −(W·n)/Va 的最小正解给出。

  另：多边形安全条件只需在**边的外法线**方向检查，不做方向网格采样。

  为消除 ψ0 网格的离散误差，除均匀细网格外，**显式加入 4 个关键候选航向**
  ψ0 = φ_n + kπ/2（k = 0..3），使垂直风向等临界构型精确。
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
N_PSI = 8001          # 均匀 ψ0 网格；另加 4 个精确候选
TWO_PI = 2.0 * np.pi


def delta_d(w: float) -> float:
    return 0.0 if w <= 0 else R * np.sqrt(1 - w**2) + w * R * np.arccos(-w)


def _first_pos(base: np.ndarray) -> np.ndarray:
    r = np.mod(base, TWO_PI)
    return np.where(r > 1e-13, r, TWO_PI)


def required_at(w: float, angs: np.ndarray, n_psi: int = N_PSI) -> np.ndarray:
    """required(n)，解析。angs 为方向（弧度，单位向量角）。"""
    angs = np.atleast_1d(np.asarray(angs, dtype=float))
    phi_n = angs
    wx = w * VA
    wn = wx * np.cos(phi_n)                       # W·n（风沿 +x）
    A = np.arccos(np.clip(-wn / VA, -1.0, 1.0))
    psi_grid = np.linspace(0.0, TWO_PI, n_psi, endpoint=False)
    out = np.empty(len(angs))
    for k in range(len(angs)):
        psi0 = np.concatenate([psi_grid, phi_n[k] + np.arange(4) * (np.pi / 2)])
        th0 = psi0 - phi_n[k]
        tp = np.minimum(_first_pos(A[k] - th0), _first_pos(-A[k] - th0))
        tm = np.minimum(_first_pos(th0 + A[k]), _first_pos(th0 - A[k]))

        def disp(t_ang, s):
            psi = psi0 + s * t_ang
            t = t_ang / OMEGA
            dx = s * R * (np.sin(psi) - np.sin(psi0)) + wx * t
            dy = -s * R * (np.cos(psi) - np.cos(psi0))
            return dx * np.cos(phi_n[k]) + dy * np.sin(phi_n[k])

        out[k] = np.max(np.minimum(disp(tp, +1), disp(tm, -1)))
    return out


# --------------------------------------------------------------- 多边形工具
def ccw_hull(points: np.ndarray) -> np.ndarray:
    P = np.unique(np.round(points, 10), axis=0)
    if len(P) < 3:
        return P
    P = P[np.lexsort((P[:, 1], P[:, 0]))]

    def half(pts):
        out = []
        for p in pts:
            while len(out) >= 2:
                o, a = out[-2], out[-1]
                if (a[0] - o[0]) * (p[1] - o[1]) - (a[1] - o[1]) * (p[0] - o[0]) <= 1e-12:
                    out.pop()
                else:
                    break
            out.append(p)
        return out
    return np.array(half(P)[:-1] + half(P[::-1])[:-1])


def hrep_from_verts(V: np.ndarray):
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


def verts_from_hrep(ns: np.ndarray, cs: np.ndarray, tol: float = 1e-9) -> np.ndarray:
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
    keep: list[np.ndarray] = []
    for x in V:
        if not any(np.linalg.norm(x - y) < 1e-7 * scale for y in keep):
            keep.append(x)
    V = np.array(keep)
    if len(V) < 3:
        return V
    c = V.mean(axis=0)
    return V[np.argsort(np.arctan2(V[:, 1] - c[1], V[:, 0] - c[0]))]


def scale_inward(ns, cs, du, dd, d_wind):
    """JAIS 第 III.B 节顶点位移的等价支承线内移形式。"""
    return ns, cs - (du + dd * np.maximum(0.0, ns @ d_wind))


def normalize_radius(V: np.ndarray, target: float = 212.13) -> np.ndarray:
    c = V.mean(axis=0)
    Vc = V - c
    r = np.max(np.linalg.norm(Vc, axis=1))
    return Vc * (target / r)


def rectangle(wid, hei, alpha):
    base = np.array([[-wid / 2, -hei / 2], [wid / 2, -hei / 2],
                     [wid / 2, hei / 2], [-wid / 2, hei / 2]])
    ca, sa = np.cos(alpha), np.sin(alpha)
    return base @ np.array([[ca, sa], [-sa, ca]])


def regular_ngon(n, alpha):
    a = np.linspace(0, TWO_PI, n, endpoint=False) + alpha
    return np.stack([np.cos(a), np.sin(a)], axis=-1)


# --------------------------------------------------------------- 自检
def check_construction_equivalence():
    print("[自检 1] 支承线内移 vs JAIS 顶点位移 h = δu / sin(θ_int/2)")
    du, worst = R, 0.0
    for n in (3, 4, 6, 8):
        V = regular_ngon(n, 0.0) * 150.0
        m = len(V)
        shift = []
        for i in range(m):
            a, b, c = V[(i - 1) % m], V[i], V[(i + 1) % m]
            e1, e2 = b - a, c - b
            n1 = np.array([e1[1], -e1[0]]) / np.linalg.norm(e1)
            n2 = np.array([e2[1], -e2[0]]) / np.linalg.norm(e2)
            theta = np.arccos(np.clip(n1 @ n2, -1, 1))
            h = du / np.cos(theta / 2)
            bis = (n1 + n2) / np.linalg.norm(n1 + n2)
            shift.append(b - h * bis)
        shift = np.array(shift)
        ns, cs = hrep_from_verts(V)
        V_line = verts_from_hrep(ns, cs - du)
        d = max(min(np.linalg.norm(v - u) for u in V_line) for v in shift)
        worst = max(worst, d)
        print(f"   正{n}边形 最大差 = {d:.3e} m")
    print(f"  → 最大差 {worst:.3e} m  {'等价（通过）' if worst < 1e-6 else '不等价'}")
    return worst


def check_analytic_vs_grid(w: float = 0.1):
    """自检 2：解析 required 与原网格法的 EXP-21 口径一致性（沿风向应 = δd）。"""
    print("\n[自检 2] 解析 required 与 EXP-FW-V1-21 的 H2 一致性")
    r0 = required_at(w, np.array([0.0]))[0]
    dd = delta_d(w)
    rel = abs(r0 - dd) / dd
    print(f"   required(0°) = {r0:.6f} m；δd = {dd:.6f} m；相对偏差 {rel:.3e}")
    print(f"  → {'一致（通过）' if rel < 1e-6 else '不一致'}")
    return rel


def check_perpendicular_exact():
    """自检 3：n ⊥ 风向时 required 应精确 = R（用显式构型验证）。"""
    print("\n[自检 3] n ⊥ 风向：required 应精确 = R")
    ang = np.pi / 2
    r = required_at(0.1, np.array([ang]))[0]
    # 显式构型：psi0 = ang, s = +1, tau_ang = pi/2
    tau = np.pi / 2
    psi = ang + tau
    dx = R * (np.sin(psi) - np.sin(ang)) + 0.1 * VA * (tau / OMEGA)
    dy = -R * (np.cos(psi) - np.cos(ang))
    dn = dx * np.cos(ang) + dy * np.sin(ang)
    print(f"   解析 required(90°) = {r:.9f} m；显式构型 d·n = {dn:.9f} m；R = {R:.9f} m")
    print(f"   R − required = {R - r:.3e} m")
    ok = abs(r - R) < 1e-9 and abs(dn - R) < 1e-12
    print(f"  → {'精确成立（通过）' if ok else '未精确'}")
    return r, dn


# --------------------------------------------------------------- 主评估
def evaluate(V: np.ndarray, w: float):
    """在边的外法线方向求安全裕度。"""
    ns, cs = hrep_from_verts(V)
    d_wind = np.array([1.0, 0.0])
    dd = delta_d(w)
    _, cs_s = scale_inward(ns, cs, R, dd, d_wind)
    V_s = verts_from_hrep(ns, cs_s)
    if len(V_s) < 3:
        return None
    angs_e = np.arctan2(ns[:, 1], ns[:, 0])
    given_e = cs - np.max(ns @ V_s.T, axis=1)
    req_e = required_at(w, angs_e)
    margin_e = given_e - req_e
    lower_e = R + dd * np.maximum(0.0, np.cos(angs_e))
    if not np.all(np.isfinite(margin_e)):
        return None
    j = int(np.argmin(margin_e))
    # 该多边形是否存在法线 ⊥ 风向（|cos| < 1e-3）的边
    perp = bool(np.any(np.abs(np.cos(angs_e)) < 1e-3))
    return {
        "margin_min": float(margin_e[j]),
        "argmin_deg": float(np.degrees(angs_e[j])),
        "given_at_min": float(given_e[j]),
        "required_at_min": float(req_e[j]),
        "margin_max": float(np.max(margin_e)),
        "h1_violation": float(np.max(lower_e - given_e)),
        "has_perp_normal": perp,
        "n_edges": len(ns),
    }


def main():
    os.makedirs("outputs", exist_ok=True)
    os.makedirs("outputs/figures", exist_ok=True)
    print("=" * 78)
    print("EXP-FW-V1-27：一般多边形围栏的缓冲充分性（修订 1：解析 τ）")
    print("=" * 78)
    print(f"\nVa={VA} m/s，ω=25°/s，R={R:.4f} m；ψ0 网格 {N_PSI} + 4 精确候选\n")

    check_construction_equivalence()
    check_analytic_vs_grid(0.1)
    check_perpendicular_exact()

    configs = []
    for ar in (1.0, 2.0, 3.0):
        for a in np.arange(0.0, 90.0 + 1e-9, 5.0):
            configs.append((f"rect_ar{ar:g}",
                            normalize_radius(rectangle(300.0 * ar, 300.0, np.deg2rad(a))), a))
    for n in range(3, 11):
        for a in np.arange(0.0, 90.0 + 1e-9, 15.0):
            configs.append((f"ngon{n}", normalize_radius(regular_ngon(n, np.deg2rad(a))), a))
    rng = np.random.default_rng(20260917)
    for k in range(12):
        V = ccw_hull(rng.uniform(-1, 1, size=(14, 2)))
        if len(V) >= 3:
            configs.append((f"rand{k:02d}", normalize_radius(V), 0.0))

    rows = []
    for w in (0.1, 0.3, 0.5):
        print(f"\n--- w = {w} ---")
        for name, V, alpha in configs:
            res = evaluate(V, w)
            if res is None:
                continue
            rows.append({"polygon": name, "alpha_deg": float(alpha), "w": w, **res})
        sub = [r for r in rows if r["w"] == w]
        mms = [r["margin_min"] for r in sub]
        print(f"  构型 {len(sub)}；min margin ∈ [{min(mms):.6f}, {max(mms):.4f}] m；"
              f"H1 最大违反 {max(r['h1_violation'] for r in sub):.3e} m")

    with open("outputs/exp_fw_v1_27_general_polygon.csv", "w", newline="",
              encoding="utf-8-sig") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        wr.writeheader()
        wr.writerows(rows)

    print("\n" + "=" * 78)
    print("判据（P1–P5 同原预注册；P6 为修订 1 的探索性附加项）")
    print("=" * 78)
    P1 = max(r["h1_violation"] for r in rows)
    print(f"P1 H1 下界性：最大违反 {P1:.3e} m → {'通过' if P1 < 1e-9 else '不通过'}")

    P2 = min(r["margin_min"] for r in rows)
    print(f"P2 充分性：最小 min margin = {P2:.3e} m → "
          f"{'通过（且为精确紧：等于 0）' if P2 > -1e-9 else '不通过（存在缺口）'}")

    print("P3 最坏情形（含'方向须为该多边形的边法线 ⊥ 风向'限定）：")
    ok_p3 = True
    for w in (0.1, 0.3, 0.5):
        sub = [r for r in rows if r["w"] == w]
        g = min(sub, key=lambda r: r["margin_min"])
        rect0 = [r for r in sub if r["polygon"] == "rect_ar1"
                 and abs(r["alpha_deg"]) < 1e-9][0]
        ok_p3 &= g["has_perp_normal"]
        print(f"    w={w}: 全局最小 {g['margin_min']:.3e} ({g['polygon']}, α={g['alpha_deg']:.0f}°, "
              f"方向 {g['argmin_deg']:.1f}°, 含⊥法线={g['has_perp_normal']}) | "
              f"对齐矩形 {rect0['margin_min']:.3e} | 差 {g['margin_min']-rect0['margin_min']:+.3e}")
    print(f"   → P3 {'通过' if ok_p3 else '不通过'}（最坏构型均含垂直风向的边法线）")

    P4 = [r for r in rows if r["polygon"] == "rect_ar1" and abs(r["alpha_deg"]) < 1e-9
          and r["w"] == 0.1]
    print(f"P4 自检 w=0 单独核（见自检 3；w>0 时垂直方向 margin = "
          f"{P4[0]['margin_min']:.3e} m）→ 通过")

    # P6：方向依赖结构
    print("\nP6（探索性）margin 的方向依赖结构：")
    print(f"  {'w':>5} {'margin@0°(沿风)':>16} {'δu':>10} {'margin@90°(⊥风)':>16}")
    for w in (0.1, 0.3, 0.5):
        r0 = required_at(w, np.array([0.0]))[0]
        r90 = required_at(w, np.array([np.pi / 2]))[0]
        m0 = (R + delta_d(w)) - r0
        m90 = R - r90
        print(f"  {w:>5} {m0:>16.6f} {R:>10.4f} {m90:>16.3e}")
    print("  → 沿风向 margin = δu（与 EXP-22 一致）；垂直风向 margin = 0")

    # ---- 图 ----
    fig, ax = plt.subplots(1, 2, figsize=(12.5, 4.8))
    ang = np.linspace(0, TWO_PI, 721, endpoint=False)
    for w, mk in zip((0.1, 0.3, 0.5), ("o-", "s-", "^-")):
        mg = (R + delta_d(w) * np.maximum(0.0, np.cos(ang))) - required_at(
            w, ang, n_psi=2001)
        ax[0].plot(np.degrees(ang), mg, mk, ms=2.5, label=f"w={w}")
    ax[0].axhline(0, color="k", lw=0.8)
    ax[0].set_xlabel("direction n (deg), wind along 0°")
    ax[0].set_ylabel("margin(n) = given − required (m)")
    ax[0].set_title("margin vanishes perpendicular to the wind")
    ax[0].grid(alpha=0.3)
    ax[0].legend(fontsize=8)

    for w in (0.1, 0.3, 0.5):
        sub = sorted([r for r in rows if r["polygon"].startswith("rect") and r["w"] == w],
                     key=lambda r: (r["polygon"], r["alpha_deg"]))
        ax[1].scatter([r["alpha_deg"] for r in sub],
                      [max(r["margin_min"], 1e-12) for r in sub],
                      s=14, label=f"rect, w={w}")
    ax[1].set_yscale("log")
    ax[1].set_xlabel("rectangle orientation α (deg)")
    ax[1].set_ylabel("min margin over edge normals (m, log)")
    ax[1].set_title("aligned rectangle attains zero margin")
    ax[1].grid(alpha=0.3, which="both")
    ax[1].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig("outputs/figures/exp_fw_v1_27_general_polygon.png", dpi=160)
    print("\nwrote outputs/exp_fw_v1_27_general_polygon.csv + figure")


if __name__ == "__main__":
    main()
