"""P2：有风时 d* 的解析闭式（含转弯段消耗）—— K9 的 w>0 推广。

============================================================ 预注册 ============================================================

**几何**（C 区参数化）：顶点处两条相邻边外法线 n_1,n_2；内角 θ；
向外分角线 b_out；位置 x0(s) = xv − s·b_out；航向 ψ0 ∥ b_out（朝分角线外，最不利）。

记：g_e = n_e·b_out（**对全部边**，不只相邻边）、q_e = n_e·perp(b_out)、
    m_e = max(0, n_e·d_wind)、δd = δd(w)、R = Va/ω。

**缩放层顶点**满足 n_e·xv = c_e − R − δd·m_e，故

    d0_e(s) = c_e − n_e·c0(s)，  c0(s) = x0(s) + sign·R·perp(ψ0)
            = R + δd·m_e + s·g_e − sign·R·q_e          （初始圆心距离）
    room0_e = d0_e − R = δd·m_e + s·g_e − sign·R·q_e

**关键结构（本项的新内容）**：转弯段中圆心为
    center(t) = c0 + w·Va·t·d_wind        （**纯风致平移，与转弯率无关**）
故 d_e(t) = d0_e − w·Va·m_e·t，**单调减**（m_e > 0 时），最小在**窗口末端**：

    dmin_turn_e = d0_e − w·Va·m_e·T_e
    T_e = 窗口末端 = 地面速度首次与边平行的时刻

    rate_e(t) = n_e·v_g(ψ(t)) = Va·cos(Ωt − sign·δ_e) + w·Va·m_e
    δ_e = β_e − ψ0,  β_e = atan2(n_e_y, n_e_x)   （注意 cos δ_e = g_e, sin δ_e = q_e）
    ⟹ rate_e(t) = 0 ⟺ cos(Ωt − sign·δ_e) = −w·m_e
    ⟹ 首窗口末端 T_e = [ arccos(−w·m_e) + sign·δ_e ] / Ω      （首窗口起点 t=0，因 rate_e(0)>0）

**闭式 d***（对绑定 (sign, edge)）：

    room_turn_e = d0_e − R − w·Va·m_e·T_e
    τ_sign(s) = min over {e : rate_e > 0} of room_turn_e / rate_e
    d* = min over sign of ( s 使 τ_sign(s) = 0 )

    对相邻边且 q_e = +cos(θ/2)（即 σ_e=+1）之一，显式解为
        s* = [ R·cos(θ/2) − m_e·( δd − w·Va·T_e ) ] / sin(θ/2)

**预言**：
  P2-1：`dmin_turn_e = d0_e − w·Va·m_e·T_e` 在数值上精确成立（容差 1e-9）。
  P2-2：闭式 d* 与臂 I 数值 d* 一致（容差 1e-7）。
  P2-3：**K9 的"只由 θ 决定"在有风时失效**：d* 依赖顶点相对风向的角度。

**三件套**：
  (a) 负对照：w=0 时闭式退化为 R·cot(θ/2)；
  (b) 正对照：漏掉 w·Va·m_e·T_e（转弯消耗）后必须被探测；
  (c) 交叉验证：闭式 d* vs 臂 I 数值 d*。
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
OM = J.OMEGA
TWO_PI = 2 * np.pi


# ------------------------------------------------------------------ 场景
def ngon_scenario(n, w, phi_wind=0.0, radius=212.13, alpha=0.0, j=0):
    a = np.linspace(0, TWO_PI, n, endpoint=False) + alpha
    V = J.normalize_radius(radius * np.stack([np.cos(a), np.sin(a)], axis=-1))
    ns, cs, shifts, V_s = J.scaled_geometry(V, w, VA, phi_wind)
    cs_s = cs - shifts
    xv = V_s[j]
    adj = [e for e in range(len(ns)) if abs(cs_s[e] - ns[e] @ xv) < 1e-6]
    if len(adj) != 2:
        raise ValueError("相邻边数不为 2")
    b_out = ns[adj[0]] + ns[adj[1]]
    b_out = b_out / np.linalg.norm(b_out)
    return dict(ns=ns, cs=cs, shifts=shifts, V_s=V_s, xv=xv, adj=adj,
                b_out=b_out, n=n, w=w, phi_wind=phi_wind)


def edge_params(sc):
    """对全部边计算 (g, q, m, beta, delta, rate0)。"""
    ns, b_out, w, phi_wind = sc["ns"], sc["b_out"], sc["w"], sc["phi_wind"]
    d_w = np.array([np.cos(phi_wind), np.sin(phi_wind)])
    b_perp = np.array([-b_out[1], b_out[0]])
    psi0 = float(np.arctan2(b_out[1], b_out[0]))
    g = ns @ b_out
    q = ns @ b_perp
    m = np.maximum(0.0, ns @ d_w)
    beta = np.arctan2(ns[:, 1], ns[:, 0])
    delta = np.arctan2(np.sin(beta - psi0), np.cos(beta - psi0))   # 归一化到 (-pi,pi]
    return dict(g=g, q=q, m=m, beta=beta, delta=delta, psi0=psi0, d_w=d_w,
                b_perp=b_perp)


def window_end(sign, delta_e, m_e, w, min_len=0.0):
    """rate_e(t) 的**首个正窗口**末端 T_e（解析）。

    rate_e(t) = Va·cos(Ωt − sign·δ_e) + w·Va·m_e > 0
    ⟺ u = Ωt − sign·δ_e ∈ (−A, A) + 2πk,  A = arccos(−w·m_e)
    """
    if w <= 0 or m_e <= 0:
        # 无风致漂移：d_e 不随时间变，转弯不消耗室间 → 返回 0（无消耗）
        return 0.0
    A = np.arccos(-w * m_e)
    u0 = -sign * delta_e
    # 找首个 u > u0 且 cos u > -w*m_e 的开区间
    k = 0
    # 候选区间起点：u ∈ (-A, A) + 2πk
    # 从 k = floor 附近开始搜
    k0 = int(np.floor((u0 + A) / TWO_PI))
    for kk in range(k0 - 2, k0 + 4):
        lo = -A + TWO_PI * kk
        hi = A + TWO_PI * kk
        if hi <= u0:
            continue
        u_start = max(u0, lo)
        if u_start < hi:
            # 首窗口 [u_start, hi]
            T = (hi + sign * delta_e) / OM
            return max(0.0, T)
    return 0.0


# ------------------------------------------------------------------ 闭式 τ
def tau_closed(s, sc, ep, theta, use_turn=True):
    ns, cs, xv, b_out, w = sc["ns"], sc["cs"], sc["xv"], sc["b_out"], sc["w"]
    sign_list = (+1, -1)
    best = -np.inf
    for sign in sign_list:
        t = np.inf
        ok = True
        for e in range(len(ns)):
            rate_e = VA * ep["g"][e] + w * VA * ep["m"][e]
            if rate_e <= 1e-12:
                continue
            room = (J.delta_d(w) * ep["m"][e] + s * ep["g"][e]
                    - sign * R * ep["q"][e])
            if use_turn:
                T = window_end(sign, ep["delta"][e], ep["m"][e], w)
                room -= w * VA * ep["m"][e] * T
            cand = room / rate_e
            if cand < t:
                t = cand
        if t == np.inf:
            continue
        if t > best:
            best = t
    return best


def dstar(f_of_s, dmax, tol=1e-12, maxit=90):
    lo, hi = 0.0, dmax
    v0 = f_of_s(0.0)
    if np.isfinite(v0) and v0 > 0:
        return 0.0
    vh = f_of_s(dmax)
    if not (np.isfinite(vh) and vh > 0):
        return np.nan
    for _ in range(maxit):
        mid = 0.5 * (lo + hi)
        v = f_of_s(mid)
        if np.isfinite(v) and v > 0:
            hi = mid
        else:
            lo = mid
        if hi - lo < tol:
            break
    return 0.5 * (lo + hi)


def dstar_numeric(sc, dmax=None):
    dmax = dmax if dmax else 3.0 * R
    ns, cs, xv, b_out, w = sc["ns"], sc["cs"], sc["xv"], sc["b_out"], sc["w"]
    psi0 = float(np.arctan2(b_out[1], b_out[0]))
    return dstar(lambda s: J.tau_crit_analytic_joint(
        xv - s * b_out, psi0, ns, cs, w, R, va=VA, phi_wind=sc["phi_wind"])[0], dmax)


print("=" * 104)
print("P2  有风时 d* 的解析闭式（含转弯段消耗 = 圆心风致漂移）")
print("=" * 104)
print(f"R = {R:.6f} m, Va = {VA}, omega = {np.degrees(OM):.4f} deg/s")
print()

# ================================================================= 三件套
print("[三件套]")
print("-" * 104)

# (a) 负对照：w=0 → R*cot(theta/2)
rows_a = []
for n in (3, 4, 5, 6, 7, 8):
    sc = ngon_scenario(n, 0.0)
    ep = edge_params(sc)
    theta = np.pi - np.arccos(np.clip(sc["ns"][sc["adj"][0]] @ sc["ns"][sc["adj"][1]], -1, 1))
    dc = dstar(lambda s: tau_closed(s, sc, ep, theta), 3.0 * R)
    ex = R / np.tan(theta / 2)
    rows_a.append((n, np.degrees(theta), dc, ex, abs(dc - ex)))
worst_a = max(r[4] for r in rows_a)
ok_a = worst_a < 1e-9
print(f"  (a) 负对照  : w=0 闭式 vs R*cot(theta/2)，{len(rows_a)} 组，最大差 {worst_a:.3e} m"
      f" -> {'通过' if ok_a else '不通过'}")

# (b) 正对照：漏转弯消耗
worst_b = 0.0
for n in (3, 4, 5, 6):
    for w in (0.1, 0.3, 0.5):
        sc = ngon_scenario(n, w)
        ep = edge_params(sc)
        theta = np.pi - np.arccos(np.clip(sc["ns"][sc["adj"][0]] @ sc["ns"][sc["adj"][1]], -1, 1))
        d1 = dstar(lambda s: tau_closed(s, sc, ep, theta, True), 3.0 * R)
        d0 = dstar(lambda s: tau_closed(s, sc, ep, theta, False), 3.0 * R)
        if np.isfinite(d1) and np.isfinite(d0):
            worst_b = max(worst_b, abs(d1 - d0))

ok_b = worst_b > 0.1
print(f"  (b) 正对照  : 漏转弯消耗项 -> d* 最大偏差 {worst_b:.4f} m"
      f" -> 有鉴别力：{'通过' if ok_b else '不通过'}")

# (c) 交叉验证：闭式 d* vs 臂 I 数值
worst_c = 0.0
rows_c = []
for n in (3, 4, 5, 6, 7, 8):
    for w in (0.0, 0.1, 0.3, 0.5):
        sc = ngon_scenario(n, w)
        ep = edge_params(sc)
        theta = np.pi - np.arccos(np.clip(sc["ns"][sc["adj"][0]] @ sc["ns"][sc["adj"][1]], -1, 1))
        dc = dstar(lambda s: tau_closed(s, sc, ep, theta), 3.0 * R)
        dn = dstar_numeric(sc)
        if np.isfinite(dc) and np.isfinite(dn):
            d = abs(dc - dn)
            worst_c = max(worst_c, d)
            rows_c.append((n, np.degrees(theta), w, dc, dn, d))
        else:
            rows_c.append((n, np.degrees(theta), w, dc, dn, np.nan))
ok_c = worst_c < 1e-7
print(f"  (c) 交叉验证: 闭式 vs 臂 I 数值，{len([r for r in rows_c if np.isfinite(r[5])])} 组有效，"
      f"最大差 {worst_c:.3e} m -> {'通过' if ok_c else '不通过'}")
print()

print("[A. 主表]")
print("-" * 104)
print(f"{'n':>3}{'theta':>9}{'w':>6}{'d*(闭式)':>13}{'d*(数值)':>13}{'差':>10}"
      f"{'Rcot(t/2)':>12}{'Rcot−δd':>12}")
for (n, th, w, dc, dn, d) in rows_c:
    rcot = R / np.tan(np.radians(th) / 2)
    print(f"{n:>3}{th:>9.3f}{w:>6.2f}{dc:>13.6f}{dn:>13.6f}{d:>10.2e}"
          f"{rcot:>12.6f}{rcot - J.delta_d(w):>12.6f}")

print()
print("=" * 104)
print("[判定]")
print("=" * 104)
print(f"  (a) 负对照          : {'通过' if ok_a else '不通过'}（w=0 退化为 R·cot(θ/2)）")
print(f"  (b) 正对照          : {'通过' if ok_b else '不通过'}（转弯消耗项必要）")
print(f"  (c) 交叉验证        : {'通过' if ok_c else '不通过'}")

# 显式公式核查
print()
print("[B. 显式公式核查：s* = [R·cos(θ/2) − m_e(δd − w·Va·T_e)] / sin(θ/2)]")
print("-" * 104)
print(f"{'n':>3}{'w':>6}{'绑定sign':>9}{'绑定边':>7}{'m_e':>7}{'T_e':>9}"
      f"{'显式s*':>12}{'数值d*':>12}{'差':>10}")
for n in (3, 4, 6):
    for w in (0.1, 0.3, 0.5):
        sc = ngon_scenario(n, w)
        ep = edge_params(sc)
        theta = np.pi - np.arccos(np.clip(sc["ns"][sc["adj"][0]] @ sc["ns"][sc["adj"][1]], -1, 1))
        st, ct = np.sin(theta / 2), np.cos(theta / 2)
        dn = dstar_numeric(sc)
        # 找绑定 (sign, edge)：在 d* 处 room/rate 最小者
        best = None
        for sign in (+1, -1):
            for e in range(len(sc["ns"])):
                rate_e = VA * ep["g"][e] + w * VA * ep["m"][e]
                if rate_e <= 1e-12:
                    continue
                room = (J.delta_d(w) * ep["m"][e] + dn * ep["g"][e] - sign * R * ep["q"][e])
                if w > 0 and ep["m"][e] > 0:
                    T = window_end(sign, ep["delta"][e], ep["m"][e], w)
                    room -= w * VA * ep["m"][e] * T
                t = abs(room)
                if best is None or t < best[0]:
                    best = (t, sign, e, room, rate_e)
        _, sign, e, room, rate_e = best
        T = window_end(sign, ep["delta"][e], ep["m"][e], w)
        # 显式解（仅当绑定边为相邻边且 g_e = sin(θ/2)）
        if e in sc["adj"] and abs(ep["g"][e] - st) < 1e-12:
            s_exp = (sign * R * ep["q"][e] - ep["m"][e] * (J.delta_d(w) - w * VA * T)) / st
            tag = ""
        else:
            s_exp = np.nan
            tag = "  (绑定边非相邻边，显式式不适用)"
        print(f"{n:>3}{w:>6.2f}{sign:>+9}{e:>7}{ep['m'][e]:>7.3f}{T:>9.4f}"
              f"{s_exp:>12.5f}{dn:>12.5f}"
              f"{(abs(s_exp-dn) if np.isfinite(s_exp) else float('nan')):>10.2e}{tag}")
