from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP

from domain.portfolio import SaleSimulation

_SHARES_Q = Decimal("0.0001")
_AVG_COST_Q = Decimal("0.01")
_MONEY_Q = Decimal("1")


def _trunc_shares(v: Decimal) -> Decimal:
    return v.quantize(_SHARES_Q, rounding=ROUND_DOWN)


def _round_avg_cost(v: Decimal) -> Decimal:
    return v.quantize(_AVG_COST_Q, rounding=ROUND_HALF_UP)


def _trunc_money(v: Decimal) -> Decimal:
    return v.quantize(_MONEY_Q, rounding=ROUND_DOWN)


def calc_contribution(
    prev_shares: Decimal,
    prev_avg_with: Decimal,
    prev_avg_without: Decimal,
    new_shares: Decimal,
    contribution: Decimal,
    incentive: Decimal,
) -> tuple[Decimal, Decimal, Decimal]:
    """CONTRIBUTION: 取得後の (shares_held_after, avg_cost_with, avg_cost_without) を返す"""
    unit_with = (contribution + incentive) / new_shares
    unit_without = contribution / new_shares
    total = prev_shares + new_shares
    new_avg_with = (prev_shares * prev_avg_with + new_shares * unit_with) / total
    new_avg_without = (prev_shares * prev_avg_without + new_shares * unit_without) / total
    return (
        _trunc_shares(total),
        _round_avg_cost(new_avg_with),
        _round_avg_cost(new_avg_without),
    )


def calc_dividend_reinvestment(
    prev_shares: Decimal,
    prev_avg_with: Decimal,
    prev_avg_without: Decimal,
    new_shares: Decimal,
    dividend_amount: Decimal,
) -> tuple[Decimal, Decimal, Decimal]:
    """DIVIDEND_REINVESTMENT: 取得後の (shares_held_after, avg_cost_with, avg_cost_without) を返す"""
    unit_with = dividend_amount / new_shares
    total = prev_shares + new_shares
    new_avg_with = (prev_shares * prev_avg_with + new_shares * unit_with) / total
    # avg_cost_without: 取得コスト 0 のため保有株数増加分だけ希釈される
    new_avg_without = (prev_shares * prev_avg_without) / total
    return (
        _trunc_shares(total),
        _round_avg_cost(new_avg_with),
        _round_avg_cost(new_avg_without),
    )


def calc_sale(
    prev_shares: Decimal,
    avg_with: Decimal,
    avg_without: Decimal,
    sale_shares: Decimal,
    sale_price: Decimal,
) -> tuple[Decimal, Decimal, Decimal, Decimal, Decimal]:
    """SALE: (shares_held_after, avg_cost_with, avg_cost_without, gain_loss_with, gain_loss_without) を返す"""
    gain_with = _trunc_money((sale_price - avg_with) * sale_shares)
    gain_without = _trunc_money((sale_price - avg_without) * sale_shares)
    shares_after = prev_shares - sale_shares
    if shares_after <= Decimal("0"):
        return Decimal("0"), Decimal("0"), Decimal("0"), gain_with, gain_without
    return (
        _trunc_shares(shares_after),
        avg_with,
        avg_without,
        gain_with,
        gain_without,
    )


def calc_split(
    prev_shares: Decimal,
    prev_avg_with: Decimal,
    prev_avg_without: Decimal,
    ratio_before: int,
    ratio_after: int,
) -> tuple[Decimal, Decimal, Decimal]:
    """STOCK_SPLIT / REVERSE_SPLIT: (shares_held_after, avg_cost_with, avg_cost_without) を返す"""
    r_after = Decimal(ratio_after)
    r_before = Decimal(ratio_before)
    return (
        _trunc_shares(prev_shares * r_after / r_before),
        _round_avg_cost(prev_avg_with * r_before / r_after),
        _round_avg_cost(prev_avg_without * r_before / r_after),
    )


def calc_tax(gain_loss: Decimal, tax_rate: Decimal) -> Decimal:
    """概算税額 = MAX(損益, 0) × 税率（円未満切り捨て）"""
    return _trunc_money(max(gain_loss, Decimal("0")) * tax_rate)


def simulate_sale(
    current_price: Decimal,
    simulation_shares: Decimal,
    avg_cost_with: Decimal,
    avg_cost_without: Decimal,
    tax_rate: Decimal,
) -> SaleSimulation:
    """売却シミュレーション計算"""
    gain_with = (current_price - avg_cost_with) * simulation_shares
    gain_without = (current_price - avg_cost_without) * simulation_shares
    tax_with = calc_tax(gain_with, tax_rate)
    tax_without = calc_tax(gain_without, tax_rate)
    return SaleSimulation(
        simulation_shares=simulation_shares,
        gain_loss_with=_trunc_money(gain_with),
        gain_loss_without=_trunc_money(gain_without),
        tax_with=tax_with,
        tax_without=tax_without,
        net_proceeds_with=_trunc_money(current_price * simulation_shares - tax_with),
        net_proceeds_without=_trunc_money(current_price * simulation_shares - tax_without),
    )
