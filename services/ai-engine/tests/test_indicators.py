import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.risk import position_size, rr, weighted_rr
from app.core.scoring import compute_score
from app.indicators import structure as st
from app.indicators.poi import fvgs, order_blocks, displacement_at
from app.indicators.technicals import adx, atr, ema, sma
from app.services.backtest import run_backtest
from app.services.market_data import load_csv_candles
from app.strategies.strategy_c_breakout_retest import breakout_setup
from app.strategies.strategy_d_mean_reversion import mean_reversion_setup


def c(o, h, l, cl, v=100.0, t=0):
    return {"t": t, "o": o, "h": h, "l": l, "c": cl, "v": v}


def trending(n=120, start=100.0, step=0.5):
    # Explicit zigzag pivots so swing highs/lows exist (strict inequality, n=2)
    out = []
    p = start
    for i in range(n):
        phase = i % 8
        delta = [2.0, 2.0, 1.0, -1.0, -2.0, -1.0, 0.5, 0.5][phase] + step
        o = p
        cl = p + delta
        wick = 1.5 if phase == 2 else (1.5 if phase == 4 else 0.4)
        out.append(c(o, max(o, cl) + wick, min(o, cl) - wick, cl, 100 + i, i))
        p = cl
    return out


def test_swings_and_bias():
    candles = trending()
    sh, sl = st.swings(candles)
    assert sh and sl
    assert st.bias(candles) in ("bullish", "bearish", "range")


def test_fvg_detection():
    candles = [c(10, 11, 9, 10), c(10, 12, 10, 12), c(13, 14, 12.5, 13.5)]
    gaps = fvgs(candles)
    assert gaps and gaps[0]["kind"] == "bullish"
    assert gaps[0]["low"] == 11 and gaps[0]["high"] == 12.5


def test_displacement_and_ob():
    candles = [c(100, 100.5, 99.5, 100.1) for _ in range(25)]
    candles.append(c(100, 100.6, 99.8, 100.5))          # last bullish candle
    candles.append(c(100.5, 101, 92, 93, 500))            # bearish displacement
    assert displacement_at(candles, len(candles) - 1)
    obs = order_blocks(candles)
    assert any(o["kind"] == "bearish" for o in obs)


def test_technicals():
    closes = [float(i) for i in range(1, 60)]
    assert sma(closes, 10) is not None
    assert ema(closes, 10) is not None
    candles = trending(80)
    assert atr(candles) is not None and atr(candles) > 0
    assert adx(candles) is not None


def test_scoring_thresholds():
    full = compute_score(bias_clear=True, poi_valid=True, swept=True, mss=True,
                         ltf_confirmed=True, liquidity_target=True, rr_ok=True)
    assert full["score"] == 10 and full["status"] == "READY" and full["grade"] == "A+"
    weak = compute_score(bias_clear=True, poi_valid=False, swept=False, mss=False,
                         ltf_confirmed=False, liquidity_target=False, rr_ok=False)
    assert weak["score"] == 2 and weak["status"] == "NO_SETUP"


def test_risk_position_size():
    out = position_size(balance=1000, risk_pct=1, entry=100, sl=95, targets=[110, 115])
    assert out["risk_amount"] == 10 and out["qty"] == 2
    assert out["targets"][0]["rr"] == 2.0
    assert rr(100, 95, 110) == 2.0
    assert weighted_rr(100, 95, 110, 115) == 2.5


def test_csv_loader_rejects_duplicates():
    text = "time,open,high,low,close\n1,10,11,9,10\n1,10,11,9,10\n"
    try:
        load_csv_candles(text)
        raise AssertionError("expected duplicate error")
    except ValueError:
        pass


def test_backtest_smoke_all_modes():
    candles = trending(320)
    for mode in "ABCD":
        result = run_backtest(candles, mode)
        assert result["mode"] == mode
        assert "profit_factor" in result and "net_r" in result


def test_strategy_c_d_guards():
    assert breakout_setup(trending(100)) is None  # needs 230 candles
    assert mean_reversion_setup(trending(40)) is None  # needs 60 candles
