"""P2 附：验证 dmin_turn_e = d0_e − w·Va·m_e·T_e 与窗口末端 T_e 的解析式。

这是 P2 闭式的**唯一新机制**，必须单独验证（P2-1）。
若此式不成立，则闭式的其余部分无从谈起。
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


def ngon(n, w, phi_wind=0.0, radius=212.13, alpha=0.0, j=0):
    a = np.linspace(0, TWO_PI, n, endpoint=False) + alpha
    V = J.normalize_radius(radius * np.stack([np.cos(a), np.sin(a)], axis=-1))
    ns, cs, shifts, V_s = J.scaled_geometry(V, w, VA, phi_wind)
    cs_s = cs - shifts
    xv = V_s[j]
    adj = [e for e in range(len(ns)) if abs(cs_s[e] - ns[e] @ xv) < 1e-6]
    b_out = ns[adj[0]] + ns[adj[1]]
    b_out = b_out / np.linalg.norm(b_out)
    return dict(ns=ns, cs=cs, shifts=shifts, V_s=V_s, xv=xv, adj=adj,
                b_out=b_out, n=n, w=w, phi_wind=phi_wind)


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


print("=" * 104)
print("P2 附：dmin_turn 解析式验证")
print("=" * 104)
print(f"{'n':>3}{'w':>6}{'s':>9}{'sign':>6}{'边':>4}{'dmin数值':>12}{'dmin解析':>12}"
      f"{'差':>11}{'m_e':>7}{'T_e':>9}{'来源':>12}")
print("-" * 104)
worst = 0.0
nbad = 0
for n in (3, 4, 5, 6, 7, 8, 10):
    for w in (0.1, 0.3, 0.5):
        sc = ngon(n, w)
        ns, cs = sc["ns"], sc["cs"]
        b_out, xv, w_ = sc["b_out"], sc["xv"], sc["w"]
        d_w = np.array([1.0, 0.0])
        psi0 = float(np.arctan2(b_out[1], b_out[0]))
        beta = np.arctan2(ns[:, 1], ns[:, 0])
        delta = np.arctan2(np.sin(beta - psi0), np.cos(beta - psi0))
        m = np.maximum(0.0, ns @ d_w)
        for s in (0.0, 10.0, 25.0):
            for sign in (+1, -1):
                x0 = xv - s * b_out
                c0 = J.rolling_center(x0, psi0, sign, R)
                d0 = cs - ns @ c0
                # d0 的解析式
                g = ns @ b_out
                q = ns @ np.array([-b_out[1], b_out[0]])
                d0_ana = R + J.delta_d(w) * m + s * g - sign * R * q
                for e in range(len(ns)):
                    dmin_num = J._turn_segment_min_de(x0, psi0, sign, ns[e], cs[e],
                                                      w, R, VA, 0.0)
                    T = T_analytic(sign, delta[e], m[e], w)
                    dmin_ana = d0_ana[e] - w * VA * m[e] * T
                    err = abs(dmin_ana - dmin_num)
                    # 仅报告数值确实被"转弯消耗"改变（或关键）的项
                    if m[e] > 1e-9 and err > 1e-7:
                        nbad += 1
                        if nbad <= 22:
                            print(f"{n:>3}{w:>6.2f}{s:>9.1f}{sign:>+6}{e:>4}"
                                  f"{dmin_num:>12.4f}{dmin_ana:>12.4f}{err:>11.2e}"
                                  f"{m[e]:>7.3f}{T:>9.4f}"
                                  f"{('d0' if d0_ana[e]<=dmin_num+1e-12 else 'turn'):>12}")
                    if m[e] > 1e-9:
                        worst = max(worst, err)
print()
print(f"  涉及 m_e>0 的项：最大偏差 = {worst:.3e} m；不符项数 = {nbad}")
print(f"  -> {'解析式成立' if worst < 1e-7 else '解析式不成立，需修正 T_e'}")

print()
print("=" * 104)
print("T_e 的正确性单测（直接积分 rate_e，找首个正窗口末端）")
print("=" * 104)
print(f"{'n':>3}{'w':>6}{'sign':>6}{'边':>4}{'T_e 解析':>12}{'T_e 扫描':>12}{'差':>10}")
t = np.linspace(0, TWO_PI / OM, 200001)
worstT = 0.0
for n in (3, 4, 6, 8):
    for w in (0.1, 0.3, 0.5):
        sc = ngon(n, w)
        ns = sc["ns"]
        b_out, w_ = sc["b_out"], sc["w"]
        d_w = np.array([1.0, 0.0])
        psi0 = float(np.arctan2(b_out[1], b_out[0]))
        beta = np.arctan2(ns[:, 1], ns[:, 0])
        delta = np.arctan2(np.sin(beta - psi0), np.cos(beta - psi0))
        m = np.maximum(0.0, ns @ d_w)
        for sign in (+1, -1):
            for e in range(len(ns)):
                if m[e] <= 1e-9:
                    continue
                Ta = T_analytic(sign, delta[e], m[e], w)
                psi = psi0 + sign * OM * t
                rate = VA * np.cos(psi - beta[e]) + w * VA * m[e]
                moving = rate > 0
                if not moving.any():
                    continue
                i0 = int(np.argmax(moving))
                i1 = i0
                while i1 + 1 < len(moving) and moving[i1 + 1]:
                    i1 += 1
                Ts = t[i1]
                if abs(Ta - Ts) > 1e-6:
                    worstT = max(worstT, abs(Ta - Ts))
                    if worstT < 1e10:
                        print(f"{n:>3}{w:>6.2f}{sign:>+6}{e:>4}{Ta:>12.4f}{Ts:>12.4f}"
                              f"{abs(Ta-Ts):>10.2e}")
print(f"  最大差 = {worstT:.3e} s -> {'T_e 解析式成立' if worstT < 1e-6 else 'T_e 需修正'}")
