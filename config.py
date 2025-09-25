"""
Configuration settings for the trading backtest system
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Telegram settings
    API_ID = int(os.getenv('TELEGRAM_API_ID', ''))  # Get from my.telegram.org
    API_HASH = os.getenv('TELEGRAM_API_HASH', '')  # Get from my.telegram.org
    PHONE_NUMBER = os.getenv('TELEGRAM_PHONE', '')  # Your phone number
    SESSION_NAME = 'trading_backtest_session'
    CHANNEL_USERNAME = 't.me/trendingssol'

    # Trading parameters
    TAKE_PROFIT_PERCENTAGE = 10.0  # Take profit at 10%
    STOP_LOSS_PERCENTAGE = 6.67  # Stop loss for 1.5:1 risk/reward ratio
    RISK_REWARD_RATIO = 1.5
    INITIAL_CAPITAL = 10000.0  # Starting capital for backtest
    POSITION_SIZE = 100.0  # Amount to invest per trade

    # Database settings
    DATABASE_PATH = 'data/trades.db'

    # Web interface settings
    WEB_PORT = 5000

    # Monitoring settings
    CHECK_INTERVAL = 5  # Check for new messages every 5 seconds
    MAX_RETRIES = 3
    RETRY_DELAY = 10  # Seconds between retries

    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'logs/trading.log'

    # Pattern matching for token detection
    TOKEN_PATTERNS = [
        r'([A-Z]{3,10})',  # Token symbols like SOL, BONK
        r'CA:\s*([A-Za-z0-9]{32,44})',  # Contract addresses
        r'Contract:\s*([A-Za-z0-9]{32,44})',
        r'Token:\s*([A-Z]{3,10})',
        r'\$([A-Z]{3,10})',  # $SYMBOL format
    ]

    # Price patterns
    PRICE_PATTERNS = [
        r'Price:\s*\$?([\d.]+)',
        r'Entry:\s*\$?([\d.]+)',
        r'\$?([\d.]+)\s*USD',
        r'Buy at:\s*\$?([\d.]+)',
    ]