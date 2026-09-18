"""EXP-FW-V1-26: 联合条件下的方向依赖延迟预算（主实验）。

预注册：experiments/EXP-FW-V1-26-preregistration.md
依据：V2.1 第 4 节（原始规格）+ V2.2 第 3.2 节（基准改联合条件）
前置探索：notes/exp26_horizon_wellposedness.py
          （发现：顶点处 τ_crit < 0，无正允许延迟 → 三区场景设计）

== 独立性要求（预注册 4.2，硬条件）==
本脚本**不得**调用 EXP-27 的 required() 或 27A 的 pen_vec()。
臂 I 必须从**控制律 + 运动学积分**独立实现。允许：numpy、围栏几何（半平面）。
交叉验证在 §C3 中显式进行（比较对象是独立实现的解析式）。

== 机动模型（冻结）==
  1. 延迟 τ：沿初始航向 ψ0 直飞（地面速度 v_g = Va·e(ψ0) + W）
  2. 转弯：以最大速率按 sign 转弯；围栏跟随控制器接管后停止评价
  3. 联合条件：转弯圆盘对所有边同时可行（圆盘填充）

== 三区场景（预注册第 3 节）==
  A 区：边中点（τ_crit > 0）——H1/H2/H3
  B 区：缩放层顶点（τ_crit < 0）——K8 的任务层确认
  C 区：顶点向内过渡（定位临界距离 d*）

== 执行顺序（负责人指定，不得颠倒）==
  1 skeleton → 2 独立臂 I → 3 P1b 正对照 → 4 负对照 → 5 解析交叉 → 6 主扫描
"""
from __future__ import annotations

import csv
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

VA_DEFAULT = 18.0
OMEGA = np.deg2rad(25.0)
R = VA_DEFAULT / OMEGA
TWO_PI = 2.0 * np.pi
N_T = 4001          # 运动学积分的时间网格（单条轨迹，非各边混用）


# ============================================================ 几何（允许使用）
def hrep_from_verts(V):
    """逆时针凸多边形 → 半平面表示 n·x ≤ c。"""
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


def delta_d(w, va=VA_DEFAULT):
    """JAIS 2020 的方向缓冲（常值风）。"""
    r = va / OMEGA
    return 0.0 if w <= 0 else r * np.sqrt(1 - w**2) + w * r * np.arccos(-w)


def scaled_geometry(V, w, va=VA_DEFAULT, phi_wind=0.0):
    """缩放层：c'_e = c_e − δu − δd·max(0, n_e·d_wind)。返回 ns, cs, shifts, V_s。"""
    ns, cs = hrep_from_verts(V)
    r = va / OMEGA
    d_wind = np.array([np.cos(phi_wind), np.sin(phi_wind)])
    shifts = r + delta_d(w, va) * np.maximum(0.0, ns @ d_wind)
    return ns, cs, shifts, verts_from_hrep(ns, cs - shifts)


def rectangle(wid, hei, alpha=0.0):
    base = np.array([[-wid / 2, -hei / 2], [wid / 2, -hei / 2],
                     [wid / 2, hei / 2], [-wid / 2, hei / 2]])
    ca, sa = np.cos(alpha), np.sin(alpha)
    return base @ np.array([[ca, sa], [-sa, ca]])


def normalize_radius(V, target=212.13):
    c = V.mean(axis=0)
    Vc = V - c
    return Vc * (target / max(1e-12, np.max(np.linalg.norm(Vc, axis=1))))


# ============================================================ 臂 I：独立实现
def v_ground(psi, w, va=VA_DEFAULT, phi_wind=0.0):
    """地面速度向量（常值风）。"""
    return np.array([va * np.cos(psi) + w * va * np.cos(phi_wind),
                     va * np.sin(psi) + w * va * np.sin(phi_wind)])


def rolling_center(x0, psi0, sign, r):
    """转弯圆心（瞬时转弯；一阶滚转由臂 R 单独处理）。"""
    return np.asarray(x0, float) + sign * r * np.array([-np.sin(psi0), np.cos(psi0)])


