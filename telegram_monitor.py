"""
Telegram channel monitoring module
"""

import asyncio
import logging
import re
from datetime import datetime
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError
import json

logger = logging.getLogger(__name__)

class TelegramMonitor:
    def __init__(self, config, db_manager):
        self.config = config
        self.db = db_manager
        self.client = None
        self.running = False
        self.processed_messages = set()

    async def start_monitoring(self):
        """Start monitoring the Telegram channel"""
        try:
            # Initialize Telegram client
            self.client = TelegramClient(
                self.config.SESSION_NAME,
                self.config.API_ID,
                self.config.API_HASH
            )

            await self.client.start(phone=self.config.PHONE_NUMBER)
            logger.info("Telegram client connected successfully")

            # Get channel entity
            channel = await self.client.get_entity(self.config.CHANNEL_USERNAME)
            logger.info(f"Connected to channel: {channel.title}")

            # Register event handler for new messages
            @self.client.on(events.NewMessage(chats=channel))
            async def handle_new_message(event):
                await self.process_message(event.message)

            # Process historical messages (last 100)
            logger.info("Processing historical messages...")
            async for message in self.client.iter_messages(channel, limit=100):
                if message.id not in self.processed_messages:
                    await self.process_message(message)

            logger.info("Starting real-time monitoring...")
            self.running = True

            # Keep the client running
            while self.running:
                await asyncio.sleep(1)

        except SessionPasswordNeededError:
            logger.error("Two-factor authentication is enabled. Please disable it temporarily.")
            raise
        except Exception as e:
            logger.error(f"Error in monitoring: {e}")
            raise

    async def process_message(self, message):
        """Process a Telegram message for trading signals"""
        try:
            if message.id in self.processed_messages:
                return

            self.processed_messages.add(message.id)

            # Extract token information
            token_info = self.extract_token_info(message.text)

            if token_info:
                logger.info(f"New token detected: {token_info}")

                # Create a backtest trade
                trade_data = {
                    'token_symbol': token_info.get('symbol', 'UNKNOWN'),
                    'token_address': token_info.get('address', ''),
                    'entry_price': token_info.get('price', 0.001),  # Default price if not found
                    'entry_time': message.date,
                    'message_id': message.id,
                    'message_text': message.text[:500],  # Store first 500 chars
                    'channel': self.config.CHANNEL_USERNAME,
                    'position_size': self.config.POSITION_SIZE,
                    'take_profit_percentage': self.config.TAKE_PROFIT_PERCENTAGE,
                    'stop_loss_percentage': self.config.STOP_LOSS_PERCENTAGE,
                }

                # Simulate the trade
                self.simulate_trade(trade_data)

        except Exception as e:
            logger.error(f"Error processing message {message.id}: {e}")

    def extract_token_info(self, text):
        """Extract token information from message text"""
        if not text:
            return None

        token_info = {}

        # Look for token symbols
        for pattern in self.config.TOKEN_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                token_info['symbol'] = match.group(1).upper()
                break

        # Look for contract addresses
        address_pattern = r'[A-Za-z0-9]{32,44}'
        address_match = re.search(address_pattern, text)
        if address_match:
            token_info['address'] = address_match.group(0)

        # Look for price information
        for pattern in self.config.PRICE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    token_info['price'] = float(match.group(1))
                    break
                except:
                    pass

        # If no price found, use a default
        if 'price' not in token_info and 'symbol' in token_info:
            token_info['price'] = 0.001  # Default price

        return token_info if 'symbol' in token_info else None

    def simulate_trade(self, trade_data):
        """Simulate a trade with take profit and stop loss"""
        entry_price = trade_data['entry_price']
        take_profit_price = entry_price * (1 + self.config.TAKE_PROFIT_PERCENTAGE / 100)
        stop_loss_price = entry_price * (1 - self.config.STOP_LOSS_PERCENTAGE / 100)

        # For backtesting, randomly determine if TP or SL was hit
        # In real scenario, you would check actual price movement
        import random

        # Simulate 60% win rate for backtesting
        if random.random() < 0.6:
            # Take profit hit
            exit_price = take_profit_price
            exit_type = 'TAKE_PROFIT'
            pnl = trade_data['position_size'] * (self.config.TAKE_PROFIT_PERCENTAGE / 100)
        else:
            # Stop loss hit
            exit_price = stop_loss_price
            exit_type = 'STOP_LOSS'
            pnl = -trade_data['position_size'] * (self.config.STOP_LOSS_PERCENTAGE / 100)

        trade_data.update({
            'exit_price': exit_price,
            'exit_time': datetime.now(),
            'exit_type': exit_type,
            'take_profit_price': take_profit_price,
            'stop_loss_price': stop_loss_price,
            'pnl': pnl,
            'pnl_percentage': (exit_price - entry_price) / entry_price * 100,
            'status': 'CLOSED',
        })

        # Save to database
        self.db.save_trade(trade_data)
        logger.info(f"Trade completed: {trade_data['token_symbol']} - {exit_type} - PnL: ${pnl:.2f}")

    async def stop(self):
        """Stop monitoring"""
        self.running = False
        if self.client:
            await self.client.disconnect()
        logger.info("Telegram monitor stopped")