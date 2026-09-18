"""P2 附：闭式失配诊断 —— 在数值 d* 处逐边打印 room/rate，找出真正的约束项。

背景：`p2_dstar_wind_closed_form.py` 的闭式在 w>0 时与数值臂严重不符
（n=3, w=0.5 差 51.7 m），因此该闭式**缺失了某项**。本脚本定位缺失项。
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

R = J.R
VA = J.VA_DEFAULT


def ngon(n, w, phi_wind=0.0, radius=212.13, alpha=0.0, j=0):
    a = np.linspace(0, 2 * np.pi, n, endpoint=False) + alpha
    V = J.normalize_radius(radius * np.stack([np.cos(a), np.sin(a)], axis=-1))
    ns, cs, shifts, V_s = J.scaled_geometry(V, w, VA, phi_wind)
    cs_s = cs - shifts
    xv = V_s[j]
    adj = [e for e in range(len(ns)) if abs(cs_s[e] - ns[e] @ xv) < 1e-6]
    b_out = ns[adj[0]] + ns[adj[1]]
    b_out = b_out / np.linalg.norm(b_out)
    return dict(ns=ns, cs=cs, shifts=shifts, V_s=V_s, xv=xv, adj=adj,
                b_out=b_out, cs_s=cs_s, n=n, w=w, phi_wind=phi_wind)


def dstar_numeric(sc, dmax=3.0 * R, tol=1e-10):
    ns, cs, xv, b_out = sc["ns"], sc["cs"], sc["xv"], sc["b_out"]
    w = sc["w"]
    psi0 = float(np.arctan2(b_out[1], b_out[0]))
    f = lambda s: J.tau_crit_analytic_joint(xv - s * b_out, psi0, ns, cs, w, R,
                                            va=VA, phi_wind=sc["phi_wind"])[0]
    if f(0.0) > 0:
        return 0.0
    lo, hi = 0.0, dmax
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        v = f(mid)
        if not np.isfinite(v) or v <= 0:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def terms_at(sc, s):
    """在位置 s 处，逐 sign 逐边列出 room/rate 与来源（d0 还是 dmin_turn）。"""
    ns, cs, xv, b_out, w = sc["ns"], sc["cs"], sc["xv"], sc["b_out"], sc["w"]
    psi0 = float(np.arctan2(b_out[1], b_out[0]))
    x0 = xv - s * b_out
    vg = J.v_ground(psi0, w, VA, sc["phi_wind"])
    rates = ns @ vg
    out = {}
    for sign in (+1, -1):
        c0 = J.rolling_center(x0, psi0, sign, R)
        d0 = cs - ns @ c0
        dmin = np.array([J._turn_segment_min_de(x0, psi0, sign, ns[k], cs[k], w, R,
                                                VA, sc["phi_wind"])
                         for k in range(len(ns))])
        rows = []
        for k in range(len(ns)):
            room = min(d0[k], dmin[k]) - R
            src = "d0" if d0[k] <= dmin[k] else "dmin_turn"
            rows.append(dict(e=k, d0=d0[k], dmin=dmin[k], room=room,
                             rate=rates[k], src=src,
                             t=(room / rates[k] if rates[k] > 1e-9 else np.nan)))
        out[sign] = rows
    return out, rates


print("=" * 104)
print("P2 附：闭式失配诊断")
print("=" * 104)

for (n, w) in ((3, 0.3), (4, 0.3), (3, 0.5), (4, 0.1)):
    sc = ngon(n, w)
    ds = dstar_numeric(sc)
    theta = 180 - 360 / n
    print()
    print("=" * 104)
    print(f"n={n}  theta={theta:.2f} deg  w={w}  数值 d* = {ds:.6f} m "
          f"(R*cot(theta/2) = {R/np.tan(np.radians(theta/2)):.6f})")
    print(f"  顶点 xv=({sc['xv'][0]:.3f},{sc['xv'][1]:.3f})  "
          f"b_out=({sc['b_out'][0]:.4f},{sc['b_out'][1]:.4f})  adj={sc['adj']}")
    print(f"  两相邻边 σ_e = n_e·perp(b_out): "
          f"{[round(float(sc['ns'][e] @ np.array([-sc['b_out'][1], sc['b_out'][0]])),4) for e in sc['adj']]}")
    print(f"  两相邻边 m_e = max(0, n_e·d_wind): "
          f"{[round(max(0.0,float(sc['ns'][e] @ np.array([1.0,0.0]))),4) for e in sc['adj']]}")
    dd = J.delta_d(w)
    print(f"  delta_d = {dd:.4f}")
    print(f"  闭式预言（相邻边）：room_e = delta_d*m_e + s*sin(theta/2) "
          f"- sign*sigma_e*R*cos(theta/2)")
    print(f"      sin(theta/2)={np.sin(np.radians(theta/2)):.4f}  "
          f"cos(theta/2)={np.cos(np.radians(theta/2)):.4f}")
    print()
    # 在 d* 附近取两点
    for s in (max(0.0, ds - 0.5), ds, ds + 0.5):
        tt, _ = J.tau_crit_analytic_joint(sc["xv"] - s * sc["b_out"],
                                          float(np.arctan2(sc["b_out"][1], sc["b_out"][0])),
                                          sc["ns"], sc["cs"], w, R, va=VA,
                                          phi_wind=sc["phi_wind"])
        tm = J.tau_crit_analytic_joint(sc["xv"] - s * sc["b_out"],
                                       float(np.arctan2(sc["b_out"][1], sc["b_out"][0])),
                                       sc["ns"], sc["cs"], w, R, va=VA,
                                       phi_wind=sc["phi_wind"])[0]
        out, rates = terms_at(sc, s)
        print(f"  --- s = {s:.4f}   tau = {tm:.6f}")
        for sign in (+1, -1):
            rows = out[sign]
            fin = [r for r in rows if np.isfinite(r["t"])]
            fin.sort(key=lambda r: r["t"])
            print(f"      sign={sign:+d}  (前 3 个有限候选)")
            print(f"        {'e':>3}{'d0':>10}{'dmin_turn':>11}{'room':>10}"
                  f"{'rate':>10}{'来源':>11}{'t':>10}")
            for r in fin[:3]:
                print(f"        {r['e']:>3}{r['d0']:>10.3f}{r['dmin']:>11.3f}"
                      f"{r['room']:>10.3f}{r['rate']:>10.3f}{r['src']:>11}{r['t']:>10.4f}")
            infeas = [r for r in rows if r["rate"] <= 1e-9 and r["room"] < 0]
            if infeas:
                print(f"        !! 近掠射不可行边: "
                      f"{[(r['e'], round(r['room'],3), round(r['rate'],3), r['src']) for r in infeas]}")
        print()
