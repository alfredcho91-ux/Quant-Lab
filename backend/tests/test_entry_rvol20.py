from __future__ import annotations

import pandas as pd

from backend.modules.deepcoin.snapshot import _entry_rvol20


def test_entry_rvol20_excludes_the_reference_candle_from_its_baseline():
    completed = pd.DataFrame({"volume": [100.0] * 20 + [180.0]})

    assert _entry_rvol20(completed) == 1.8


def test_entry_rvol20_requires_all_twenty_prior_completed_volumes():
    assert _entry_rvol20(pd.DataFrame({"volume": [100.0] * 20})) is None
    assert _entry_rvol20(pd.DataFrame({"volume": [100.0] * 19 + [None, 180.0]})) is None


def test_entry_rvol20_returns_unavailable_for_a_zero_volume_baseline():
    assert _entry_rvol20(pd.DataFrame({"volume": [0.0] * 20 + [180.0]})) is None
