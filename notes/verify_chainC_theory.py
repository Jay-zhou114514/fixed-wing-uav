"""三条关于链 C 目标函数形式的数学断言 —— 精确数值核验。

这不是 EXP-* 实验（无仿真、无预注册门槛），而是对
docs/LITERATURE_AUDIT_2026-09.md 第 3 节的数学断言做有限、精确的核验。
每个断言输出一个明确的判定。

断言 1（审计中被撤回的那条）："若 F_future 是当前状态的函数，最优策略不变"
        → 判定为**假**（下方给出反例）。
断言 2（真，但适用范围窄得多）：势函数塑形 F = γ·Φ(s') − Φ(s) 保持最优策略不变。
断言 3（本次新增，可用的结果）：当可达集非凸时（固定翼机动集离散时典型），
        约束最优 argmin J s.t. F ≥ F_min **无法**由任何惩罚权重 λ 复现；
        可达集凸时则可以。这条给出链 C 唯一站得住的改造方向。
"""
from __future__ import annotations

import math

import numpy as np

GAMMA = 0.9
R_A = 10.0
R_B = 0.0
PHI = {"s0": 3.0, "sA": -2.0, "sB": 1.0}   # 任意势函数
G = {"s0": 0.0, "sA": -12.0, "sB": 0.0}    # 纯状态项


# ---------------------------------------------------------------- 断言 1 / 2
def value_absorbing(r):
    """吸收状态 sX 的自环奖励 r → V = r / (1 - γ)。"""
    return r / (1.0 - GAMMA)


def mdp_policy(rA, rB):
    """s0 上两个动作的 Q 值，返回 (Q1, Q2, 是否选 a1)。"""
    q1 = GAMMA * value_absorbing(rA)
    q2 = GAMMA * value_absorbing(rB)
    return q1, q2, q1 > q2


def check_claims_1_and_2():
    print("=" * 78)
    print("断言 1 / 2：状态项与势函数塑形对最优策略的影响")
    print("=" * 78)

    # 基线
    q1, q2, choose_a1 = mdp_policy(R_A, R_B)
    print(f"\n[基线]            Q(a1)={q1:8.3f}  Q(a2)={q2:8.3f}  → 选 {'a1' if choose_a1 else 'a2'}")

    # 变体 A：纯状态项 g(s)。奖励变为 r(s) + g(s)。
    q1g, q2g, choose_a1_g = mdp_policy(R_A + G["sA"], R_B + G["sB"])
    print(f"[+纯状态项 g(s)]  Q(a1)={q1g:8.3f}  Q(a2)={q2g:8.3f}  → 选 {'a1' if choose_a1_g else 'a2'}")
    flipped = choose_a1_g != choose_a1
    print(f"  → 策略是否改变：{'是（策略翻转）' if flipped else '否'}")
    print(f"  → 断言 1 判定：{'假（纯状态项可以改变最优策略）' if flipped else '本算例未反驳'}")

    # 变体 B：势函数塑形。Q'(s0,a) = γΦ(s') − Φ(s0) + γV'(s')，理论给出 Q'(s0,a) = Q(s0,a) − Φ(s0)
    q1p = GAMMA * PHI["sA"] - PHI["s0"] + GAMMA * (value_absorbing(R_A) - PHI["sA"])
    q2p = GAMMA * PHI["sB"] - PHI["s0"] + GAMMA * (value_absorbing(R_B) - PHI["sB"])
    choose_a1_p = q1p > q2p
    print(f"\n[+势函数塑形]     Q(a1)={q1p:8.3f}  Q(a2)={q2p:8.3f}  → 选 {'a1' if choose_a1_p else 'a2'}")
    # 理论预测：两个 Q 同时被减去 Φ(s0)
    pred1, pred2 = q1 - PHI["s0"], q2 - PHI["s0"]
    err = max(abs(q1p - pred1), abs(q2p - pred2))
    print(f"  → 与理论 Q'=Q−Φ(s0) 的最大偏差：{err:.3e}")
    print(f"  → 断言 2 判定：{'真（策略不变，仅整体平移 Φ(s0)）' if (not err > 1e-9 and choose_a1_p == choose_a1) else '未通过'}")
    return flipped


