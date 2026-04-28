# dscr-tools 📊

**Python toolkit for loan amortization, DSCR tracking, covenant monitoring, and loan sizing.**

Supports multiple interest calculation methods, interest-only periods, ARM loans,
max loan sizing, and stress testing — replacing bespoke Excel models with
auditable, version-controlled Python code.

---

## Why dscr-tools?

Every commercial real estate and private credit analyst builds the same loan model
from scratch in Excel. dscr-tools standardizes the engine so you can focus on
the deal, not the spreadsheet.

---

## Installation

    pip install dscr-tools

---

## Quickstart

    from dscrtools import LoanParams, NOISchedule
    from dscrtools.models import amortization, dscr, sizing, stress

    loan = LoanParams(
        loan_amount=8_000_000,
        interest_rate=0.065,
        amortization_years=30,
        loan_term_years=10,
        interest_method="partial_io",
        io_periods=24,
        payments_per_year=12,
        property_name="Midtown Office Building",
    )

    noi = NOISchedule(
        base_noi=750_000,
        growth_rate=0.03,
        vacancy_rate=0.05,
        capex_reserve=10_000,
    )

    amortization.summary(loan)
    dscr.summary_table(dscr.analyze(loan, noi, min_dscr=1.25))
    sizing.size_loan(loan, noi=750_000, property_value=12_000_000)
    stress.rate_shock(loan, noi, rate_shocks=[0.01, 0.02, 0.03])
    stress.noi_stress(loan, noi, noi_haircuts=[0.10, 0.20, 0.30])

---

## Interest Methods

- fixed_30_360   - Fixed rate, 30/360 day count (most CRE loans)
- fixed_actual_360 - Fixed rate, Actual/360 (agency multifamily)
- fixed_actual_365 - Fixed rate, Actual/365 (some bank loans)
- interest_only  - Full interest-only, no principal payments
- partial_io     - Interest-only period followed by full amortization
- arm            - Adjustable rate with floor and cap

---

## Modules

- amortization - Full period-by-period schedule with I/O and ARM support
- dscr         - Annual DSCR calculation, covenant tracking, breach detection
- sizing       - Max loan sizing via DSCR, LTV, and Debt Yield tests
- stress       - Rate shock and NOI stress sensitivity tables
- loan         - Interest calculation primitives for all day-count conventions

---

## DSCR Covenant Logic

- DSCR above min_dscr  - OK
- DSCR below min_dscr  - BREACH
- DSCR below 1.0       - DEFAULT

---

## Loan Sizing

Solves for the maximum loan amount that satisfies all three constraints
simultaneously, identifying the binding constraint:

    sizing.size_loan(loan, noi=750_000, property_value=12_000_000,
                     min_dscr=1.25, max_ltv=0.75, min_debt_yield=0.08)

---

## Running Tests

    PYTHONPATH=. pytest tests/ -v

32 tests across all modules.

---

## Who This Is For

- CRE analysts underwriting commercial mortgage loans
- Private credit teams modeling leveraged deals
- Real estate finance practitioners replacing Excel waterfalls
- Anyone who needs reproducible, auditable loan math in Python

---

## License

MIT 2026 Jaypatel1511
