"""
Flask web application for viewing backtest statistics
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import logging
from datetime import datetime
from backtester import Backtester
from config import Config

logger = logging.getLogger(__name__)

def create_app(db_manager):
    app = Flask(__name__)
    CORS(app)

    # Create backtester instance
    config = Config()
    backtester = Backtester(config, db_manager)

    @app.route('/')
    def index():
        """Main dashboard page"""
        return render_template('index.html')

    @app.route('/api/statistics')
    def get_statistics():
        """Get trading statistics"""
        try:
            stats = backtester.calculate_statistics()
            return jsonify(stats)
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/trades')
    def get_trades():
        """Get trade list"""
        try:
            limit = request.args.get('limit', 50, type=int)
            trades = db_manager.get_recent_trades(limit)

            # Format dates for display
            for trade in trades:
                if trade.get('entry_time'):
                    trade['entry_time'] = str(trade['entry_time'])[:19]
                if trade.get('exit_time'):
                    trade['exit_time'] = str(trade['exit_time'])[:19]

                # Round numerical values
                for key in ['entry_price', 'exit_price', 'pnl', 'pnl_percentage']:
                    if trade.get(key) is not None:
                        trade[key] = round(float(trade[key]), 4)

            return jsonify(trades)
        except Exception as e:
            logger.error(f"Error getting trades: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/chart-data')
    def get_chart_data():
        """Get data for charts"""
        try:
            chart_data = backtester.get_performance_chart_data()
            return jsonify(chart_data)
        except Exception as e:
            logger.error(f"Error getting chart data: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/token-performance')
    def get_token_performance():
        """Get performance by token"""
        try:
            token_stats = backtester.get_token_performance()
            return jsonify(token_stats)
        except Exception as e:
            logger.error(f"Error getting token performance: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/system-status')
    def get_system_status():
        """Get system status"""
        try:
            open_trades = db_manager.get_open_trades()
            all_trades = db_manager.get_all_trades()

            status = {
                'is_running': True,
                'start_time': datetime.now().isoformat(),
                'open_trades_count': len(open_trades),
                'total_trades_count': len(all_trades),
                'channel_monitored': config.CHANNEL_USERNAME,
                'take_profit': config.TAKE_PROFIT_PERCENTAGE,
                'stop_loss': config.STOP_LOSS_PERCENTAGE,
                'risk_reward_ratio': config.RISK_REWARD_RATIO,
            }
            return jsonify(status)
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return jsonify({'error': str(e)}), 500

    return app