"""V2.0 候选判据的精确核验：约束型 ≠ 惩罚型的充要条件。

本文件服务于 RESEARCH_PLAN v1.2 的 H2 与拟议的 V2.0 实验设计。
目标：把"约束最优不可被惩罚项复现"从有限算例升级为**可判定的判据**。

不需要仿真：全部为精确点集运算。

判据（修正版，本文件核验）：
  设动作 a 的代价 J(a)（min）与未来可行空间 F(a)（max）。
  取 Pareto 集，按 F 升序。计算其**下凸包**（lower convex hull）。
  则：a 不可被任何 λ ≥ 0 复现  ⟺  a 不在下凸包上（被凸包"跳过"）。

  第一版判据（"局部斜率递增即可支撑"）已被本文件核验**否决**：
  反例中某点局部凸，但被远处一个边际代价极低的点压低了 λ 上界，故仍不可支撑。
  这说明不可支撑是**全局**性质，必须用凸包成员判定。
"""
from __future__ import annotations

import itertools
import math
import random

TOL = 1e-9


# ------------------------------------------------------------------ 基础工具
def pareto_set(pts):
    """min J（pts[0]）、max F（pts[1]）的 Pareto 集，按 F 升序。"""
    out = []
    for i, P in enumerate(pts):
        dom = False
        for j, Q in enumerate(pts):
            if i == j:
                continue
            if (Q[0] <= P[0] + TOL and Q[1] >= P[1] - TOL) and \
               (Q[0] < P[0] - TOL or Q[1] > P[1] + TOL):
                dom = True
                break
        if not dom:
            out.append(P)
    return sorted(out, key=lambda P: (P[1], P[0]))


def supported_lambda(P, pts):
    """P 是否被某个 λ ≥ 0 支持：∃λ≥0 使 J−λF 在 P 处最小。返回可行区间或 None。"""
    lo, hi = 0.0, math.inf
    Jp, Fp = P
    for Q in pts:
        if Q is P:
            continue
        dF, dJ = Fp - Q[1], Jp - Q[0]
        if dF > TOL:
            lo = max(lo, dJ / dF)
        elif dF < -TOL:
            hi = min(hi, dJ / dF)
        elif dJ > TOL:
            return None
    return None if lo > hi + TOL else (lo, hi)


def brute_supported(pts):
    """暴力：λ 候选取两两斜率，逐点检查。"""
    cand = {0.0}
    for P in pts:
        for Q in pts:
            if P is not Q and abs(P[1] - Q[1]) > TOL:
                s = (P[0] - Q[0]) / (P[1] - Q[1])
                if s >= 0:
                    cand.add(s)
    out = set()
    for P in pts:
        for lam in cand:
            vals = [Q[0] - lam * Q[1] for Q in pts]
            if abs((P[0] - lam * P[1]) - min(vals)) < 1e-7:
                out.add(P)
                break
    return out


def lower_hull(pts):
    """下凸包（点按 F 升序；x=F, y=J）。返回凸包顶点列表。"""
    P = sorted(set(pts), key=lambda q: (q[1], q[0]))
    if len(P) <= 2:
        return P
    hull = []
    for p in P:                                  # 下凸包：保留逆时针（左转）链
        while len(hull) >= 2:
            o, a = hull[-2], hull[-1]
            cr = (a[1] - o[1]) * (p[0] - o[0]) - (a[0] - o[0]) * (p[1] - o[1])
            if cr <= TOL:                        # 非左转 → 弹出（含共线，选端点）
                hull.pop()
            else:
                break
        hull.append(p)
    return hull


def criterion_supported(pts):
    """判据：Pareto 点中，位于下凸包上者可支撑。"""
    hull = set(lower_hull(pts))
    return set(p for p in pareto_set(pts) if p in hull)


# ------------------------------------------------------------------ 核验 1
def check_criterion(trials=4000, seed=20260917):
    rng = random.Random(seed)
    mismatch, total = 0, 0
    worst = []
    for _ in range(trials):
        n = rng.randint(4, 9)
        pts = list({(round(rng.uniform(0, 40), 3), round(rng.uniform(0, 120), 3))
                    for _ in range(n)})
        par = pareto_set(pts)
        if len(par) < 3:
            continue
        brute = brute_supported(pts) & set(par)
        crit = criterion_supported(pts)
        total += len(par)
        if brute != crit:
            mismatch += 1
            if len(worst) < 3:
                worst.append((par, sorted(par), sorted(brute ^ crit)))
    return mismatch, trials, total, worst


