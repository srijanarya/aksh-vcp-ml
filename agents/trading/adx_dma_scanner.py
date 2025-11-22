"""
ADX + 3-DMA Trend Scanner

Implements the proven trading strategy:
- Entry: close > 50 DMA AND close > 100 DMA AND close > 200 DMA AND ADX > 20
- Exit: close < 50 DMA OR ADX < 10

Based on 12-year backtested strategy showing:
- +265% total return
- 28.24% win rate with 1.681 profit factor
- 386 trades over 12 years

Author: Trading System
Created: 2025-11-18
"""

import logging
import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import numpy as np
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


@dataclass
class TradingSignal:
    """Trading signal with all relevant data"""
    symbol: str
    signal_type: str  # 'BUY' or 'SELL'
    date: str
    close_price: float

    # Moving averages
    dma_50: Optional[float] = None
    dma_100: Optional[float] = None
    dma_200: Optional[float] = None

    # ADX components
    adx: Optional[float] = None
    plus_di: Optional[float] = None
    minus_di: Optional[float] = None

    # Additional context
    volume: Optional[float] = None
    avg_volume_30d: Optional[float] = None
    volume_ratio: Optional[float] = None

    # Signal strength (for ranking)
    signal_strength: Optional[float] = None

    created_at: str = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


class ADXDMAScanner:
    """
    Scans stocks for ADX + 3-DMA trend signals

    Strategy Logic:
    ---------------
    BUY Signal:
        - close > 50 DMA
        - close > 100 DMA
        - close > 200 DMA
        - ADX > 20 (strong trend)

    SELL Signal:
        - close < 50 DMA (trend broken)
        OR
        - ADX < 10 (weak trend)

    Signal Strength Scoring:
    ------------------------
    Base score = 50
    +10 if close > all 3 DMAs by >2%
    +10 if ADX > 25 (very strong trend)
    +10 if volume > 2x average (confirmation)
    +10 if 50 DMA > 100 DMA > 200 DMA (aligned trend)
    +10 if +DI > -DI by >5 (strong bullish momentum)

    Max score = 100 (highest conviction)
    """

    def __init__(self, output_db_path: str):
        """
        Initialize scanner

        Args:
            output_db_path: Path to store signals database
        """
        self.output_db_path = output_db_path
        self._initialize_database()
        logger.info(f"ADXDMAScanner initialized: output_db={output_db_path}")

    def _initialize_database(self):
        """Create trading_signals table"""
        conn = sqlite3.connect(self.output_db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trading_signals (
                signal_id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                signal_type TEXT NOT NULL,
                date DATE NOT NULL,
                close_price REAL NOT NULL,

                dma_50 REAL,
                dma_100 REAL,
                dma_200 REAL,

                adx REAL,
                plus_di REAL,
                minus_di REAL,

                volume REAL,
                avg_volume_30d REAL,
                volume_ratio REAL,

                signal_strength REAL,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, date, signal_type) ON CONFLICT REPLACE
            )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_symbol_date ON trading_signals(symbol, date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_signal_type ON trading_signals(signal_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_date ON trading_signals(date)")

        conn.commit()
        conn.close()
        logger.info("Database schema initialized")

    def calculate_dma(self, prices: pd.Series, period: int) -> pd.Series:
        """
        Calculate simple moving average (DMA = Daily Moving Average)

        Args:
            prices: Series of closing prices
            period: Moving average period (50, 100, or 200)

        Returns:
            Series of moving average values
        """
        return prices.rolling(window=period, min_periods=period).mean()

    def calculate_adx(self, high: pd.Series, low: pd.Series, close: pd.Series,
                      period: int = 14, smoothing: int = 14) -> Dict[str, pd.Series]:
        """
        Calculate ADX (Average Directional Index) with +DI and -DI

        ADX measures trend strength (0-100):
        - ADX > 25 = strong trend
        - ADX 20-25 = developing trend
        - ADX < 20 = weak/no trend

        Args:
            high: Series of high prices
            low: Series of low prices
            close: Series of close prices
            period: ADX period (default: 14)
            smoothing: Smoothing period (default: 14)

        Returns:
            Dict with 'adx', 'plus_di', 'minus_di' Series
        """
        # Calculate True Range (TR)
        high_low = high - low
        high_close = np.abs(high - close.shift())
        low_close = np.abs(low - close.shift())

        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)

        # Calculate Directional Movement (+DM and -DM)
        up_move = high - high.shift()
        down_move = low.shift() - low

        plus_dm = pd.Series(np.where((up_move > down_move) & (up_move > 0), up_move, 0), index=close.index)
        minus_dm = pd.Series(np.where((down_move > up_move) & (down_move > 0), down_move, 0), index=close.index)

        # Smooth TR, +DM, -DM using Wilder's smoothing (EMA with alpha=1/period)
        atr = tr.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
        plus_dm_smooth = plus_dm.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
        minus_dm_smooth = minus_dm.ewm(alpha=1/period, min_periods=period, adjust=False).mean()

        # Calculate +DI and -DI
        plus_di = 100 * (plus_dm_smooth / atr)
        minus_di = 100 * (minus_dm_smooth / atr)

        # Calculate DX (Directional Index)
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)

        # Calculate ADX (smoothed DX)
        adx = dx.ewm(alpha=1/smoothing, min_periods=smoothing, adjust=False).mean()

        return {
            'adx': adx.round(2),
            'plus_di': plus_di.round(2),
            'minus_di': minus_di.round(2)
        }

    def fetch_stock_data(self, symbol: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """
        Fetch historical stock data from yfinance

        Args:
            symbol: NSE symbol (e.g., "TCS.NS")
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            DataFrame with OHLCV data or None if fetch fails
        """
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date)

            if df.empty:
                logger.warning(f"No data found for {symbol}")
                return None

            # Rename columns to lowercase
            df = df.rename(columns={
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })

            # Reset index to get date as column
            df = df.reset_index()
            df['date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
            df = df.drop('Date', axis=1)

            return df

        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return None

    def calculate_signal_strength(self, close: float, dma_50: float, dma_100: float,
                                   dma_200: float, adx: float, plus_di: float,
                                   minus_di: float, volume: float, avg_volume: float) -> float:
        """
        Calculate signal strength score (0-100)

        Higher score = higher conviction signal
        """
        score = 50  # Base score

        # +10 if close > all DMAs by >2%
        if (close > dma_50 * 1.02 and close > dma_100 * 1.02 and close > dma_200 * 1.02):
            score += 10

        # +10 if ADX > 25 (very strong trend)
        if adx > 25:
            score += 10

        # +10 if volume > 2x average
        if volume > avg_volume * 2:
            score += 10

        # +10 if DMAs aligned (50 > 100 > 200)
        if dma_50 > dma_100 > dma_200:
            score += 10

        # +10 if +DI > -DI by >5 (strong bullish momentum)
        if plus_di > minus_di + 5:
            score += 10

        return score

    def scan_symbol(self, symbol: str, scan_date: Optional[str] = None) -> List[TradingSignal]:
        """
        Scan a single symbol for trading signals

        Args:
            symbol: NSE symbol (e.g., "TCS.NS")
            scan_date: Date to scan (YYYY-MM-DD). If None, uses today.

        Returns:
            List of TradingSignal objects (may be empty if no signals)
        """
        if scan_date is None:
            scan_date = datetime.now().strftime('%Y-%m-%d')

        # Fetch 250 days of data (enough for 200 DMA + buffer)
        start_date = (datetime.strptime(scan_date, '%Y-%m-%d') - timedelta(days=400)).strftime('%Y-%m-%d')

        df = self.fetch_stock_data(symbol, start_date, scan_date)

        if df is None or len(df) < 200:
            logger.debug(f"Insufficient data for {symbol}: need 200 days, got {len(df) if df is not None else 0}")
            return []

        # Calculate indicators
        df['dma_50'] = self.calculate_dma(df['close'], 50)
        df['dma_100'] = self.calculate_dma(df['close'], 100)
        df['dma_200'] = self.calculate_dma(df['close'], 200)

        adx_data = self.calculate_adx(df['high'], df['low'], df['close'], period=14, smoothing=14)
        df['adx'] = adx_data['adx']
        df['plus_di'] = adx_data['plus_di']
        df['minus_di'] = adx_data['minus_di']

        # Calculate volume indicators
        df['avg_volume_30d'] = df['volume'].rolling(window=30, min_periods=30).mean()
        df['volume_ratio'] = df['volume'] / df['avg_volume_30d']

        # Get latest values
        latest = df.iloc[-1]

        # Check for missing data
        if pd.isna(latest['dma_200']) or pd.isna(latest['adx']):
            logger.debug(f"Missing indicator data for {symbol}")
            return []

        signals = []

        # Check BUY signal
        buy_condition = (
            latest['close'] > latest['dma_50'] and
            latest['close'] > latest['dma_100'] and
            latest['close'] > latest['dma_200'] and
            latest['adx'] > 20
        )

        if buy_condition:
            signal_strength = self.calculate_signal_strength(
                latest['close'], latest['dma_50'], latest['dma_100'],
                latest['dma_200'], latest['adx'], latest['plus_di'],
                latest['minus_di'], latest['volume'], latest['avg_volume_30d']
            )

            signals.append(TradingSignal(
                symbol=symbol,
                signal_type='BUY',
                date=latest['date'],
                close_price=float(latest['close']),
                dma_50=float(latest['dma_50']),
                dma_100=float(latest['dma_100']),
                dma_200=float(latest['dma_200']),
                adx=float(latest['adx']),
                plus_di=float(latest['plus_di']),
                minus_di=float(latest['minus_di']),
                volume=float(latest['volume']),
                avg_volume_30d=float(latest['avg_volume_30d']),
                volume_ratio=float(latest['volume_ratio']),
                signal_strength=signal_strength
            ))

        # Check SELL signal (for positions we might hold)
        sell_condition = (
            latest['close'] < latest['dma_50'] or
            latest['adx'] < 10
        )

        if sell_condition:
            signals.append(TradingSignal(
                symbol=symbol,
                signal_type='SELL',
                date=latest['date'],
                close_price=float(latest['close']),
                dma_50=float(latest['dma_50']),
                dma_100=float(latest['dma_100']),
                dma_200=float(latest['dma_200']),
                adx=float(latest['adx']),
                plus_di=float(latest['plus_di']),
                minus_di=float(latest['minus_di']),
                volume=float(latest['volume']),
                avg_volume_30d=float(latest['avg_volume_30d']),
                volume_ratio=float(latest['volume_ratio']),
                signal_strength=None  # SELL signals don't need strength
            ))

        return signals

    def scan_multiple_symbols(self, symbols: List[str], scan_date: Optional[str] = None) -> pd.DataFrame:
        """
        Scan multiple symbols for trading signals

        Args:
            symbols: List of NSE symbols (e.g., ["TCS.NS", "INFY.NS"])
            scan_date: Date to scan (YYYY-MM-DD). If None, uses today.

        Returns:
            DataFrame with all signals found
        """
        all_signals = []

        for symbol in symbols:
            logger.info(f"Scanning {symbol}...")
            signals = self.scan_symbol(symbol, scan_date)
            all_signals.extend(signals)

        if not all_signals:
            logger.warning("No signals found across all symbols")
            return pd.DataFrame()

        # Convert to DataFrame
        df = pd.DataFrame([asdict(s) for s in all_signals])

        # Save to database
        self._save_signals(all_signals)

        # Sort by signal strength (BUY signals only)
        df_buy = df[df['signal_type'] == 'BUY'].sort_values('signal_strength', ascending=False)
        df_sell = df[df['signal_type'] == 'SELL']

        df = pd.concat([df_buy, df_sell], ignore_index=True)

        logger.info(f"Scan complete: {len(df_buy)} BUY signals, {len(df_sell)} SELL signals")

        return df

    def _save_signals(self, signals: List[TradingSignal]):
        """Save signals to database"""
        if not signals:
            return

        conn = sqlite3.connect(self.output_db_path)
        cursor = conn.cursor()

        for signal in signals:
            signal_dict = asdict(signal)
            cursor.execute("""
                INSERT OR REPLACE INTO trading_signals (
                    symbol, signal_type, date, close_price,
                    dma_50, dma_100, dma_200,
                    adx, plus_di, minus_di,
                    volume, avg_volume_30d, volume_ratio,
                    signal_strength, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                signal_dict['symbol'], signal_dict['signal_type'], signal_dict['date'],
                signal_dict['close_price'], signal_dict['dma_50'], signal_dict['dma_100'],
                signal_dict['dma_200'], signal_dict['adx'], signal_dict['plus_di'],
                signal_dict['minus_di'], signal_dict['volume'], signal_dict['avg_volume_30d'],
                signal_dict['volume_ratio'], signal_dict['signal_strength'], signal_dict['created_at']
            ))

        conn.commit()
        conn.close()
        logger.info(f"Saved {len(signals)} signals to database")


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    scanner = ADXDMAScanner(output_db_path="/Users/srijan/Desktop/aksh/trading_signals.db")

    # Test with a few NSE symbols
    test_symbols = [
        "TCS.NS",
        "INFY.NS",
        "RELIANCE.NS",
        "HDFCBANK.NS",
        "ICICIBANK.NS"
    ]

    print("\n" + "="*70)
    print("ADX + 3-DMA SCANNER - TEST RUN")
    print("="*70)

    results = scanner.scan_multiple_symbols(test_symbols)

    if not results.empty:
        print(f"\n{'='*70}")
        print("BUY SIGNALS (Ranked by Strength)")
        print("="*70)
        buy_signals = results[results['signal_type'] == 'BUY']
        if not buy_signals.empty:
            for idx, row in buy_signals.iterrows():
                print(f"\n{row['symbol']}")
                print(f"  Price: ₹{row['close_price']:.2f}")
                print(f"  50 DMA: ₹{row['dma_50']:.2f} | 100 DMA: ₹{row['dma_100']:.2f} | 200 DMA: ₹{row['dma_200']:.2f}")
                print(f"  ADX: {row['adx']:.1f} | +DI: {row['plus_di']:.1f} | -DI: {row['minus_di']:.1f}")
                print(f"  Volume Ratio: {row['volume_ratio']:.2f}x")
                print(f"  Signal Strength: {row['signal_strength']:.0f}/100")
        else:
            print("  No BUY signals found")

        print(f"\n{'='*70}")
        print("SELL SIGNALS")
        print("="*70)
        sell_signals = results[results['signal_type'] == 'SELL']
        if not sell_signals.empty:
            for idx, row in sell_signals.iterrows():
                print(f"\n{row['symbol']}")
                print(f"  Price: ₹{row['close_price']:.2f}")
                print(f"  50 DMA: ₹{row['dma_50']:.2f} | ADX: {row['adx']:.1f}")
                print(f"  Reason: {'Below 50 DMA' if row['close_price'] < row['dma_50'] else 'Weak ADX'}")
        else:
            print("  No SELL signals found")
    else:
        print("\n No signals found")