def tau_crit_analytic_joint(x0, psi0, ns, cs, w, r, va=VA_DEFAULT, phi_wind=0.0,
                            rate_tol=1e-9):
    """联合条件下的 τ_crit 解析式（臂 I 的预言）。

    圆心 c(τ) = x0 + v_g·τ + sign·R·(−sinψ0, cosψ0) 对 τ 线性
    条件：d_e(τ) = c_e − n_e·c(τ) ≥ R 对所有 e

    **两类边**（27A 掠射教训的直接应用）：
      1) 推进边（n_e·v_g > 0）：τ_crit 由 [d_e(0) − R]/(n_e·v_g) 决定；
      2) **掠射边（|n_e·v_g| ≈ 0）**：延迟不改变其 d_e，但**转弯段会**；
         若转弯段使 d_e < R，则该 sign 在任何 τ 下都不可行 → τ_crit = −inf。

    本函数与 `_turn_segment_min_de` 均为本脚本独立实现，
    不调用 EXP-27 的 required() 或 27A 的 pen_vec()。
    """
    vg = v_ground(psi0, w, va, phi_wind)
    rates = ns @ vg
    out = {}
    for sign in (+1, -1):
        c0 = rolling_center(x0, psi0, sign, r)
        d0 = cs - ns @ c0
        # 转弯段（无延迟）中圆心到各边的最小距离
        dmin_turn = np.array([
            _turn_segment_min_de(x0, psi0, sign, ns[e], cs[e], w, r, va, phi_wind)
            for e in range(len(ns))
        ])
        # 关键：延迟段与转弯段共用同一速率偏移 rate_e，
        # 故整体最小 d_e = min(d0_e, dmin_turn_e) − rate_e·τ
        m_e = np.minimum(d0, dmin_turn)
        best = np.inf
        for e in range(len(ns)):
            room = m_e[e] - r
            if rates[e] > rate_tol:
                t_e = room / rates[e]
                if t_e < best:
                    best = t_e
            elif room < 0:
                best = -np.inf      # 即使零延迟也不足（转弯本身已越界）
                break
        out[sign] = best
    return max(out[+1], out[-1]), out


def _turn_segment_min_de(x0, psi0, sign, n_e, c_e, w, r, va, phi_wind, n_t=N_T):
    """转弯段（无延迟）中圆心到边 e 的最小距离，**限定在该边仍被推进的连续时段内**。

    窗口定义必须与 `simulate_arm_I` 一致：从首次 "n_e·v_g > 0" 开始，
    到该条件首次中断为止。窗口之外由控制器接管，不评价。
    """
    t = np.linspace(0.0, TWO_PI / OMEGA, n_t)
    psi = psi0 + sign * OMEGA * t
    dx = sign * r * (np.sin(psi) - np.sin(psi0)) + w * va * np.cos(phi_wind) * t
    dy = -sign * r * (np.cos(psi) - np.cos(psi0)) + w * va * np.sin(phi_wind) * t
    x = np.asarray(x0, float) + np.stack([dx, dy], axis=-1)
    vgx = va * np.cos(psi) + w * va * np.cos(phi_wind)
    vgy = va * np.sin(psi) + w * va * np.sin(phi_wind)
    rate = vgx * n_e[0] + vgy * n_e[1]
    moving = rate > 1e-12
    if not moving.any():
        # 全程不推进：d_e 不因转弯减小，返回初始值（不构成约束）
        c0 = np.asarray(x0, float) + sign * r * np.array([-np.sin(psi0), np.cos(psi0)])
        return float(c_e - c0 @ n_e)
    i0 = int(np.argmax(moving))
    i1 = i0
    while i1 + 1 < len(moving) and moving[i1 + 1]:
        i1 += 1
    center = x + sign * r * np.stack([-np.sin(psi), np.cos(psi)], axis=-1)
    d = c_e - center @ n_e
    return float(np.min(d[i0:i1 + 1]))


