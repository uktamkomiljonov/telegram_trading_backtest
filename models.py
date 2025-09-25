from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Trade:
    id: Optional[int] = None
    token_address: str = ""
    token_symbol: str = ""
    entry_price: float = 0.0
    exit_price: Optional[float] = None
    entry_time: datetime = datetime.now()
    exit_time: Optional[datetime] = None
    position_size: float = 0.0
    status: str = "OPEN"  # OPEN, CLOSED_PROFIT, CLOSED_LOSS, CLOSED_MANUAL
    profit_loss: Optional[float] = None
    profit_loss_percent: Optional[float] = None
    telegram_message_id: Optional[int] = None
    telegram_message_text: str = ""


@dataclass
class TokenSignal:
    token_address: str
    token_symbol: str
    price: float
    timestamp: datetime
    message_text: str
    message_id: int


@dataclass
class PriceData:
    token_address: str
    price: float
    timestamp: datetime
    volume_24h: Optional[float] = None
    market_cap: Optional[float] = None


@dataclass
class BacktestResult:
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_profit_loss: float = 0.0
    total_profit_loss_percent: float = 0.0
    win_rate: float = 0.0
    average_win: float = 0.0
    average_loss: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: Optional[float] = None
    total_fees: float = 0.0
    net_profit: float = 0.0

    def calculate_metrics(self, trades):
        if not trades:
            return

        self.total_trades = len(trades)
        winning_trades = [t for t in trades if t.profit_loss and t.profit_loss > 0]
        losing_trades = [t for t in trades if t.profit_loss and t.profit_loss < 0]

        self.winning_trades = len(winning_trades)
        self.losing_trades = len(losing_trades)

        if self.total_trades > 0:
            self.win_rate = (self.winning_trades / self.total_trades) * 100

        self.total_profit_loss = sum(t.profit_loss for t in trades if t.profit_loss)

        if winning_trades:
            self.average_win = sum(t.profit_loss for t in winning_trades) / len(winning_trades)
        if losing_trades:
            self.average_loss = sum(t.profit_loss for t in losing_trades) / len(losing_trades)

        # Calculate max drawdown
        cumulative_pnl = []
        running_total = 0
        for trade in trades:
            if trade.profit_loss:
                running_total += trade.profit_loss
                cumulative_pnl.append(running_total)

        if cumulative_pnl:
            peak = cumulative_pnl[0]
            max_dd = 0
            for value in cumulative_pnl:
                if value > peak:
                    peak = value
                drawdown = peak - value
                if drawdown > max_dd:
                    max_dd = drawdown
            self.max_drawdown = max_dd