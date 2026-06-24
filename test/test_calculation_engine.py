"""design_logic.md section 7 の数値例による CalculationEngine の検証"""
from decimal import Decimal
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from service.calculation_engine import (
    calc_contribution,
    calc_dividend_reinvestment,
    calc_sale,
    calc_split,
    calc_tax,
    simulate_sale,
)

D = Decimal


# ── 数値例 ─────────────────────────────────────────────────────────────

def test_contribution_1_from_zero():
    """#1: 0 株から CONTRIBUTION 拠出 10000 奨励 500 取得 10 株"""
    shares, avg_with, avg_without = calc_contribution(
        D("0"), D("0"), D("0"),
        D("10"), D("10000"), D("500"),
    )
    assert shares == D("10.0000")
    assert avg_with == D("1050.00")
    assert avg_without == D("1000.00")


def test_contribution_2():
    """#2: CONTRIBUTION 拠出 10000 奨励 500 取得 9 株"""
    shares, avg_with, avg_without = calc_contribution(
        D("10"), D("1050.00"), D("1000.00"),
        D("9"), D("10000"), D("500"),
    )
    assert shares == D("19.0000")
    assert avg_with == D("1105.26")
    assert avg_without == D("1052.63")


def test_dividend_reinvestment_3():
    """#3: DIVIDEND_REINVESTMENT 配当 950 円 再投資 1 株"""
    shares, avg_with, avg_without = calc_dividend_reinvestment(
        D("19"), D("1105.26"), D("1052.63"),
        D("1"), D("950"),
    )
    assert shares == D("20.0000")
    assert avg_with == D("1097.50")
    assert avg_without == D("1000.00")


def test_sale_4():
    """#4: SALE 5 株を 1300 円で売却"""
    shares, avg_with, avg_without, gain_with, gain_without = calc_sale(
        D("20"), D("1097.50"), D("1000.00"),
        D("5"), D("1300"),
    )
    assert shares == D("15.0000")
    assert avg_with == D("1097.50")    # avg_cost は変化しない
    assert avg_without == D("1000.00")
    assert gain_with == D("1012")      # 1012.50 → 円未満切り捨て
    assert gain_without == D("1500")


def test_stock_split_5():
    """#5: STOCK_SPLIT 2:1"""
    shares, avg_with, avg_without = calc_split(
        D("15"), D("1097.50"), D("1000.00"), 1, 2,
    )
    assert shares == D("30.0000")
    assert avg_with == D("548.75")
    assert avg_without == D("500.00")


# ── SALE で保有株数が 0 になる場合 ─────────────────────────────────────

def test_sale_to_zero():
    shares, avg_with, avg_without, gain_with, gain_without = calc_sale(
        D("5"), D("1000.00"), D("900.00"),
        D("5"), D("1200"),
    )
    assert shares == D("0")
    assert avg_with == D("0")
    assert avg_without == D("0")
    assert gain_with == D("1000")   # (1200-1000)*5
    assert gain_without == D("1500")  # (1200-900)*5


# ── 税額計算 ──────────────────────────────────────────────────────────

def test_calc_tax_positive_gain():
    tax = calc_tax(D("1012"), D("0.20315"))
    assert tax == D("205")  # 1012 * 0.20315 = 205.5878 → 205


def test_calc_tax_negative_gain():
    tax = calc_tax(D("-500"), D("0.20315"))
    assert tax == D("0")


# ── REVERSE_SPLIT ──────────────────────────────────────────────────────

def test_reverse_split():
    """株式合併 2:1 (2 株を 1 株に)"""
    shares, avg_with, avg_without = calc_split(
        D("30"), D("500.00"), D("400.00"), 2, 1,
    )
    assert shares == D("15.0000")
    assert avg_with == D("1000.00")
    assert avg_without == D("800.00")


# ── 売却シミュレーション ─────────────────────────────────────────────

def test_simulate_sale_profit():
    result = simulate_sale(
        current_price=D("1300"),
        simulation_shares=D("15"),
        avg_cost_with=D("548.75"),
        avg_cost_without=D("500.00"),
        tax_rate=D("0.20315"),
    )
    assert result.gain_loss_with == D("11268")    # (1300-548.75)*15 = 11268.75 → 11268
    assert result.gain_loss_without == D("12000")  # (1300-500)*15
    assert result.tax_with == D("2289")   # 11268.75 * 0.20315 = 2289.24... → 2289
    assert result.tax_without == D("2437")  # 12000 * 0.20315 = 2437.8 → 2437
    assert result.net_proceeds_with == D("17211")    # 1300*15 - 2289 = 19500 - 2289
    assert result.net_proceeds_without == D("17063")  # 19500 - 2437
