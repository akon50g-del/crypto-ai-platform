"""Phase 5: economic-calendar blackout wiring (worker writes, engine reads)."""
from datetime import datetime, timedelta, timezone

from app.core.filters import check_filters
from app.models.db import EconomicEvent, get_session, init_db
from app.services import repository as repo


def _base_kwargs(**over):
    kw = dict(side="long", strategy="A", final_rr=2.5, min_final_rr=2.0,
              htf_bias="bullish", btc_bias="bullish", btc_context_enabled=True,
              atr_anomaly=False, has_active_signal=False)
    kw.update(over)
    return kw


def test_blackout_blocks_within_30min():
    now = datetime.now(timezone.utc)
    ev = [{"scheduled_at": now + timedelta(minutes=10), "impact": "HIGH", "title": "CPI"}]
    res = check_filters(**_base_kwargs(news_events=ev, now=now))
    assert not res["passed"]
    assert any("blackout" in f for f in res["failures"])


def test_blackout_ignores_medium_and_far_events():
    now = datetime.now(timezone.utc)
    ev = [{"scheduled_at": now + timedelta(minutes=5), "impact": "MEDIUM", "title": "x"},
          {"scheduled_at": now + timedelta(hours=2), "impact": "HIGH", "title": "CPI"}]
    assert check_filters(**_base_kwargs(news_events=ev, now=now))["passed"]


def test_load_news_events_from_db():
    init_db()
    now = datetime.now(timezone.utc)
    with get_session() as session:
        session.add(EconomicEvent(title="US CPI", impact="HIGH",
                                  scheduledAt=now + timedelta(minutes=15)))
        session.add(EconomicEvent(title="Far Event", impact="HIGH",
                                  scheduledAt=now + timedelta(days=3)))
        session.commit()
        events = repo.load_news_events(session, now=now)
    titles = [e["title"] for e in events]
    assert "US CPI" in titles and "Far Event" not in titles
