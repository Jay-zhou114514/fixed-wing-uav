"""τ 修正的独立验证（EXP-27A 的前置）。

背景：EXP-27A 四次实现失败，根因之一是 EXP-21/27 沿用的 τ 口径
      （`τ = 首个 v·n ≤ 0 的时刻`）在实现上有一个未处理的退化情形。

本脚本：
  1. 定义修正版 τ（模式 A）；
  2. 用**独立暴力参照**逐组验证；
  3. 输出可入库的验证结论。

修正版 τ（模式 A）：
    v(0)·n < 0  → 飞机在 t=0 已在后退 → τ = 0，穿透 = 0
    v(0)·n = 0  → **掠射**（相切）：不属于"已在后退"，走解析支
    否则        → τ = 首个使 v·n = 0 的正时刻
  解析支：v·n = 0 ⟺ cos(ψ0 + s·ω·τ − φ_n) = −(W·n)/Va
          令 A = arccos(−(W·n)/Va)，取满足 cos(θ) = ±A 的最小正 τ。

注：`v(0)·n = 0` 是测度零的相切退化。离散暴力参照会立刻判"已满足"（τ≈0），
    解析式则沿相切方向继续积分——两者在**该点上**不一致属预期，
    不在判据的适用范围。验证时排除 |v(0)·n| < 1e-9。
"""
from __future__ import annotations

import numpy as np

VA = 18.0
OM = np.deg2rad(25.0)
R = VA / OM
TWO_PI = 2.0 * np.pi
GRAZE_TOL = 1e-9


def _first_pos(x):
    r = np.mod(x, TWO_PI)
    return np.where(r > 1e-13, r, TWO_PI)


def disp(psi0, sign, t, w):
    """常值风下常转弯轨迹的地面位移。"""
    psi = psi0 + sign * OM * t
    dx = sign * R * (np.sin(psi) - np.sin(psi0)) + w * VA * t
    dy = -sign * R * (np.cos(psi) - np.cos(psi0))
    return dx, dy


def vdotn0(psi0, w, phi_n):
    return (VA * np.cos(psi0) + w * VA) * np.cos(phi_n) + VA * np.sin(psi0) * np.sin(phi_n)


def tau_fixed(psi0, sign, w, phi_n):
    """修正版 τ 与首次外摆穿透。返回 (penetration, tau, branch)。"""
    if vdotn0(psi0, w, phi_n) < -GRAZE_TOL:
        return 0.0, 0.0, "t0_backward"
    A = np.arccos(np.clip(-w * np.cos(phi_n), -1.0, 1.0))
    th0 = psi0 - phi_n
    if sign > 0:
        tau = min(_first_pos(A - th0), _first_pos(-A - th0))
    else:
        tau = min(_first_pos(th0 + A), _first_pos(th0 - A))
    t = tau / OM
    dx, dy = disp(psi0, sign, t, w)
    return float(dx * np.cos(phi_n) + dy * np.sin(phi_n)), float(t), "analytic"


def penetration_brute(psi0, sign, w, phi_n, n_t=400001):
    """独立暴力参照：离散扫描首个 v·n ≤ 0，取此前累积最大。"""
    n = np.array([np.cos(phi_n), np.sin(phi_n)])
    t = np.linspace(0.0, 4 * TWO_PI / OM, n_t)
    dx, dy = disp(psi0, sign, t, w)
    psi = psi0 + sign * OM * t
    vx = VA * np.cos(psi) + w * VA
    vy = VA * np.sin(psi)
    proj_d = dx * n[0] + dy * n[1]
    proj_v = vx * n[0] + vy * n[1]
    mask = proj_v <= 0.0
    if not mask.any():
        return None
    i = int(np.argmax(mask))
    return float(np.max(proj_d[: i + 1]))


def validate(step=5.0, n_t=200001, tol=1e-6, verbose=True):
    """逐组比对，排除掠射退化。返回汇总。"""
    rows = []
    for w in (0.0, 0.1, 0.2, 0.3, 0.4, 0.5):
        tot = bad = 0
        worst = 0.0
        for phd in np.arange(0.0, 360.0, step):
            phi_n = np.deg2rad(phd)
            for psd in np.arange(0.0, 360.0, step):
                psi0 = np.deg2rad(psd)
                if abs(vdotn0(psi0, w, phi_n)) < GRAZE_TOL:
                    continue                      # 掠射退化，不在适用范围内
                for sign in (+1, -1):
                    b = penetration_brute(psi0, sign, w, phi_n, n_t=n_t)
                    if b is None:
                        continue
                    r, _, _ = tau_fixed(psi0, sign, w, phi_n)
                    tot += 1
                    d = abs(r - b)
                    if d > tol:
                        bad += 1
                    worst = max(worst, d)
        rows.append((w, tot, bad, worst))
        if verbose:
            print(f"  w={w:>4.1f}  组数={tot:>6}  偏差>{tol:g}={bad:>4}  最大偏差={worst:.3e}")
    return rows


def check_negative_and_positive():
    """三件套之 (a)(b)：负对照与正对照。"""
    print("\n[负对照] 沿风向 w=0（无风）：required 应等于 R（转弯半径）")
    w = 0.0
    best = -np.inf
    for psd in np.arange(0.0, 360.0, 1.0):
        psi0 = np.deg2rad(psd)
        vals = [tau_fixed(psi0, s, w, 0.0)[0] for s in (+1, -1)]
        best = max(best, min(vals))
    print(f"   max_psi0 min_sign pen = {best:.6f} m；R = {R:.6f} m；"
          f"偏差 = {abs(best - R):.2e} → {'通过' if abs(best - R) < 1e-6 else '不通过'}")

    print("\n[正对照] w=0.3 沿风向：required 应等于 δd（非 R），判据须能区分")
    w = 0.3
    dd = R * np.sqrt(1 - w**2) + w * R * np.arccos(-w)
    best = -np.inf
    for psd in np.arange(0.0, 360.0, 1.0):
        psi0 = np.deg2rad(psd)
        vals = [tau_fixed(psi0, s, w, 0.0)[0] for s in (+1, -1)]
        best = max(best, min(vals))
    print(f"   max_psi0 min_sign pen = {best:.6f} m；δd = {dd:.6f} m；"
          f"偏差 = {abs(best - dd):.2e} → {'通过' if abs(best - dd) < 1e-5 else '不通过'}")
    print(f"   与 R 之差 = {abs(best - R):.4f} m（应显著非零，证明判据有区分能力）")
    return best


if __name__ == "__main__":
    print("=" * 78)
    print("τ 修正的独立验证（模式 A + 暴力参照）")
    print("=" * 78)
    print(f"\n参数：Va={VA} m/s，ω=25°/s，R={R:.6f} m，δu=R\n")
    check_negative_and_positive()
    print("\n[交叉验证] 修正 τ vs 独立暴力参照（排除掠射退化）")
    rows = validate()
    ok = all(bad == 0 for _, _, bad, _ in rows)
    print(f"\n→ 汇总：{'全部一致' if ok else '存在不一致'}"
          f"（阈值 1e-6 m）")
