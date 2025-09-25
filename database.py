"""
Database operations for storing and retrieving trade data
"""

import sqlite3
import logging
import json
from datetime import datetime
from pathlib import Path
import threading

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path='data/trades.db'):
        self.db_path = db_path
        self.lock = threading.Lock()

        # Create data directory if it doesn't exist
        Path(db_path).parent.mkdir(exist_ok=True)

    def initialize(self):
        """Initialize database tables"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                # Create trades table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS trades (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        token_symbol TEXT NOT NULL,
                        token_address TEXT,
                        entry_price REAL NOT NULL,
                        exit_price REAL,
                        entry_time TIMESTAMP NOT NULL,
                        exit_time TIMESTAMP,
                        position_size REAL NOT NULL,
                        take_profit_price REAL,
                        stop_loss_price REAL,
                        take_profit_percentage REAL,
                        stop_loss_percentage REAL,
                        exit_type TEXT,
                        pnl REAL,
                        pnl_percentage REAL,
                        status TEXT DEFAULT 'OPEN',
                        message_id INTEGER,
                        message_text TEXT,
                        channel TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Create statistics table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS statistics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date DATE NOT NULL,
                        total_trades INTEGER,
                        winning_trades INTEGER,
                        losing_trades INTEGER,
                        total_pnl REAL,
                        win_rate REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Create indices for better performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(token_symbol)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_entry_time ON trades(entry_time)')

                conn.commit()
                conn.close()

                logger.info("Database initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise

    def save_trade(self, trade_data):
        """Save a trade to the database"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute('''
                    INSERT INTO trades (
                        token_symbol, token_address, entry_price, exit_price,
                        entry_time, exit_time, position_size, take_profit_price,
                        stop_loss_price, take_profit_percentage, stop_loss_percentage,
                        exit_type, pnl, pnl_percentage, status, message_id,
                        message_text, channel
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    trade_data.get('token_symbol'),
                    trade_data.get('token_address'),
                    trade_data.get('entry_price'),
                    trade_data.get('exit_price'),
                    trade_data.get('entry_time'),
                    trade_data.get('exit_time'),
                    trade_data.get('position_size'),
                    trade_data.get('take_profit_price'),
                    trade_data.get('stop_loss_price'),
                    trade_data.get('take_profit_percentage'),
                    trade_data.get('stop_loss_percentage'),
                    trade_data.get('exit_type'),
                    trade_data.get('pnl'),
                    trade_data.get('pnl_percentage'),
                    trade_data.get('status', 'OPEN'),
                    trade_data.get('message_id'),
                    trade_data.get('message_text'),
                    trade_data.get('channel'),
                ))

                conn.commit()
                trade_id = cursor.lastrowid
                conn.close()

                logger.info(f"Trade saved with ID: {trade_id}")
                return trade_id

        except Exception as e:
            logger.error(f"Error saving trade: {e}")
            return None

    def get_all_trades(self):
        """Get all trades from the database"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute('SELECT * FROM trades ORDER BY entry_time DESC')
                trades = [dict(row) for row in cursor.fetchall()]

                conn.close()
                return trades

        except Exception as e:
            logger.error(f"Error fetching trades: {e}")
            return []

    def get_recent_trades(self, limit=20):
        """Get recent trades"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute(
                    'SELECT * FROM trades ORDER BY entry_time DESC LIMIT ?',
                    (limit,)
                )
                trades = [dict(row) for row in cursor.fetchall()]

                conn.close()
                return trades

        except Exception as e:
            logger.error(f"Error fetching recent trades: {e}")
            return []

    def get_open_trades(self):
        """Get all open trades"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute('SELECT * FROM trades WHERE status = "OPEN"')
                trades = [dict(row) for row in cursor.fetchall()]

                conn.close()
                return trades

        except Exception as e:
            logger.error(f"Error fetching open trades: {e}")
            return []

    def update_trade(self, trade_id, update_data):
        """Update a trade"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                # Build update query dynamically
                fields = []
                values = []
                for key, value in update_data.items():
                    fields.append(f"{key} = ?")
                    values.append(value)

                values.append(trade_id)
                query = f"UPDATE trades SET {', '.join(fields)} WHERE id = ?"

                cursor.execute(query, values)
                conn.commit()
                conn.close()

                logger.info(f"Trade {trade_id} updated")
                return True

        except Exception as e:
            logger.error(f"Error updating trade {trade_id}: {e}")
            return False

    def save_daily_statistics(self, stats):
        """Save daily statistics"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute('''
                    INSERT INTO statistics (
                        date, total_trades, winning_trades, losing_trades,
                        total_pnl, win_rate
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    datetime.now().date(),
                    stats.get('total_trades'),
                    stats.get('winning_trades'),
                    stats.get('losing_trades'),
                    stats.get('total_pnl'),
                    stats.get('win_rate'),
                ))

                conn.commit()
                conn.close()

                logger.info("Daily statistics saved")

        except Exception as e:
            logger.error(f"Error saving statistics: {e}")

    def close(self):
        """Close database connection"""
        logger.info("Database connection closed")