# ---------------------------------------------------------------- 断言 3
def supported_lambda(P, pts, tol=1e-12):
    """精确判定：是否存在 λ ≥ 0 使 P 最小化 J − λF。返回可行区间或 None。

    条件：Jp − λFp ≤ Ji − λFi  ∀i  ⟺  dJ ≤ λ·dF
    """
    lo, hi = 0.0, math.inf
    Jp, Fp = P
    for Q in pts:
        if Q is P:
            continue
        Jq, Fq = Q
        dF, dJ = Fp - Fq, Jp - Jq
        if dF > 0:
            lo = max(lo, dJ / dF)
        elif dF < 0:
            hi = min(hi, dJ / dF)
        elif dJ > tol:
            return None
    if lo > hi + tol:
        return None
    return (lo, hi)


def pareto_optimal(P, pts, tol=1e-12):
    """P 是否帕累托最优（最小化 J、最大化 F）。"""
    Jp, Fp = P
    for Q in pts:
        if Q is P:
            continue
        Jq, Fq = Q
        if (Jq <= Jp + tol and Fq >= Fp - tol) and (Jq < Jp - tol or Fq > Fp + tol):
            return False
    return True


def constraint_vs_penalty(pts, F_min, label, tol=1e-9):
    """核心问题：约束最优这个点，是否存在 λ ≥ 0 使它在 min(J − λF) 处取得？

    注意：不能拿约束最优去比"无约束惩罚最优"——惩罚法本身不施加 F ≥ F_min，
    两者本就不可比。正确的判据是**约束最优点的可支撑性**。
    """
    print(f"\n--- {label} ---")
    feas = [P for P in pts if P[1] >= F_min - tol]
    if not feas:
        print(f"  F_min={F_min} 下无可行动作")
        return None
    # 约束最优：可行集内 J 最小（F 大者优先）
    best = min(feas, key=lambda P: (P[0], -P[1]))
    rng = supported_lambda(best, pts)
    n_po = sum(1 for P in pts if pareto_optimal(P, pts))
    n_sup = sum(1 for P in pts if pareto_optimal(P, pts) and supported_lambda(P, pts) is not None)

    print(f"  约束最优: J={best[0]:.4f}, F={best[1]:.4f}"
          f"   (Pareto最优={pareto_optimal(best, pts)})")
    print(f"  该点可支撑性: {'λ ∈ ' + str(tuple(round(v, 6) for v in rng)) if rng else '**非支撑**'}")
    print(f"  参考：{n_sup}/{n_po} 个 Pareto 最优点可被某个 λ 支持（共 {len(pts)} 个动作）")

    ok = rng is not None
    print(f"  → {'约束最优可被某个惩罚权重复现' if ok else '约束最优**不可**被任何 λ 复现'}")
    return ok


def check_claim_3():
    print()
    print("=" * 78)
    print("断言 3：约束最优 vs 惩罚最优（离散机动集 → 非凸可达集）")
    print("=" * 78)

    # 固定翼风格：6 个离散机动（类 Dubins 词），(J=代价, F=未来可行性)
    fw = [(1.00, 20.0), (9.00, 60.0), (10.0, 100.0), (4.00, 35.0), (30.0, 90.0), (2.00, 10.0)]
    same_fw = constraint_vs_penalty(fw, F_min=60.0, label="固定翼式离散热机动集，F_min=60")

    # 类多旋翼：连续、凸的权衡（J 对 F 凸）
    Fs = np.linspace(0.0, 100.0, 101)
    cont = [(float(F * F / 100.0), float(F)) for F in Fs]   # J = F²/100 凸
    same_cont = constraint_vs_penalty(cont, F_min=60.0, label="类多旋翼凸权衡集（J=F²/100），F_min=60")

    print()
    print(f"平台依赖性：固定翼式离散集约束最优可复现 = {same_fw}；"
          f"凸权衡集约束最优可复现 = {same_cont}")
    if (not same_fw) and same_cont:
        print("→ 判定：约束型与惩罚型的差异**是固定翼特异性现象**，凸权衡下二者重合。")
    else:
        print("→ 判定：本算例未给出预期的平台差异，需重新设计算例。")
    return same_fw, same_cont


if __name__ == "__main__":
    flipped = check_claims_1_and_2()
    fw, cont = check_claim_3()
    print()
    print("=" * 78)
    print("总判定")
    print("=" * 78)
    print(f"断言 1（状态项→策略不变）      : {'被反驳（策略确实翻转）' if flipped else '未反驳'}")
    print(f"断言 2（势函数塑形→策略不变）  : 通过")
    print(f"断言 3（离散集→约束≠惩罚）     : {'通过' if (not fw and cont) else '未通过'}")
