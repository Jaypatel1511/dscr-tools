import pytest
import pandas as pd
from dscrtools.models.dscr import analyze, summary_table


def test_analyze_returns_list(standard_loan, sample_noi):
    results = analyze(standard_loan, sample_noi)
    assert len(results) == standard_loan.loan_term_years


def test_dscr_positive(standard_loan, sample_noi):
    results = analyze(standard_loan, sample_noi)
    for r in results:
        assert r.dscr > 0


def test_dscr_status_ok(standard_loan, sample_noi):
    results = analyze(standard_loan, sample_noi, min_dscr=1.0)
    for r in results:
        assert r.status in ("OK", "BREACH", "DEFAULT")


def test_covenant_breach_detected(standard_loan):
    from dscrtools.data.schema import NOISchedule
    tight_noi = NOISchedule(base_noi=400_000, growth_rate=0.0)
    results = analyze(standard_loan, tight_noi, min_dscr=1.25)
    breaches = [r for r in results if r.covenant_breach]
    assert len(breaches) > 0


def test_io_loan_higher_dscr(standard_loan, io_loan, sample_noi):
    std_results = analyze(standard_loan, sample_noi)
    io_results = analyze(io_loan, sample_noi)
    assert io_results[0].dscr > std_results[0].dscr


def test_summary_table_returns_df(standard_loan, sample_noi):
    results = analyze(standard_loan, sample_noi)
    df = summary_table(results)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == standard_loan.loan_term_years
