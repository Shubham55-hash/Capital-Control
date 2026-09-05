from dataclasses import dataclass, field

@dataclass
class Settings:
    # Demo value shown using Indian numbering: INR 10 lakh.
    capital: float = 1_000_000
    confidence: float = .99
    base_dcvar_limit: float = .05
    risk_multipliers: dict = field(default_factory=lambda: {"NORMAL": 1., "STRESS": .7, "CRISIS": .4})
    shrinkage: float = .25
    max_weight: float = .55
    max_turnover: float = .45
    tc_rate: float = .002
    sector_limit: float = .62
    liquidity_limit: float = .48
    normal_vol20_ratio: float = 1.5
    crisis_vol20_ratio: float = 2.0
    stress_drawdown: float = .08
    crisis_drawdown: float = .15
    emergency_cash_step: float = .10

settings = Settings()
