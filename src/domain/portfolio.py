from dataclasses import dataclass
from decimal import Decimal


@dataclass
class PortfolioSummary:
    shares_held: Decimal
    avg_cost_with: Decimal
    avg_cost_without: Decimal
    total_contribution: Decimal
    realized_gain_loss_with: Decimal
    realized_gain_loss_without: Decimal


@dataclass
class SaleSimulation:
    simulation_shares: Decimal
    gain_loss_with: Decimal
    gain_loss_without: Decimal
    tax_with: Decimal
    tax_without: Decimal
    net_proceeds_with: Decimal
    net_proceeds_without: Decimal
