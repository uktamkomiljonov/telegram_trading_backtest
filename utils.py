import requests
import time
import logging
import re
from datetime import datetime
from typing import Optional, Dict
from models import PriceData
import config


class PriceProvider:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.last_request_time = {}
        self.rate_limit_delay = 1  # Seconds between requests

    def get_token_price(self, token_address: str, retries: int = 3) -> Optional[float]:
        """Get current price for a token address"""
        for attempt in range(retries):
            try:
                # Try DexScreener first (better for new tokens)
                price = self._get_price_dexscreener(token_address)
                if price:
                    return price

                # Fallback to other sources if needed
                self.logger.warning(f"Could not get price for {token_address}, attempt {attempt + 1}")
                time.sleep(2 ** attempt)  # Exponential backoff

            except Exception as e:
                self.logger.error(f"Error getting price for {token_address}: {e}")

        return None

    def _get_price_dexscreener(self, token_address: str) -> Optional[float]:
        """Get price from DexScreener API"""
        try:
            # Rate limiting
            current_time = time.time()
            if token_address in self.last_request_time:
                time_diff = current_time - self.last_request_time[token_address]
                if time_diff < self.rate_limit_delay:
                    time.sleep(self.rate_limit_delay - time_diff)

            url = f"{config.DEXSCREENER_API_URL}/tokens/{token_address}"
            response = requests.get(url, timeout=10)

            self.last_request_time[token_address] = time.time()

            if response.status_code == 200:
                data = response.json()
                if 'pairs' in data and data['pairs']:
                    # Get the pair with highest liquidity
                    pairs = data['pairs']
                    best_pair = max(pairs, key=lambda x: float(x.get('liquidity', {}).get('usd', 0)))
                    return float(best_pair['priceUsd'])

        except Exception as e:
            self.logger.error(f"DexScreener API error: {e}")

        return None


class TradeCalculator:
    @staticmethod
    def calculate_profit_loss(entry_price: float, exit_price: float, position_size: float) -> tuple:
        """Calculate profit/loss in USD and percentage"""
        shares = position_size / entry_price
        exit_value = shares * exit_price
        profit_loss_usd = exit_value - position_size
        profit_loss_percent = ((exit_price - entry_price) / entry_price) * 100

        return profit_loss_usd, profit_loss_percent

    @staticmethod
    def calculate_position_size(entry_price: float, max_position_size: float = config.POSITION_SIZE) -> float:
        """Calculate position size based on available capital"""
        return min(max_position_size, max_position_size)

    @staticmethod
    def get_take_profit_price(entry_price: float) -> float:
        """Calculate take profit price"""
        return entry_price * (1 + config.TAKE_PROFIT_PERCENT / 100)

    @staticmethod
    def get_stop_loss_price(entry_price: float) -> float:
        """Calculate stop loss price"""
        return entry_price * (1 - config.STOP_LOSS_PERCENT / 100)


class Logger:
    @staticmethod
    def setup_logging():
        """Setup logging configuration"""
        import os

        # Create logs directory if it doesn't exist
        os.makedirs(os.path.dirname(config.LOG_FILE), exist_ok=True)

        logging.basicConfig(
            level=getattr(logging, config.LOG_LEVEL),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(config.LOG_FILE),
                logging.StreamHandler()
            ]
        )


class DataValidator:
    @staticmethod
    def validate_token_address(address: str) -> bool:
        """Validate Solana token address format"""
        if not address or len(address) < 32 or len(address) > 44:
            return False
        # Basic base58 validation
        return bool(re.match(r'^[A-HJ-NP-Z1-9]+$', address))

    @staticmethod
    def validate_price(price: float) -> bool:
        """Validate price is reasonable"""
        return 0.00000001 <= price <= 1000000

    @staticmethod
    def sanitize_symbol(symbol: str) -> str:
        """Clean and validate token symbol"""
        if not symbol:
            return "UNKNOWN"
        return re.sub(r'[^A-Z0-9]', '', symbol.upper())[:10]


def format_currency(amount: float, decimals: int = 2) -> str:
    """Format currency with proper decimals"""
    if abs(amount) < 0.01:
        return f"${amount:.6f}"
    return f"${amount:,.{decimals}f}"


def format_percentage(percentage: float, decimals: int = 2) -> str:
    """Format percentage with proper sign and decimals"""
    sign = "+" if percentage > 0 else ""
    return f"{sign}{percentage:.{decimals}f}%"


def calculate_time_diff(start_time: datetime, end_time: datetime = None) -> str:
    """Calculate human readable time difference"""
    if end_time is None:
        end_time = datetime.now()

    diff = end_time - start_time
    days = diff.days
    hours, remainder = divmod(diff.seconds, 3600)
    minutes, _ = divmod(remainder, 60)

    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"