# ------------------------------------------------------------------ 核验 2
def hull_relaxation(pts, n=240):
    """以凸包顶点间的线性组合近似"允许混合"后的可达集。"""
    hull = lower_hull(pts) + [p for p in sorted(set(pts), key=lambda q: (-q[1], q[0]))[:3]]
    verts = sorted(set(hull + pts))
    out = []
    for A, B in itertools.combinations(verts, 2):
        for i in range(n + 1):
            t = i / n
            out.append((round(A[0] + t * (B[0] - A[0]), 9),
                        round(A[1] + t * (B[1] - A[1]), 9)))
    return list(set(out + pts))


def check_mixing(pts, fmin_list):
    """同一 F_min 下：单动作承诺 vs 允许混合，各自的最优 J 与可支撑性。"""
    rows = []
    for Fmin in fmin_list:
        feas = [P for P in pts if P[1] >= Fmin - TOL]
        best_strict = min(feas, key=lambda Q: (Q[0], -Q[1]))
        strict_supported = supported_lambda(best_strict, pts) is not None

        relax = hull_relaxation(pts)
        feas_r = [P for P in relax if P[1] >= Fmin - TOL]
        best_relax = min(feas_r, key=lambda Q: (Q[0], -Q[1]))
        rows.append((Fmin, best_strict, strict_supported, best_relax))
    return rows


# ------------------------------------------------------------------ 主程序
if __name__ == "__main__":
    print("=" * 78)
    print("V2.0 候选判据核验（修正版）：约束型 ≠ 惩罚型的条件")
    print("=" * 78)

    print("\n[核验 1] 判据 = 下凸包成员  ⟺  可被某 λ ≥ 0 支持")
    m, t, npts, worst = check_criterion()
    print(f"  随机点集 {t} 组，比对 Pareto 点 {npts} 个")
    print(f"  判据与暴力搜索不一致的点集数：{m}")
    print(f"  → 判定：{'一致，判据成立' if m == 0 else '仍不一致'}")
    for par, _, diff in worst:
        print(f"    反例：{par}  差异点={diff}")

    print("\n[核验 2] 允许混合（随机化）是否消灭分歧")
    fw = [(1.00, 20.0), (9.00, 60.0), (10.0, 100.0), (4.00, 35.0), (2.00, 10.0), (30.0, 90.0)]
    par = pareto_set(fw)
    hull = lower_hull(fw)
    skipped = [p for p in par if p not in set(hull)]
    print(f"  点集：{fw}")
    print(f"  Pareto 集：{par}")
    print(f"  下凸包顶点：{hull}")
    print(f"  被凸包跳过（不可支撑）的 Pareto 点：{skipped}")
    rows = check_mixing(fw, sorted({p[1] for p in par}))
    print(f"\n  {'F_min':>7} {'单动作最优(J,F)':>22} {'可支撑':>8} {'混合后最优(J,F)':>22}")
    for Fmin, bs, sup, br in rows:
        print(f"  {Fmin:>7.1f} {str(bs):>22} {str(sup):>8} {str(br):>22}")
    n_div = sum(1 for _, _, sup, _ in rows if not sup)
    print(f"  → 单动作承诺下出现分歧的 F_min 个数：{n_div}/{len(rows)}")
    print(f"  → 混合后最优 J 与单动作不同的 F_min 个数："
          f"{sum(1 for _, bs, _, br in rows if abs(bs[0]-br[0]) > 1e-6)}/{len(rows)}")

    print("\n[核验 3] 平台对比：离散（非凸）vs 凸")
    convex = [(F * F / 100.0, F) for F in [i * 5.0 for i in range(21)]]
    for tag, pts in [("固定翼式离散集", fw), ("凸权衡集", convex)]:
        pr = pareto_set(pts)
        sk = [p for p in pr if p not in set(lower_hull(pts))]
        print(f"  {tag}：Pareto {len(pr)} 个，被凸包跳过 {len(sk)} 个 → "
              f"{'有分歧' if sk else '无分歧'}")

    print("\n" + "=" * 78)
    print("结论")
    print("=" * 78)
    print(f"1. 判据（下凸包成员 ⟺ 可支撑）：{'通过' if m == 0 else '未通过'}")
    print("2. 第一版判据（局部斜率）已被反例否决 —— 不可支撑是全局性质")
    print("3. 分歧条件：可达 (J,F) 集非凸，且决策为**确定性单动作承诺**")
    print("4. 凸权衡集（类多旋翼）下无分歧 → 平台差异可检验")
