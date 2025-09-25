"""
Backtesting engine for analyzing trading performance
"""

import logging
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class Backtester:
    def __init__(self, config, db_manager):
        self.config = config
        self.db = db_manager
        self.initial_capital = config.INITIAL_CAPITAL

    def calculate_statistics(self):
        """Calculate comprehensive backtest statistics"""
        try:
            trades = self.db.get_all_trades()

            if not trades:
                return self.get_empty_statistics()

            df = pd.DataFrame(trades)

            # Basic statistics
            total_trades = len(df)
            winning_trades = len(df[df['pnl'] > 0])
            losing_trades = len(df[df['pnl'] < 0])
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

            # PnL statistics
            total_pnl = df['pnl'].sum()
            avg_win = df[df['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
            avg_loss = abs(df[df['pnl'] < 0]['pnl'].mean()) if losing_trades > 0 else 0

            # Calculate profit factor
            gross_profit = df[df['pnl'] > 0]['pnl'].sum() if winning_trades > 0 else 0
            gross_loss = abs(df[df['pnl'] < 0]['pnl'].sum()) if losing_trades > 0 else 0
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

            # Calculate maximum drawdown
            cumulative_pnl = df['pnl'].cumsum()
            running_max = cumulative_pnl.cummax()
            drawdown = cumulative_pnl - running_max
            max_drawdown = drawdown.min()
            max_drawdown_pct = (max_drawdown / self.initial_capital * 100) if self.initial_capital > 0 else 0

            # Calculate Sharpe ratio (simplified)
            returns = df['pnl_percentage'] / 100
            sharpe_ratio = (returns.mean() / returns.std() * np.sqrt(252)) if returns.std() > 0 else 0

            # Calculate expected value
            expected_value = (win_rate / 100 * avg_win) - ((1 - win_rate / 100) * avg_loss)

            # Time-based statistics
            if 'entry_time' in df.columns:
                df['entry_time'] = pd.to_datetime(df['entry_time'])
                first_trade = df['entry_time'].min()
                last_trade = df['entry_time'].max()
                trading_days = (last_trade - first_trade).days + 1
                trades_per_day = total_trades / trading_days if trading_days > 0 else 0
            else:
                trading_days = 0
                trades_per_day = 0

            # ROI calculation
            ending_capital = self.initial_capital + total_pnl
            roi = ((ending_capital - self.initial_capital) / self.initial_capital * 100) if self.initial_capital > 0 else 0

            statistics = {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': round(win_rate, 2),
                'total_pnl': round(total_pnl, 2),
                'avg_win': round(avg_win, 2),
                'avg_loss': round(avg_loss, 2),
                'profit_factor': round(profit_factor, 2),
                'max_drawdown': round(max_drawdown, 2),
                'max_drawdown_pct': round(max_drawdown_pct, 2),
                'sharpe_ratio': round(sharpe_ratio, 2),
                'expected_value': round(expected_value, 2),
                'roi': round(roi, 2),
                'initial_capital': self.initial_capital,
                'ending_capital': round(ending_capital, 2),
                'trading_days': trading_days,
                'trades_per_day': round(trades_per_day, 2),
                'gross_profit': round(gross_profit, 2),
                'gross_loss': round(gross_loss, 2),
            }

            return statistics

        except Exception as e:
            logger.error(f"Error calculating statistics: {e}")
            return self.get_empty_statistics()

    def get_empty_statistics(self):
        """Return empty statistics structure"""
        return {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0,
            'total_pnl': 0,
            'avg_win': 0,
            'avg_loss': 0,
            'profit_factor': 0,
            'max_drawdown': 0,
            'max_drawdown_pct': 0,
            'sharpe_ratio': 0,
            'expected_value': 0,
            'roi': 0,
            'initial_capital': self.initial_capital,
            'ending_capital': self.initial_capital,
            'trading_days': 0,
            'trades_per_day': 0,
            'gross_profit': 0,
            'gross_loss': 0,
        }

    def get_performance_chart_data(self):
        """Get data for performance chart"""
        try:
            trades = self.db.get_all_trades()

            if not trades:
                return {'labels': [], 'cumulative_pnl': [], 'trade_pnl': []}

            df = pd.DataFrame(trades)
            df = df.sort_values('entry_time')

            cumulative_pnl = df['pnl'].cumsum().tolist()
            trade_pnl = df['pnl'].tolist()

            # Format timestamps for chart
            labels = []
            for idx, row in df.iterrows():
                if pd.notna(row.get('entry_time')):
                    labels.append(str(row['entry_time'])[:19])
                else:
                    labels.append(f"Trade {idx + 1}")

            return {
                'labels': labels,
                'cumulative_pnl': cumulative_pnl,
                'trade_pnl': trade_pnl,
            }

        except Exception as e:
            logger.error(f"Error getting chart data: {e}")
            return {'labels': [], 'cumulative_pnl': [], 'trade_pnl': []}

    def get_token_performance(self):
        """Get performance by token"""
        try:
            trades = self.db.get_all_trades()

            if not trades:
                return []

            df = pd.DataFrame(trades)

            # Group by token symbol
            token_stats = df.groupby('token_symbol').agg({
                'pnl': ['sum', 'mean', 'count'],
                'pnl_percentage': 'mean'
            }).round(2)

            token_stats.columns = ['total_pnl', 'avg_pnl', 'trade_count', 'avg_pnl_pct']
            token_stats = token_stats.reset_index()

            # Calculate win rate per token
            win_rates = []
            for token in token_stats['token_symbol']:
                token_trades = df[df['token_symbol'] == token]
                wins = len(token_trades[token_trades['pnl'] > 0])
                total = len(token_trades)
                win_rate = (wins / total * 100) if total > 0 else 0
                win_rates.append(round(win_rate, 2))

            token_stats['win_rate'] = win_rates

            return token_stats.to_dict('records')

        except Exception as e:
            logger.error(f"Error getting token performance: {e}")
            return []