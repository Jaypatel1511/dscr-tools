from dataclasses import dataclass, field
from typing import Optional


# Supported interest calculation methods
INTEREST_METHODS = {
    "fixed_30_360":   "Fixed rate, 30/360 day count convention",
    "fixed_actual_360": "Fixed rate, Actual/360 day count convention",
    "fixed_actual_365": "Fixed rate, Actual/365 day count convention",
    "interest_only":  "Full interest-only, no principal payments",
    "partial_io":     "Interest-only period followed by full amortization",
    "arm":            "Adjustable rate mortgage with floor and cap",
}

# Minimum DSCR thresholds by lender type
DSCR_BENCHMARKS = {
    "conventional_commercial": 1.25,
    "agency_multifamily":      1.20,
    "small_balance_commercial": 1.20,
    "private_credit":          1.15,
    "bridge":                  1.10,
}


@dataclass
class LoanParams:
    """
    Core input contract for a loan — used across all dscrtools modules.
    All dollar amounts in whole dollars. Rates as decimals (0.065 = 6.5%).
    """
    loan_amount: float              # e.g. 8_000_000
    interest_rate: float            # annual rate e.g. 0.065
    amortization_years: int         # amortization term e.g. 30
    loan_term_years: int            # actual loan term e.g. 10
    interest_method: str            # see INTEREST_METHODS above
    io_periods: int = 0             # interest-only periods in months
    payments_per_year: int = 12     # 12=monthly, 4=quarterly, 1=annual
    rate_floor: float = 0.0         # ARM floor rate
    rate_cap: float = 1.0           # ARM cap rate
    origination_fee_pct: float = 0.0  # upfront fee as % of loan
    prepayment_penalty_pct: float = 0.0  # prepayment penalty %
    property_name: Optional[str] = None
    lender_name: Optional[str] = None

    def __post_init__(self):
        if self.loan_amount <= 0:
            raise ValueError("loan_amount must be positive")
        if not (0 < self.interest_rate < 1):
            raise ValueError("interest_rate must be between 0 and 1 (e.g. 0.065)")
        if self.amortization_years <= 0:
            raise ValueError("amortization_years must be positive")
        if self.loan_term_years <= 0:
            raise ValueError("loan_term_years must be positive")
        if self.loan_term_years > self.amortization_years:
            raise ValueError("loan_term_years cannot exceed amortization_years")
        if self.interest_method not in INTEREST_METHODS:
            raise ValueError(
                f"interest_method must be one of: {list(INTEREST_METHODS.keys())}"
            )
        if self.payments_per_year not in (1, 4, 12):
            raise ValueError("payments_per_year must be 1, 4, or 12")
        if self.io_periods < 0:
            raise ValueError("io_periods must be >= 0")
        if self.io_periods > self.loan_term_years * self.payments_per_year:
            raise ValueError("io_periods cannot exceed total loan periods")

    @property
    def total_periods(self) -> int:
        """Total number of payment periods over loan term."""
        return self.loan_term_years * self.payments_per_year

    @property
    def amortization_periods(self) -> int:
        """Total amortization periods."""
        return self.amortization_years * self.payments_per_year

    @property
    def periodic_rate(self) -> float:
        """Interest rate per payment period."""
        return self.interest_rate / self.payments_per_year

    @property
    def loan_amount_mm(self) -> float:
        return self.loan_amount / 1_000_000

    @property
    def origination_fee(self) -> float:
        return self.loan_amount * self.origination_fee_pct

    def __repr__(self):
        return (
            f"LoanParams(amount=${self.loan_amount_mm:.2f}MM, "
            f"rate={self.interest_rate*100:.2f}%, "
            f"method='{self.interest_method}', "
            f"term={self.loan_term_years}yr/{self.amortization_years}yr amort, "
            f"io_periods={self.io_periods})"
        )


@dataclass
class NOISchedule:
    """
    Net Operating Income schedule for DSCR analysis.
    Can be defined as explicit period values or grown from a base NOI.
    """
    base_noi: float                  # starting annual NOI
    growth_rate: float = 0.03        # annual NOI growth rate
    explicit_noi: Optional[list] = None  # override with explicit annual NOIs
    vacancy_rate: float = 0.05       # vacancy/credit loss assumption
    capex_reserve: float = 0.0       # annual capex reserve deduction

    def __post_init__(self):
        if self.base_noi <= 0:
            raise ValueError("base_noi must be positive")
        if not (0 <= self.vacancy_rate < 1):
            raise ValueError("vacancy_rate must be between 0 and 1")

    def get_noi(self, year: int) -> float:
        """
        Return NOI for a given year (1-indexed).
        Uses explicit schedule if provided, otherwise grows from base.
        """
        if self.explicit_noi and year <= len(self.explicit_noi):
            return self.explicit_noi[year - 1]
        return self.base_noi * ((1 + self.growth_rate) ** (year - 1))

    def get_effective_noi(self, year: int) -> float:
        """NOI after vacancy and capex reserve deductions."""
        raw = self.get_noi(year)
        return raw * (1 - self.vacancy_rate) - self.capex_reserve