def simulate_arm_I(x0, psi0, sign, tau_delay, ns, cs, w, r, va=VA_DEFAULT,
                   phi_wind=0.0, n_t=N_T):
    """臂 I 的运动学积分（**独立于任何 required/pen 实现**）。

    阶段 1：沿 ψ0 直飞 τ_delay
    阶段 2：以最大速率按 sign 转弯，**直到该边不再被推进**（首次外摆口径）

    评价窗口（冻结，与预注册一致）：对每条边 e，只评价"n_e·v_g > 0 的时段"，
    因为一旦 n_e·v_g ≤ 0，飞机不再朝该边前进，控制器可接管 → 评价结束。
    **不得**取整周期最大（那会退回 27A v3 的视界错误，且量不良定义）。

    返回 (worst_over, violated)：worst_over = max_e max_{推进时段} [d_e(t) 的越界量]，
    其中圆盘越界量 = R − d_e(t)（d_e 为圆心到边距离），圆心 = x(t) + sign·R·(−sinψ(t), cosψ(t))。
    """
    # 时间序列：延迟段（含端点）+ 转弯段（去掉 t=0 的重复点）
    if tau_delay > 0:
        n_fly = max(2, int(n_t * tau_delay / 10.0) + 2)
        t_fly = np.linspace(0.0, tau_delay, n_fly)
        t_turn = np.linspace(0.0, TWO_PI / OMEGA, n_t)[1:]
        t_all = np.concatenate([t_fly, tau_delay + t_turn])
    else:
        t_fly = np.array([0.0])
        t_turn = np.linspace(0.0, TWO_PI / OMEGA, n_t)
        t_all = t_turn

    # 位置：直飞段 + 转弯段
    x = np.empty((len(t_all), 2))
    if tau_delay > 0:
        vg0 = v_ground(psi0, w, va, phi_wind)
        x[:len(t_fly)] = np.asarray(x0, float) + np.outer(t_fly, vg0)
        x_start_turn = x[len(t_fly) - 1]
        psi_turn = psi0 + sign * OMEGA * t_turn
        dx = sign * r * (np.sin(psi_turn) - np.sin(psi0)) + w * va * np.cos(phi_wind) * t_turn
        dy = -sign * r * (np.cos(psi_turn) - np.cos(psi0)) + w * va * np.sin(phi_wind) * t_turn
        x[len(t_fly):] = x_start_turn + np.stack([dx, dy], axis=-1)
    else:
        n_fly = 0
        x_start_turn = np.asarray(x0, float)
        psi_turn = psi0 + sign * OMEGA * t_turn
        dx = sign * r * (np.sin(psi_turn) - np.sin(psi0)) + w * va * np.cos(phi_wind) * t_turn
        dy = -sign * r * (np.cos(psi_turn) - np.cos(psi0)) + w * va * np.sin(phi_wind) * t_turn
        x[:] = x_start_turn + np.stack([dx, dy], axis=-1)

    # 逐边评价（**只在从首次推进开始的连续推进段**；这是良定义的窗口）
    worst = -np.inf
    for e in range(len(ns)):
        n_e, c_e = ns[e], cs[e]
        vg = np.empty((len(t_all), 2))
        if tau_delay > 0:
            vg[:len(t_fly)] = v_ground(psi0, w, va, phi_wind)
            vg[len(t_fly):] = np.stack(
                [va * np.cos(psi_turn) + w * va * np.cos(phi_wind),
                 va * np.sin(psi_turn) + w * va * np.sin(phi_wind)], axis=-1)
        else:
            vg[:] = np.stack(
                [va * np.cos(psi_turn) + w * va * np.cos(phi_wind),
                 va * np.sin(psi_turn) + w * va * np.sin(phi_wind)], axis=-1)
        rate = vg @ n_e
        moving = rate > 1e-12
        if not moving.any():
            continue
        i0 = int(np.argmax(moving))                 # 首次推进
        i1 = i0
        while i1 + 1 < len(moving) and moving[i1 + 1]:
            i1 += 1                                 # 连续推进段结束
        psi_all = np.concatenate([np.full(len(t_fly), psi0), psi_turn]) if tau_delay > 0 \
            else psi_turn
        center = x + sign * r * np.stack([-np.sin(psi_all), np.cos(psi_all)], axis=-1)
        d = c_e - center @ n_e                      # 圆心到边距离
        over = r - d                                # 圆盘越界量（>0 即越界）
        m = float(np.max(over[i0:i1 + 1]))
        worst = max(worst, m)
    return worst, (worst > 1e-9)


def tau_crit_measured(x0, psi0, ns, cs, w, r, va=VA_DEFAULT, phi_wind=0.0,
                      lo=0.0, hi=30.0, iters=80, tol=1e-12):
    """臂 I 的 τ_crit：二分求"首次出现越界"的延迟。返回 (tau_crit, 是否可行)。"""
    def violated(tau):
        for sign in (+1, -1):
            _, v = simulate_arm_I(x0, psi0, sign, tau, ns, cs, w, r, va, phi_wind)
            if not v:
                return False          # 存在可行转向 → 不越界
        return True

    if violated(lo):
        # 零延迟即越界 → 二分负侧
        lo2, hi2 = -hi, 0.0
        for _ in range(iters):
            mid = 0.5 * (lo2 + hi2)
            if violated(mid):
                hi2 = mid
            else:
                lo2 = mid
        return 0.5 * (lo2 + hi2), False
    if not violated(hi):
        return np.inf, True
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        if violated(mid):
            hi = mid
        else:
            lo = mid
        if hi - lo < tol:
            break
    return 0.5 * (lo + hi), True


# ============================================================ 三件套
def setup_rect(w, va=VA_DEFAULT, wid=600.0, hei=600.0):
    V = normalize_radius(rectangle(wid, hei, 0.0))
    ns, cs, shifts, V_s = scaled_geometry(V, w, va)
    return V, ns, cs, shifts, V_s


