"""P2 最终核查：相邻边显式闭式 vs 高分辨率数值（N_T 提高以消除网格误差）。

显式闭式（相邻边，q_e = sign·cos(θ/2)，g_e = sin(θ/2)）：
    room_e(sign,s) = δd·m_e + s·sin(θ/2) − sign·R·cos(θ/2) − w·Va·m_e·T_e
    rate_e         = Va·( sin(θ/2) + w·m_e )
    τ = 0 ⟹
        s* = [ sign·R·cos(θ/2) − m_e·( δd − w·Va·T_e ) ] / sin(θ/2)

其中 T_e = [ arccos(−w·m_e) + sign·δ_e ] / ω。
（δ_e 为 n_e 与 b_out 的夹角，已归一化。）

本脚本用**提高 N_T 的独立数值实现**（不使用 joint_latency 的 4001 网格）
核对上式，并判定其成立范围。
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np

SRC = Path(__file__).resolve().parent.parent / "src"
spec = importlib.util.spec_from_file_location("j26", SRC / "exp_fw_v1_26_joint_latency.py")
J = importlib.util.module_from_spec(spec)
sys.modules["j26"] = J
spec.loader.exec_module(J)

R, VA, OM = J.R, J.VA_DEFAULT, J.OMEGA
TWO_PI = 2 * np.pi
NT = 4_000_001          # 高分辨率转弯网格


def dmin_turn_hi(x0, psi0, sign, n_e, c_e, w, n_t=NT):
    """独立的高分辨率转弯段最小距离（与 joint_latency 同一口径，仅网格更细）。"""
    t = np.linspace(0.0, TWO_PI / OM, n_t)
    psi = psi0 + sign * OM * t
    dx = sign * R * (np.sin(psi) - np.sin(psi0)) + w * VA * t
    dy = -sign * R * (np.cos(psi) - np.cos(psi0))
    x = np.asarray(x0, float) + np.stack([dx, dy], axis=-1)
    vgx = VA * np.cos(psi) + w * VA
    vgy = VA * np.sin(psi)
    rate = vgx * n_e[0] + vgy * n_e[1]
    moving = rate > 1e-12
    if not moving.any():
        c0 = np.asarray(x0, float) + sign * R * np.array([-np.sin(psi0), np.cos(psi0)])
        return float(c_e - c0 @ n_e)
    i0 = int(np.argmax(moving))
    i1 = i0
    while i1 + 1 < len(moving) and moving[i1 + 1]:
        i1 += 1
    center = x + sign * R * np.stack([-np.sin(psi), np.cos(psi)], axis=-1)
    d = c_e - center @ n_e
    return float(np.min(d[i0:i1 + 1]))


def tau_num(x0, psi0, ns, cs, w):
    """独立数值 τ_crit（高分辨率）。"""
    vg = np.array([VA * np.cos(psi0) + w * VA, VA * np.sin(psi0)])
    rates = ns @ vg
    best = -np.inf
    for sign in (+1, -1):
        c0 = np.asarray(x0, float) + sign * R * np.array([-np.sin(psi0), np.cos(psi0)])
        d0 = cs - ns @ c0
        dmin = np.array([dmin_turn_hi(x0, psi0, sign, ns[k], cs[k], w)
                         for k in range(len(ns))])
        m = np.minimum(d0, dmin)
        t = np.inf
        for e in range(len(ns)):
            room = m[e] - R
            if rates[e] > 1e-12:
                t = min(t, room / rates[e])
            elif room < 0:
                t = -np.inf
                break
        best = max(best, t)
    return best


def ngon(n, w, radius=212.13, alpha=0.0, j=0):
    a = np.linspace(0, TWO_PI, n, endpoint=False) + alpha
    V = J.normalize_radius(radius * np.stack([np.cos(a), np.sin(a)], axis=-1))
    ns, cs, shifts, V_s = J.scaled_geometry(V, w, VA, 0.0)
    xv = V_s[j]
    adj = [e for e in range(len(ns)) if abs((cs - shifts)[e] - ns[e] @ xv) < 1e-6]
    b_out = ns[adj[0]] + ns[adj[1]]
    b_out /= np.linalg.norm(b_out)
    return ns, cs, shifts, V_s, xv, adj, b_out


def T_analytic(sign, delta_e, m_e, w):
    if w <= 0 or m_e <= 0:
        return 0.0
    A = np.arccos(-w * m_e)
    u0 = -sign * delta_e
    k0 = int(np.floor((u0 + A) / TWO_PI))
    for kk in range(k0 - 2, k0 + 4):
        lo, hi = -A + TWO_PI * kk, A + TWO_PI * kk
        if hi <= u0:
            continue
        if max(u0, lo) < hi:
            return max(0.0, (hi + sign * delta_e) / OM)
    return 0.0


print("=" * 108)
print("P2 最终：相邻边显式闭式 vs 高分辨率数值（N_T = 4e6）")
print("=" * 108)
print(f"{'n':>3}{'theta':>8}{'w':>6}{'sign':>6}{'m_e':>7}{'T_e':>9}{'s*(显式)':>12}"
      f"{'d*(数值)':>12}{'差':>10}{'绑定边':>7}{'相邻?':>7}")
print("-" * 108)

worst = 0.0
rows = []
for n in (3, 4, 5, 6, 8):
    for w in (0.0, 0.1, 0.3, 0.5):
        ns, cs, shifts, V_s, xv, adj, b_out = ngon(n, w)
        theta = np.pi - np.arccos(np.clip(ns[adj[0]] @ ns[adj[1]], -1, 1))
        psi0 = float(np.arctan2(b_out[1], b_out[0]))
        st, ct = np.sin(theta / 2), np.cos(theta / 2)
        dd = J.delta_d(w)
        beta = np.arctan2(ns[:, 1], ns[:, 0])
        delta = np.arctan2(np.sin(beta - psi0), np.cos(beta - psi0))
        m = np.maximum(0.0, ns @ np.array([1.0, 0.0]))
        # 数值 d*（高分辨率，先粗扫再细二分）
        f = lambda s: tau_num(xv - s * b_out, psi0, ns, cs, w)
        ds = np.linspace(0.0, 2.5 * R, 4001)
        tv = np.array([f(float(s)) for s in ds])
        dnum = np.nan
        for i in range(len(ds) - 1):
            a, b = tv[i], tv[i + 1]
            if np.isfinite(a) and np.isfinite(b) and a <= 0 < b:
                lo, hi = ds[i], ds[i + 1]
                for _ in range(45):
                    mid = 0.5 * (lo + hi)
                    if f(mid) <= 0:
                        lo = mid
                    else:
                        hi = mid
                dnum = 0.5 * (lo + hi)
                break
            if not np.isfinite(a) and np.isfinite(b) and b > 0:
                lo, hi = ds[i], ds[i + 1]
                for _ in range(45):
                    mid = 0.5 * (lo + hi)
                    v = f(mid)
                    if not np.isfinite(v) or v <= 0:
                        lo = mid
                    else:
                        hi = mid
                dnum = 0.5 * (lo + hi)
                break
        if not np.isfinite(dnum):
            continue
        # 绑定 (sign, e)：在 d* 处 room/rate 最小
        best = None
        for sign in (+1, -1):
            c0 = np.asarray(xv - dnum * b_out) + sign * R * np.array([-np.sin(psi0), np.cos(psi0)])
            d0 = cs - ns @ c0
            for e in range(len(ns)):
                rate_e = VA * ns[e] @ np.array([np.cos(psi0) + w, np.sin(psi0)])
                if rate_e <= 1e-12:
                    continue
                room = (d0[e] - R) - (w * VA * m[e] * T_analytic(sign, delta[e], m[e], w)
                                      if m[e] > 0 else 0.0)
                t = abs(room)
                if best is None or t < best[0]:
                    best = (t, sign, e, room, rate_e)
        _, sign, e, room, rate_e = best
        T = T_analytic(sign, delta[e], m[e], w)
        s_exp = (sign * R * ct - m[e] * (dd - w * VA * T)) / st
        d = abs(s_exp - dnum) if np.isfinite(s_exp) else np.nan
        isadj = e in adj
        if np.isfinite(d):
            worst = max(worst, d)
        rows.append((n, np.degrees(theta), w, s_exp, dnum, d, e, isadj))
        print(f"{n:>3}{np.degrees(theta):>8.2f}{w:>6.2f}{sign:>+6}{m[e]:>7.3f}"
              f"{T:>9.4f}{s_exp:>12.5f}{dnum:>12.5f}"
              f"{(d if np.isfinite(d) else float('nan')):>10.2e}{e:>7}"
              f"{('是' if isadj else '否'):>7}")

print()
print("=" * 108)
adj_rows = [r for r in rows if r[7]]
non_rows = [r for r in rows if not r[7]]
print(f"  绑定边为**相邻边**的组数：{len(adj_rows)}；最大偏差 = "
      f"{max([r[5] for r in adj_rows]) if adj_rows else float('nan'):.3e} m")
print(f"  绑定边为**非相邻边**的组数：{len(non_rows)}；最大偏差 = "
      f"{max([r[5] for r in non_rows]) if non_rows else float('nan'):.3e} m")
print()
print("  判读：显式闭式在绑定边为相邻边时成立；非相邻边绑定需另用一般几何。")
