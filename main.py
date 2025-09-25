#!/usr/bin/env python3
"""
Main application entry point for Telegram trading backtester
"""

import asyncio
import logging
import sys
from datetime import datetime
import signal
import threading
from pathlib import Path

from telegram_monitor import TelegramMonitor
from backtester import Backtester
from database import DatabaseManager
from web_app import create_app
from config import Config

# Setup logging
Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/trading.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class TradingBacktestSystem:
    def __init__(self):
        self.config = Config()
        self.db = DatabaseManager()
        self.monitor = TelegramMonitor(self.config, self.db)
        self.backtester = Backtester(self.config, self.db)
        self.running = True

    async def start(self):
        """Start the backtesting system"""
        logger.info("Starting Trading Backtest System...")
        logger.info(f"Monitoring channel: {self.config.CHANNEL_USERNAME}")
        logger.info(f"Take Profit: {self.config.TAKE_PROFIT_PERCENTAGE}%")
        logger.info(f"Risk/Reward: {self.config.RISK_REWARD_RATIO}")

        # Initialize database
        self.db.initialize()

        # Start web server in separate thread
        web_thread = threading.Thread(target=self.run_web_server, daemon=True)
        web_thread.start()
        logger.info(f"Web interface started at http://localhost:{self.config.WEB_PORT}")

        # Start monitoring
        try:
            await self.monitor.start_monitoring()
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
        finally:
            await self.shutdown()

    def run_web_server(self):
        """Run Flask web server"""
        app = create_app(self.db)
        app.run(host='0.0.0.0', port=self.config.WEB_PORT, debug=False)

    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down...")
        self.running = False
        await self.monitor.stop()
        self.db.close()
        logger.info("Shutdown complete")


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}")
    sys.exit(0)


def main():
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Create and start system
    system = TradingBacktestSystem()

    # Run async event loop
    try:
        asyncio.run(system.start())
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()