def edge_midpoint(V_s, ns, cs, e):
    """A 区：边 e 的中点。"""
    return (V_s[e] + V_s[(e + 1) % len(V_s)]) / 2


def c3_analytic_crosscheck(w_list=(0.0, 0.1, 0.3, 0.5)):
    """§C3：臂 I 的解析式与独立解析实现交叉（同式不同实现路径）。"""
    print("\n[C3] 解析交叉：τ_crit 解析式 vs 数值二分（臂 I 独立积分）")
    print(f"   {'w':>5} {'位置':>10} {'解析τ':>10} {'数值τ':>10} {'差':>10}")
    worst = 0.0
    for w in w_list:
        V, ns, cs, shifts, V_s = setup_rect(w)
        for tag, x0 in (("边中点", edge_midpoint(V_s, ns, cs, 0)),
                        ("顶点", V_s[0])):
            psi_out = 0.0 if tag == "边中点" else float(
                np.arctan2(V[0][1] - x0[1], V[0][0] - x0[0]))
            ana, _ = tau_crit_analytic_joint(x0, psi_out, ns, cs, w, R)
            meas, feasible = tau_crit_measured(x0, psi_out, ns, cs, w, R)
            d = abs(ana - meas) if np.isfinite(ana) and np.isfinite(meas) else 0.0
            worst = max(worst, d)
            fa = f"{ana:.5f}" if np.isfinite(ana) else "inf"
            fm = f"{meas:.5f}" if np.isfinite(meas) else "inf"
            print(f"   {w:>5.1f} {tag:>10} {fa:>10} {fm:>10} {d:>10.2e}")
    print(f"   → 最大差 {worst:.2e} m；{'一致' if worst < 1e-6 else '不一致'}")
    return worst


def p1b_positive_control():
    """Step 3: positive control -- vertex must report a violation, magnitude R*cos(theta/2)."""
    print("")
    print("[P1b 正对照] 顶点（B 区），tau=0 应越界，量应 = R*cos(theta/2)")
    pred = R * np.cos(np.pi / 4)      # 矩形内角 90 度
    print(f"   {'w':>5} {'sign':>5} {'越界量(m)':>11} {'预测':>10} {'差':>10}")
    worst = 0.0
    for w in (0.0, 0.1, 0.3, 0.5):
        V, ns, cs, shifts, V_s = setup_rect(w)
        x0 = V_s[0]
        psi = float(np.arctan2(V[0][1] - x0[1], V[0][0] - x0[0]))
        for sign in (+1, -1):
            m_, vi = simulate_arm_I(x0, psi, sign, 0.0, ns, cs, w, R)
            worst = max(worst, abs(m_ - pred))
            print(f"   {w:>5.1f} {sign:>+5d} {m_:>11.4f} {pred:>10.4f} {abs(m_ - pred):>10.2e}")
    ok = worst < 1e-9
    print(f"   -> {'通过' if ok else '不通过'}（最大差 {worst:.2e}）")
    return ok


def negative_control():
    """Step 4: negative control -- far from every edge, no violation expected."""
    print("")
    print("[负对照] 形心处（距各边 >= R），tau=0 应无越界")
    bad = tot = 0
    for w in (0.0, 0.1, 0.3, 0.5):
        V, ns, cs, shifts, V_s = setup_rect(w)
        c = V_s.mean(axis=0)
        for psd in range(0, 360, 45):
            psi = np.deg2rad(psd)
            for sign in (+1, -1):
                m_, vi = simulate_arm_I(c, psi, sign, 0.0, ns, cs, w, R)
                tot += 1
                bad += int(vi)
    ok = bad == 0
    print(f"   {tot} 组合，越界 {bad} 个 -> {'通过' if ok else '不通过'}")
    return ok


def analytic_cross():
    """Step 5: cross-validate arm I against the analytic formula, over approach directions."""
    print("")
    print("[解析交叉] 臂 I 数值 tau_crit vs 解析式（A 区，扫接近方向）")
    print(f"   {'w':>5} {'psi(deg)':>9} {'解析tau':>10} {'数值tau':>10} {'差':>10}")
    worst = 0.0
    n_cmp = 0
    for w in (0.0, 0.1, 0.3, 0.5):
        V, ns, cs, shifts, V_s = setup_rect(w)
        e = 0
        mid = edge_midpoint(V_s, ns, cs, e)
        x0 = mid + 1.0 * R * (-ns[e])
        for psd in (0, 45, 90, 135, 180, 225, 270, 315):
            psi = np.deg2rad(psd)
            ana, _ = tau_crit_analytic_joint(x0, psi, ns, cs, w, R)
            meas, _ = tau_crit_measured(x0, psi, ns, cs, w, R)
            if not (np.isfinite(ana) and np.isfinite(meas)):
                continue
            d = abs(ana - meas)
            worst = max(worst, d)
            n_cmp += 1
            if psd in (0, 90, 180):
                print(f"   {w:>5.1f} {psd:>9} {ana:>10.5f} {meas:>10.5f} {d:>10.2e}")
    ok = worst < 1e-3
    print(f"   -> 共比较 {n_cmp} 组；最大差 {worst:.2e} -> {'通过' if ok else '不通过'}")
    return ok


