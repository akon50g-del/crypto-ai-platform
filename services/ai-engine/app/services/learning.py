"""Learning loop: aggregate outcomes per strategy/symbol/regime and (when
enough data exists) suggest Score-weight adjustments with Scikit-learn.

Hard guardrails from STRATEGY_SPEC §11-12: suggestions are NEVER auto-applied.
They require >=100 closed trades, PF >= 1.20, positive expectancy, and an
out-of-sample pass. Rules stay in charge; ML only tunes weights within bounds.
"""
from __future__ import annotations


def aggregate(outcomes: list[dict]) -> dict:
    """outcomes: [{strategy, symbol, regime, side, r, result, score_breakdown}]"""
    def stats(rows: list[dict]) -> dict:
        if not rows:
            return {"trades": 0}
        wins = [r for r in rows if r["r"] > 0]
        losses = [r for r in rows if r["r"] < 0]
        gw = sum(r["r"] for r in wins)
        gl = -sum(r["r"] for r in losses)
        net = round(sum(r["r"] for r in rows), 3)
        equity = peak = dd = 0.0
        for r in rows:
            equity += r["r"]
            peak = max(peak, equity)
            dd = max(dd, peak - equity)
        return {
            "trades": len(rows), "wins": len(wins), "losses": len(losses),
            "win_rate_pct": round(100 * len(wins) / len(rows), 2),
            "profit_factor": round(gw / gl, 3) if gl else None,
            "expectancy_r": round(net / len(rows), 4), "net_r": net,
            "max_drawdown_r": round(dd, 3),
        }

    by_strategy: dict[str, list] = {}
    by_symbol: dict[str, list] = {}
    by_regime: dict[str, list] = {}
    for o in outcomes:
        by_strategy.setdefault(o["strategy"], []).append(o)
        by_symbol.setdefault(o["symbol"], []).append(o)
        by_regime.setdefault(o["regime"], []).append(o)
    return {
        "overall": stats(outcomes),
        "by_strategy": {k: stats(v) for k, v in sorted(by_strategy.items())},
        "by_symbol": {k: stats(v) for k, v in sorted(by_symbol.items())},
        "by_regime": {k: stats(v) for k, v in sorted(by_regime.items())},
    }


def suggest_weights(outcomes: list[dict], min_trades: int = 100) -> dict:
    """Logistic-regression feature importances over score components.
    Returns a *suggestion* only; config is never mutated automatically."""
    if len(outcomes) < min_trades:
        return {"status": "insufficient_data", "closed_trades": len(outcomes),
                "required": min_trades,
                "note": "weight tuning stays locked until acceptance sample size"}
    try:
        from sklearn.linear_model import LogisticRegression
    except ImportError:
        return {"status": "sklearn_unavailable",
                "note": "pip install scikit-learn to enable weight suggestions"}
    features = ["bias", "poi", "sweep", "mss", "ltfConfirmation", "liquidityTarget", "rr"]
    X, y = [], []
    for o in outcomes:
        bd = o.get("score_breakdown") or {}
        X.append([1.0 if bd.get(f) else 0.0 for f in features])
        y.append(1 if o["r"] > 0 else 0)
    if len(set(y)) < 2:
        return {"status": "single_class", "note": "need both wins and losses"}
    model = LogisticRegression(max_iter=500)
    model.fit(X, y)
    coefs = {f: round(float(c), 3) for f, c in zip(features, model.coef_[0])}
    agg = aggregate(outcomes)["overall"]
    return {
        "status": "suggestion_only", "coefficients": coefs,
        "train_accuracy": round(float(model.score(X, y)), 3),
        "current_stats": agg,
        "note": "review + OOS backtest required before any config change; never auto-applied",
    }
