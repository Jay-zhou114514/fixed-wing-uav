"""诊断：EXP-27A 四次失败是"实现错误"还是"概念问题"？

用**独立暴力参照**测三个部件，不依赖我此前的任何推理：
  T1  v0 的解析 τ 公式  vs  暴力搜索首个 v·n ≤ 0
  T2  EXP-27 的 required  vs  暴力 max_psi0 min_sign [首次外摆穿透]
  T3  单边、无顶点构型：能否用一次最大速率转弯保持不越界（应能，且与 d 有关）
"""
from __future__ import annotations

import numpy as np

VA = 18.0
OM = np.deg2rad(25.0)
R = VA / OM
TWO_PI = 2 * np.pi


def d_traj(psi0, sign, t, w):
    psi = psi0 + sign * OM * t
    dx = sign * R * (np.sin(psi) - np.sin(psi0)) + w * VA * t
    dy = -sign * R * (np.cos(psi) - np.cos(psi0))
    return dx, dy


def v_traj(psi0, sign, t, w):
    psi = psi0 + sign * OM * t
    return VA * np.cos(psi) + w * VA, VA * np.sin(psi)


# ---------- 暴力参照：首个 v·n ≤ 0 的时刻与首次外摆穿透 ----------
def brute(psi0, sign, w, n, n_t=400001):
    t = np.linspace(0.0, 4 * TWO_PI / OM, n_t)
    dx, dy = d_traj(psi0, sign, t, w)
    vx, vy = v_traj(psi0, sign, t, w)
    proj_d = dx * n[0] + dy * n[1]
    proj_v = vx * n[0] + vy * n[1]
    mask = proj_v <= 0.0
    if mask.any():
        i = int(np.argmax(mask))
        pen_first = float(np.max(proj_d[: i + 1]))
    else:
        pen_first = float("inf")
    pen_full = float(np.max(proj_d))
    return pen_first, pen_full


# ---------- v0 的解析 τ 公式 ----------
def first_pos(x):
    r = np.mod(x, TWO_PI)
    return np.where(r > 1e-13, r, TWO_PI)


def v0_R(psi0, sign, w, phi_n):
    A = np.arccos(np.clip(-w * np.cos(phi_n), -1.0, 1.0))
    th0 = psi0 - phi_n
    if sign > 0:
        tau = min(first_pos(A - th0), first_pos(-A - th0))
    else:
        tau = min(first_pos(th0 + A), first_pos(th0 - A))
    t = tau / OM
    dx, dy = d_traj(psi0, sign, np.array([t]), w)
    return dx[0] * np.cos(phi_n) + dy[0] * np.sin(phi_n), t


print("=" * 78)
print("T1  v0 的解析 τ 公式 vs 暴力首个 v·n ≤ 0")
print("=" * 78)
worst = 0.0
rng = np.random.default_rng(20260918)
for w in (0.0, 0.1, 0.3, 0.5):
    for ndeg in (0, 45, 90, 135, 180, 270):
        n = np.array([np.cos(np.deg2rad(ndeg)), np.sin(np.deg2rad(ndeg))])
        phi_n = np.arctan2(n[1], n[0])
        for _ in range(6):
            psi0 = float(rng.uniform(0, TWO_PI))
            for sign in (+1, -1):
                r_an, tau_an = v0_R(psi0, sign, w, phi_n)
                pen_b, _ = brute(psi0, sign, w, n)
                if not np.isfinite(pen_b):
                    continue
                diff = abs(r_an - pen_b)
                worst = max(worst, diff)
print(f"   最大绝对差 = {worst:.3e} m → "
      f"{'一致（τ 公式正确）' if worst < 1e-3 else '不一致（τ 公式有 bug）'}")

print()
print("=" * 78)
print("T2  EXP-27 的 required vs 暴力 max_psi0 min_sign [首次外摆穿透]")
print("=" * 78)
def required_brute(w, phi_n, n_psi=20001):
    n = np.array([np.cos(phi_n), np.sin(phi_n)])
    best = -np.inf
    for psi0 in np.linspace(0, TWO_PI, n_psi, endpoint=False):
        vals = []
        for sign in (+1, -1):
            p, _ = brute(psi0, sign, w, n, n_t=2001)
            vals.append(p)
        best = max(best, min(vals))
    return best

print(f"   {'w':>5} {'n(deg)':>8} {'EXP-27 required':>16} {'暴力首次外摆':>14} {'差':>10}")
for w in (0.1, 0.3):
    for ndeg in (0.0, 90.0):
        phi_n = np.deg2rad(ndeg)
        # EXP-27 的解析式
        dd = 0.0 if w <= 0 else R * np.sqrt(1 - w**2) + w * R * np.arccos(-w)
        A = np.arccos(np.clip(-w * np.cos(phi_n), -1, 1))
        # 直接调用 EXP-27 的实现
        import importlib.util
        s = importlib.util.spec_from_file_location('b', 'src/exp_fw_v1_27_general_polygon.py')
        b = importlib.util.module_from_spec(s); s.loader.exec_module(b)
        req = b.required_at(w, np.array([phi_n]))[0]
        rb = required_brute(w, phi_n, n_psi=7201)
        print(f"   {w:>5.1f} {ndeg:>8.1f} {req:>16.6f} {rb:>14.6f} {abs(req-rb):>10.2e}")

print()
print("=" * 78)
print("T3  单边构型：飞机距边界 d，一次最大速率转弯能否保持不越界？")
print("=" * 78)
print("   （若 d 足够大则应能；d 小于某阈值则必然越界 → 判据应有检出能力）")
w = 0.3
n = np.array([1.0, 0.0])
print(f"   {'d(m)':>8} {'最坏首次外摆':>14} {'判定':>10}")
psi_grid = np.linspace(0, TWO_PI, 1441, endpoint=False)
for d in (5.0, 20.0, 41.25, 60.0, 80.0, 103.82, 120.0, 150.0):
    worst = -np.inf
    for psi0 in psi_grid:
        vals = []
        for sign in (+1, -1):
            p, _ = brute(psi0, sign, w, n, n_t=20001)
            vals.append(p)
        worst = max(worst, min(vals))
    viol = worst - d
    print(f"   {d:>8.2f} {worst:>14.4f} {'越界' if viol > 1e-9 else '安全':>10}")