def main():
    print("=" * 78)
    print("EXP-FW-V1-26: 联合条件下的方向依赖延迟预算")
    print("=" * 78)
    print(f"R = {R:.4f} m；六步顺序：骨架 -> 臂 I -> P1b -> 负对照 -> 解析交叉 -> 主扫描")
    print("")
    print("[1-2] 骨架与独立臂 I 就绪（不调用 required()/pen_vec()）")

    ok_b = p1b_positive_control()
    ok_n = negative_control()
    ok_c = analytic_cross()

    print("")
    print("=" * 78)
    print("三件套总判")
    print("=" * 78)
    all_ok = ok_b and ok_n and ok_c
    print(f"  P1b 正对照 : {'通过' if ok_b else '不通过'}")
    print(f"  负对照     : {'通过' if ok_n else '不通过'}")
    print(f"  解析交叉   : {'通过' if ok_c else '不通过'}")
    if not all_ok:
        print("")
        print("  ** 三件套未全过 -> 主扫描结果不得讨论。**")
        return

    print("")
    print("[6] 主扫描：三区 x 接近方向（按预注册 4.1 扫描 phi）")
    os.makedirs("outputs", exist_ok=True)
    rows = []
    for w in (0.0, 0.1, 0.3, 0.5):
        V, ns, cs, shifts, V_s = setup_rect(w)
        e = 0
        mid = edge_midpoint(V_s, ns, cs, e)
        # A 区：边外 1R；C 区：0.25R；B 区：顶点
        positions = [("A1R", mid + 1.0 * R * (-ns[e]), True),
                     ("C0.25R", mid + 0.25 * R * (-ns[e]), True),
                     ("B_vertex", V_s[0], False)]
        for zone, x0, sweep in positions:
            if zone == "B_vertex":
                psi_list = [float(np.arctan2(V[0][1] - x0[1], V[0][0] - x0[0]))]
            else:
                psi_list = [np.deg2rad(p) for p in (0, 30, 45, 60, 90, 120, 135, 180,
                                                    225, 270, 315)]
            for psi in psi_list:
                ana, per = tau_crit_analytic_joint(x0, psi, ns, cs, w, R)
                meas, feas = tau_crit_measured(x0, psi, ns, cs, w, R)
                rows.append({"w": w, "zone": zone,
                             "psi_deg": float(np.degrees(psi)),
                             "x0_x": float(x0[0]), "x0_y": float(x0[1]),
                             "tau_analytic": float(ana) if np.isfinite(ana) else np.nan,
                             "tau_measured": float(meas) if np.isfinite(meas) else np.nan,
                             "zero_delay_violates": bool(ana < 0)})
        # 摘要打印
        sub = [r for r in rows if r["w"] == w]
        ta = [r["tau_analytic"] for r in sub if np.isfinite(r["tau_analytic"])]
        neg = [r for r in sub if r["zero_delay_violates"]]
        print(f"   w={w:>4.1f}: {len(sub)} 组；tau 范围 [{min(ta):.4f}, {max(ta):.4f}] s；"
              f"零延迟即越界 {len(neg)} 组")

    with open("outputs/exp_fw_v1_26_joint_latency.csv", "w", newline="",
              encoding="utf-8-sig") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        wr.writeheader()
        wr.writerows(rows)
    print("")
    print(f"wrote outputs/exp_fw_v1_26_joint_latency.csv（{len(rows)} 行）")

    # 方向依赖摘要
    print("")
    print("[方向依赖摘要] w=0.3，A1R 区，tau_crit 随接近方向")
    sub = sorted([r for r in rows if r["w"] == 0.3 and r["zone"] == "A1R"],
                 key=lambda r: r["psi_deg"])
    for r in sub:
        print(f"   psi={r['psi_deg']:>6.0f} deg  tau_crit={r['tau_analytic']:>9.4f} s")


if __name__ == "__main__":
    main()
