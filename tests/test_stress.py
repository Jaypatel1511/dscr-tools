import pytest
import pandas as pd
from dscrtools.models.stress import rate_shock, noi_stress, break_even_noi


def test_rate_shock_returns_df(standard_loan, sample_noi):
    df = rate_shock(standard_loan, sample_noi, rate_shocks=[0.01, 0.02])
    assert isinstance(df, pd.DataFrame)
    assert "Base" in df.columns
    assert "+1bps" in df.columns


def test_rate_shock_lowers_dscr(standard_loan, sample_noi):
    df = rate_shock(standard_loan, sample_noi, rate_shocks=[0.02])
    assert df["+2bps"].mean() < df["Base"].mean()


def test_noi_stress_returns_df(standard_loan, sample_noi):
    df = noi_stress(standard_loan, sample_noi, noi_haircuts=[0.10, 0.20])
    assert isinstance(df, pd.DataFrame)
    assert "Base" in df.columns
    assert "-10% NOI" in df.columns


def test_noi_stress_lowers_dscr(standard_loan, sample_noi):
    df = noi_stress(standard_loan, sample_noi, noi_haircuts=[0.20])
    assert df["-20% NOI"].mean() < df["Base"].mean()


def test_break_even_noi_positive(standard_loan):
    be_noi = break_even_noi(standard_loan, min_dscr=1.0)
    assert be_noi > 0


def test_break_even_noi_scales_with_dscr(standard_loan):
    be_1x = break_even_noi(standard_loan, min_dscr=1.0)
    be_125x = break_even_noi(standard_loan, min_dscr=1.25)
    assert be_125x > be_1x
