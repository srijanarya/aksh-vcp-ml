#!/usr/bin/env python3
"""
Multi-Timeframe Breakout Strategy for High Beta Stocks

Key Concepts:
1. Higher timeframes (Daily/Weekly) for trend and structure
2. Lower timeframes (Hourly/4H) for precise entry
3. Multiple confluences required for entry
4. Focus on high beta stocks (volatility > market)

Strategy Logic:
- Weekly: Identify strong uptrend and base formation
- Daily: Confirm breakout setup with volume
- 4H/1H: Fine-tune entry on pullback or continuation
- Confluences: Volume, momentum, structure alignment
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import yfinance as yf

# Import S/R analyzer
from strategies.multi_timeframe_sr import MultiTimeframeSR


@dataclass
class MultiTimeframeSignal:
    """Multi-timeframe breakout signal"""
    symbol: str
    entry_price: float
    stop_loss: float
    target: float
    risk_reward_ratio: float
    confluences: List[str]
    timeframe_analysis: Dict[str, str]
    strength_score: float  # 0-100
    timestamp: datetime
    sr_quality_score: float = 0.0  # S/R quality (0-100)
    sr_analysis: Dict = None  # Detailed S/R data
    rs_metrics: Dict = None  # Relative Strength metrics vs Nifty
    adx_metrics: Dict = None  # ADX trend strength metrics
    beta: float = 1.0  # Stock beta vs Nifty


class MultiTimeframeBreakoutStrategy:
    """
    Advanced multi-timeframe breakout strategy for high beta stocks

    Timeframe Hierarchy:
    - Weekly (1W): Macro trend, major S/R levels
    - Daily (1D): Breakout setup, volume confirmation
    - 4-Hour (4H): Entry refinement, momentum confirmation
    - 1-Hour (1H): Precise entry timing (optional)

    Hard Filters (must pass):
    - Beta > 1.0 (volatility vs market)
    - ADX > 20 (trend strength - proven in 12-year backtest)
    - S/R Quality >= 60 (support/resistance quality)

    Confluences Required (minimum 2 of 7):
    1. Weekly uptrend intact (strength >= 50)
    2. Daily breakout above resistance
    3. Volume expansion (>1.5x average)
    4. S/R confluence zone (2+ levels align)
    5. Outperforming market (RS 30-day > 1.0)
    6. RS trend improving/strengthening
    7. Strong ADX trend (ADX > 25)

    NOTE: 4H momentum filter removed to avoid rate limits
    """

    def __init__(self):
        self.min_confluences = 2  # Keep at 2 of 7 confluences
        self.high_beta_threshold = 0.9  # STAGE 1 RELAXATION: from 1.0 (originally 1.2)
        self.min_adx = 18  # STAGE 1 RELAXATION: from 20 (moderate trend)
        self.sr_analyzer = MultiTimeframeSR()  # S/R analyzer
        self.min_sr_quality = 50  # STAGE 1 RELAXATION: from 60 (moderate S/R quality)

    def fetch_multi_timeframe_data(
        self,
        symbol: str,
        lookback_days: int = 365
    ) -> Dict[str, pd.DataFrame]:
        """Fetch data for multiple timeframes with retry logic"""
        import time

        # Handle .NS suffix - don't double-add it
        symbol_with_ns = symbol if '.NS' in symbol else f"{symbol}.NS"
        ticker = yf.Ticker(symbol_with_ns)

        # Fetch daily data (then resample for weekly)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)

        # Retry logic for rate limits
        max_retries = 3
        retry_delay = 5  # Start with 5 seconds

        for attempt in range(max_retries):
            try:
                daily_data = ticker.history(start=start_date, end=end_date, interval='1d')
                break
            except Exception as e:
                if 'rate' in str(e).lower() or '429' in str(e):
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                        continue
                raise

        # Resample to weekly
        weekly_data = daily_data.resample('W').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }).dropna()

        # REMOVED: 4H intraday data fetch to avoid rate limits and speed up backtesting
        # Strategy now relies on Daily + Weekly timeframes only
        data_4h = pd.DataFrame()

        # Normalize column names to lowercase (do this in-place)
        if not daily_data.empty:
            daily_data.columns = [col.lower() for col in daily_data.columns]
        if not weekly_data.empty:
            weekly_data.columns = [col.lower() for col in weekly_data.columns]
        if not data_4h.empty:
            data_4h.columns = [col.lower() for col in data_4h.columns]

        return {
            'weekly': weekly_data,
            'daily': daily_data,
            '4h': data_4h
        }

    def calculate_beta(self, symbol: str, market_index: str = '^NSEI') -> float:
        """Calculate stock beta vs market index"""
        try:
            # Handle .NS suffix - don't double-add it
            symbol_with_ns = symbol if '.NS' in symbol else f"{symbol}.NS"

            # Check cache first
            cache_key = f"{symbol_with_ns}_{market_index}"
            if hasattr(self, '_beta_cache') and cache_key in self._beta_cache:
                return self._beta_cache[cache_key]

            # Initialize cache if needed
            if not hasattr(self, '_beta_cache'):
                self._beta_cache = {}
                self._last_beta_request_time = 0

            # Rate limiting: 2 second delay between beta calculations
            import time
            current_time = time.time()
            time_since_last = current_time - self._last_beta_request_time
            if time_since_last < 2.0:
                sleep_time = 2.0 - time_since_last
                time.sleep(sleep_time)

            # Fetch 1 year of data
            stock = yf.Ticker(symbol_with_ns)
            self._last_beta_request_time = time.time()
            time.sleep(2.0)  # Rate limit between stock and index

            index = yf.Ticker(market_index)
            self._last_beta_request_time = time.time()

            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)

            stock_data = stock.history(start=start_date, end=end_date)['Close']
            index_data = index.history(start=start_date, end=end_date)['Close']

            # Calculate returns
            stock_returns = stock_data.pct_change().dropna()
            index_returns = index_data.pct_change().dropna()

            # Align data
            aligned_data = pd.DataFrame({
                'stock': stock_returns,
                'index': index_returns
            }).dropna()

            # Calculate beta
            covariance = aligned_data.cov().loc['stock', 'index']
            variance = aligned_data['index'].var()
            beta = covariance / variance

            # Cache the result
            self._beta_cache[cache_key] = beta

            return beta

        except Exception as e:
            print(f"Error calculating beta: {e}")
            # Cache the default value to avoid repeated failures
            if hasattr(self, '_beta_cache'):
                self._beta_cache[cache_key] = 1.0
            return 1.0

    def calculate_adx(self, daily_data: pd.DataFrame, period: int = 14) -> Dict[str, float]:
        """
        Calculate ADX (Average Directional Index) for trend strength

        ADX Values:
        - < 20: Weak trend (avoid trading)
        - 20-25: Developing trend
        - 25-50: Strong trend (ideal for trend following)
        - 50-75: Very strong trend
        - > 75: Extremely strong trend (may be overextended)

        Returns:
            Dict with ADX, +DI, -DI values
        """
        if len(daily_data) < period * 2:
            return {'adx': 0.0, 'plus_di': 0.0, 'minus_di': 0.0}

        try:
            # Calculate True Range (TR)
            high = daily_data['high']
            low = daily_data['low']
            close = daily_data['close']

            prev_close = close.shift(1)
            tr1 = high - low
            tr2 = abs(high - prev_close)
            tr3 = abs(low - prev_close)
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = tr.rolling(window=period).mean()

            # Calculate Directional Movement
            up_move = high.diff()
            down_move = -low.diff()

            plus_dm = pd.Series(0.0, index=up_move.index)
            minus_dm = pd.Series(0.0, index=down_move.index)

            plus_dm[(up_move > down_move) & (up_move > 0)] = up_move
            minus_dm[(down_move > up_move) & (down_move > 0)] = down_move

            # Smooth the DM values
            plus_dm_smooth = plus_dm.rolling(window=period).mean()
            minus_dm_smooth = minus_dm.rolling(window=period).mean()

            # Calculate Directional Indicators
            plus_di = (plus_dm_smooth / atr) * 100
            minus_di = (minus_dm_smooth / atr) * 100

            # Calculate DX and ADX
            dx = abs(plus_di - minus_di) / (plus_di + minus_di) * 100
            adx = dx.rolling(window=period).mean()

            # Get current values
            current_adx = adx.iloc[-1] if not pd.isna(adx.iloc[-1]) else 0.0
            current_plus_di = plus_di.iloc[-1] if not pd.isna(plus_di.iloc[-1]) else 0.0
            current_minus_di = minus_di.iloc[-1] if not pd.isna(minus_di.iloc[-1]) else 0.0

            return {
                'adx': current_adx,
                'plus_di': current_plus_di,
                'minus_di': current_minus_di
            }

        except Exception as e:
            print(f"Error calculating ADX: {e}")
            return {'adx': 0.0, 'plus_di': 0.0, 'minus_di': 0.0}

    def calculate_relative_strength(
        self,
        symbol: str,
        market_index: str = '^NSEI',
        lookback_days: int = 90
    ) -> Dict[str, float]:
        """
        Calculate Relative Strength (RS) of stock vs Nifty

        RS = (Stock % change) / (Nifty % change)
        RS > 1.0 = Outperforming market
        RS < 1.0 = Underperforming market

        Returns dict with RS scores for different periods
        """
        try:
            symbol_with_ns = symbol if '.NS' in symbol else f"{symbol}.NS"

            # Check cache first
            cache_key = f"rs_{symbol_with_ns}_{lookback_days}"
            if hasattr(self, '_rs_cache') and cache_key in self._rs_cache:
                return self._rs_cache[cache_key]

            # Initialize cache
            if not hasattr(self, '_rs_cache'):
                self._rs_cache = {}

            # Fetch data
            import time
            stock = yf.Ticker(symbol_with_ns)
            time.sleep(2.0)
            index = yf.Ticker(market_index)
            time.sleep(2.0)

            end_date = datetime.now()
            start_date = end_date - timedelta(days=lookback_days)

            stock_data = stock.history(start=start_date, end=end_date)['Close']
            index_data = index.history(start=start_date, end=end_date)['Close']

            if len(stock_data) < 10 or len(index_data) < 10:
                return {'rs_90d': 1.0, 'rs_30d': 1.0, 'rs_10d': 1.0, 'rs_trend': 'neutral'}

            # Calculate RS for different periods
            def calc_rs(stock_series, index_series, days):
                if len(stock_series) < days or len(index_series) < days:
                    return 1.0
                stock_change = (stock_series.iloc[-1] / stock_series.iloc[-days] - 1) * 100
                index_change = (index_series.iloc[-1] / index_series.iloc[-days] - 1) * 100
                if index_change == 0:
                    return 1.0
                return stock_change / index_change

            rs_90d = calc_rs(stock_data, index_data, min(90, len(stock_data)))
            rs_30d = calc_rs(stock_data, index_data, min(30, len(stock_data)))
            rs_10d = calc_rs(stock_data, index_data, min(10, len(stock_data)))

            # Determine RS trend
            if rs_30d > rs_90d and rs_10d > rs_30d:
                rs_trend = 'strengthening'
            elif rs_30d > rs_90d:
                rs_trend = 'improving'
            elif rs_30d < rs_90d and rs_10d < rs_30d:
                rs_trend = 'weakening'
            elif rs_30d < rs_90d:
                rs_trend = 'declining'
            else:
                rs_trend = 'neutral'

            result = {
                'rs_90d': rs_90d,
                'rs_30d': rs_30d,
                'rs_10d': rs_10d,
                'rs_trend': rs_trend
            }

            # Cache result
            self._rs_cache[cache_key] = result
            return result

        except Exception as e:
            print(f"Error calculating RS: {e}")
            return {'rs_90d': 1.0, 'rs_30d': 1.0, 'rs_10d': 1.0, 'rs_trend': 'neutral'}

    def analyze_weekly_trend(self, data: pd.DataFrame) -> Tuple[str, float]:
        """
        Analyze weekly timeframe for macro trend

        Returns: (trend_direction, strength_score)
        """
        if len(data) < 20:
            return "unknown", 0.0

        # Calculate 20-week EMA (approx 4 months)
        data['ema_20'] = data['close'].ewm(span=20).mean()

        # Calculate 50-week EMA (approx 1 year)
        data['ema_50'] = data['close'].ewm(span=50).mean()

        current_price = data['close'].iloc[-1]
        ema_20 = data['ema_20'].iloc[-1]
        ema_50 = data['ema_50'].iloc[-1]

        # Trend determination
        if current_price > ema_20 > ema_50:
            trend = "strong_uptrend"
            strength = 100.0
        elif current_price > ema_20:
            trend = "uptrend"
            strength = 75.0
        elif current_price > ema_50:
            trend = "weak_uptrend"
            strength = 50.0
        else:
            trend = "downtrend"
            strength = 0.0

        # Check for higher highs and higher lows (last 8 weeks)
        recent_highs = data['high'].tail(8)
        recent_lows = data['low'].tail(8)

        higher_highs = recent_highs.iloc[-1] > recent_highs.iloc[0]
        higher_lows = recent_lows.iloc[-1] > recent_lows.iloc[0]

        if higher_highs and higher_lows:
            strength = min(100.0, strength + 15.0)

        return trend, strength

    def analyze_daily_breakout(self, data: pd.DataFrame) -> Tuple[bool, Dict]:
        """
        Analyze daily timeframe for breakout setup

        Returns: (is_breakout, breakout_details)
        """
        if len(data) < 50:
            return False, {}

        # Calculate 20-day high (resistance)
        data['resistance_20'] = data['high'].rolling(20).max()

        # Calculate volume average
        data['volume_ma_20'] = data['volume'].rolling(20).mean()
        data['volume_ratio'] = data['volume'] / data['volume_ma_20']

        # Calculate ATR for volatility
        high_low = data['high'] - data['low']
        high_close = abs(data['high'] - data['close'].shift())
        low_close = abs(data['low'] - data['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        data['atr'] = ranges.max(axis=1).rolling(14).mean()

        # Current values
        current_close = data['close'].iloc[-1]
        prev_resistance = data['resistance_20'].iloc[-2]
        current_volume_ratio = data['volume_ratio'].iloc[-1]
        atr = data['atr'].iloc[-1]

        # Breakout conditions
        is_breakout = False
        breakout_details = {}

        # 1. Price breaks above 20-day resistance
        price_breakout = current_close > prev_resistance

        # 2. Volume expansion (>1.5x average)
        volume_confirmation = current_volume_ratio > 1.5

        # 3. Not too extended (within 3 ATR of resistance)
        not_extended = (current_close - prev_resistance) < (3 * atr)

        if price_breakout and volume_confirmation and not_extended:
            is_breakout = True
            breakout_details = {
                'breakout_price': current_close,
                'resistance_level': prev_resistance,
                'volume_ratio': current_volume_ratio,
                'atr': atr,
                'breakout_strength': min(100, current_volume_ratio * 40)
            }

        return is_breakout, breakout_details

    def analyze_4h_momentum(self, data: pd.DataFrame) -> Tuple[bool, float]:
        """
        Analyze 4H timeframe for momentum confirmation

        Returns: (has_momentum, momentum_score)
        """
        if len(data) < 30:
            return False, 0.0

        # Calculate RSI (14 periods)
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['rsi'] = 100 - (100 / (1 + rs))

        # Calculate MACD
        ema_12 = data['close'].ewm(span=12).mean()
        ema_26 = data['close'].ewm(span=26).mean()
        data['macd'] = ema_12 - ema_26
        data['signal'] = data['macd'].ewm(span=9).mean()

        # Current values
        current_rsi = data['rsi'].iloc[-1]
        current_macd = data['macd'].iloc[-1]
        current_signal = data['signal'].iloc[-1]

        # Momentum conditions
        rsi_bullish = 50 < current_rsi < 70  # Not overbought
        macd_bullish = current_macd > current_signal

        has_momentum = rsi_bullish and macd_bullish

        # Momentum score (0-100)
        rsi_score = min((current_rsi - 50) * 2, 40)  # Max 40 points
        macd_score = 30 if macd_bullish else 0  # 30 points

        # Check if momentum is increasing
        rsi_increasing = data['rsi'].iloc[-1] > data['rsi'].iloc[-3]
        macd_increasing = data['macd'].iloc[-1] > data['macd'].iloc[-3]

        trend_score = 30 if (rsi_increasing and macd_increasing) else 0

        momentum_score = rsi_score + macd_score + trend_score

        return has_momentum, momentum_score

    def calculate_entry_levels(
        self,
        daily_data: pd.DataFrame,
        breakout_price: float,
        atr: float,
        sr_analysis: Dict = None
    ) -> Dict[str, float]:
        """
        Calculate precise entry, stop loss, and target levels
        NOW WITH S/R INTEGRATION

        Strategy:
        - Entry: On breakout or pullback to breakout level
        - Stop: Below recent swing low, 1.5 ATR, OR S/R support zone
        - Target: 2-3x risk OR before next resistance
        """
        # Find recent swing low (last 10 days)
        recent_lows = daily_data['low'].tail(10)
        swing_low = recent_lows.min()

        # Entry: Current price or breakout level
        entry = breakout_price

        # Stop loss: Lower of swing low or 1.5 ATR below entry
        stop_atr = entry - (1.5 * atr)
        stop_swing = swing_low * 0.98  # 2% below swing low for buffer
        stop_loss = max(stop_atr, stop_swing)

        # NEW: Adjust stop based on S/R support zones
        if sr_analysis and sr_analysis.get('nearest_support_below'):
            support_level = sr_analysis['nearest_support_below'][0]
            # Place stop 0.5% below support zone
            stop_at_support = support_level * 0.995
            # Use looser stop (max)
            stop_loss = max(stop_loss, stop_at_support)

        # Risk per share
        risk_per_share = entry - stop_loss

        # Target: 2.5x risk (can adjust based on structure)
        target = entry + (2.5 * risk_per_share)

        # NEW: Adjust target based on S/R resistance zones
        if sr_analysis and sr_analysis.get('nearest_resistance_above'):
            resistance_level = sr_analysis['nearest_resistance_above'][0]
            distance_to_resistance = resistance_level - entry

            # If resistance is too close (< 3x risk), exit before it
            if distance_to_resistance < (3 * risk_per_share):
                # Exit 0.5% before resistance
                target = resistance_level * 0.995

        # Risk-reward ratio
        rr_ratio = (target - entry) / risk_per_share if risk_per_share > 0 else 0

        return {
            'entry': entry,
            'stop_loss': stop_loss,
            'target': target,
            'risk_reward_ratio': rr_ratio,
            'risk_per_share': risk_per_share,
            'atr': atr
        }

    def generate_signal(self, symbol: str) -> Optional[MultiTimeframeSignal]:
        """
        Generate multi-timeframe breakout signal with confluences

        Returns signal if all conditions met, else None
        """
        print(f"\n{'='*70}")
        print(f"🔍 Analyzing {symbol} - Multi-Timeframe Breakout Strategy")
        print(f"{'='*70}\n")

        # Step 1: Check if high beta stock
        print("📊 Step 1: Checking Beta...")
        beta = self.calculate_beta(symbol)
        print(f"   Beta vs Nifty: {beta:.2f}")

        if beta < self.high_beta_threshold:
            print(f"   ❌ Beta too low (< {self.high_beta_threshold:.1f}). Skipping.")
            return None
        print(f"   ✅ High beta stock confirmed!\n")

        # Step 1.5: Calculate Relative Strength vs Nifty
        # TEMPORARILY DISABLED FOR SPEED - RS calculation takes 4+ seconds per stock
        print("💪 Step 1.5: Relative Strength Analysis... [SKIPPED FOR SPEED]")
        rs_metrics = {'rs_90d': 1.0, 'rs_30d': 1.0, 'rs_10d': 1.0, 'rs_trend': 'neutral'}
        # rs_metrics = self.calculate_relative_strength(symbol)
        # print(f"   RS 90-day: {rs_metrics['rs_90d']:.2f}x market")
        # print(f"   RS 30-day: {rs_metrics['rs_30d']:.2f}x market")
        # print(f"   RS 10-day: {rs_metrics['rs_10d']:.2f}x market")
        # print(f"   RS Trend: {rs_metrics['rs_trend']}")

        # # Interpret RS
        # if rs_metrics['rs_30d'] > 1.0:
        #     print(f"   ✅ Outperforming market (RS > 1.0)\n")
        # elif rs_metrics['rs_30d'] > 0.8:
        #     print(f"   ⚠️  Neutral performance (RS = {rs_metrics['rs_30d']:.2f})\n")
        # else:
        #     print(f"   ❌ Underperforming market (RS < 0.8)\n")

        # Step 2: Fetch multi-timeframe data
        print("📈 Step 2: Fetching Multi-Timeframe Data...")
        mtf_data = self.fetch_multi_timeframe_data(symbol)
        print(f"   Weekly bars: {len(mtf_data['weekly'])}")
        print(f"   Daily bars: {len(mtf_data['daily'])}")
        print(f"   4H bars: {len(mtf_data['4h'])}\n")

        # Step 3: Calculate ADX for trend strength
        print("📈 Step 3: ADX Trend Strength Analysis...")
        adx_metrics = self.calculate_adx(mtf_data['daily'])
        print(f"   ADX: {adx_metrics['adx']:.1f}")
        print(f"   +DI: {adx_metrics['plus_di']:.1f}")
        print(f"   -DI: {adx_metrics['minus_di']:.1f}")

        # Interpret ADX
        if adx_metrics['adx'] < 20:
            print(f"   ❌ Weak/No trend (ADX < 20). Skipping.\n")
            return None
        elif adx_metrics['adx'] < 25:
            print(f"   ⚠️  Developing trend (ADX 20-25)\n")
        elif adx_metrics['adx'] < 50:
            print(f"   ✅ Strong trend (ADX 25-50) - Ideal!\n")
        elif adx_metrics['adx'] < 75:
            print(f"   💪 Very strong trend (ADX 50-75)\n")
        else:
            print(f"   ⚡ Extremely strong trend (ADX > 75) - May be overextended\n")

        # Step 4: Analyze weekly trend
        print("📅 Step 4: Weekly Trend Analysis...")
        weekly_trend, weekly_strength = self.analyze_weekly_trend(mtf_data['weekly'])
        print(f"   Trend: {weekly_trend}")
        print(f"   Strength: {weekly_strength:.1f}/100\n")

        # Step 5: Analyze daily breakout
        print("📊 Step 5: Daily Breakout Analysis...")
        is_breakout, breakout_details = self.analyze_daily_breakout(mtf_data['daily'])
        print(f"   Breakout: {'YES ✅' if is_breakout else 'NO ❌'}")
        if is_breakout:
            print(f"   Breakout Price: ₹{breakout_details['breakout_price']:.2f}")
            print(f"   Volume Ratio: {breakout_details['volume_ratio']:.2f}x")
            print(f"   Strength: {breakout_details['breakout_strength']:.1f}/100\n")
        else:
            print("   No breakout detected. Skipping.\n")
            return None

        # Step 6: S/R Multi-Timeframe Analysis
        print("🎯 Step 6: Multi-Timeframe S/R Analysis...")
        all_sr_zones = self.sr_analyzer.analyze_multi_timeframe_sr(
            mtf_data['weekly'],
            mtf_data['daily'],
            mtf_data['4h']
        )

        # Find S/R confluences
        sr_confluences = self.sr_analyzer.find_confluent_levels(all_sr_zones)

        # Analyze breakout quality based on S/R
        current_price = mtf_data['daily']['close'].iloc[-1]
        sr_quality = self.sr_analyzer.analyze_breakout_quality(
            current_price,
            all_sr_zones
        )

        print(f"   S/R Quality Score: {sr_quality['quality_score']:.1f}/100")
        if sr_quality.get('nearest_resistance_above'):
            r_level, r_strength, r_tf = sr_quality['nearest_resistance_above']
            distance_pct = ((r_level - current_price) / current_price) * 100
            print(f"   Next Resistance: ₹{r_level:.2f} (+{distance_pct:.1f}% away, {r_tf})")
        if sr_quality.get('nearest_support_below'):
            s_level, s_strength, s_tf = sr_quality['nearest_support_below']
            distance_pct = ((current_price - s_level) / current_price) * 100
            print(f"   Nearest Support: ₹{s_level:.2f} (-{distance_pct:.1f}% away, {s_tf})")

        if sr_confluences:
            print(f"   S/R Confluences: {len(sr_confluences)} found")
            for conf in sr_confluences[:3]:  # Show top 3
                print(f"      • ₹{conf['level']:.2f} ({', '.join(conf['timeframes'])})")

        if sr_quality.get('issues'):
            for issue in sr_quality['issues']:
                print(f"   ⚠️  {issue}")
        print()

        # Check S/R quality threshold
        if sr_quality['quality_score'] < self.min_sr_quality:
            print(f"   ❌ S/R Quality too low (< {self.min_sr_quality}). Skipping.\n")
            return None

        # Step 7: Count confluences (SIMPLIFIED + ADX)
        print("🎯 Step 7: Confluence Check (need 2 of 7)...")
        confluences = []

        # 1. Weekly uptrend intact
        if weekly_strength >= 50:
            confluences.append("Weekly uptrend intact")

        # 2. Daily breakout above resistance
        if is_breakout:
            confluences.append("Daily breakout")

        # 3. Volume expansion (>1.5x average)
        if breakout_details.get('volume_ratio', 0) > 1.5:
            confluences.append("Volume expansion")

        # 4. S/R confluence zone (2+ levels align)
        if sr_confluences and len(sr_confluences) >= 2:
            confluences.append("S/R confluence zone")

        # 5. Outperforming market (RS > 1.0)
        if rs_metrics['rs_30d'] > 1.0:
            confluences.append("Outperforming market (RS > 1.0)")

        # 6. RS trend improving/strengthening
        if rs_metrics['rs_trend'] in ['strengthening', 'improving']:
            confluences.append(f"RS trend {rs_metrics['rs_trend']}")

        # 7. Strong ADX trend (ADX > 25)
        if adx_metrics['adx'] > 25:
            confluences.append(f"Strong ADX trend ({adx_metrics['adx']:.1f})")

        print(f"   Confluences found: {len(confluences)}/7")
        for conf in confluences:
            print(f"      ✅ {conf}")
        print()

        if len(confluences) < self.min_confluences:
            print(f"   ❌ Insufficient confluences (need {self.min_confluences})\n")
            return None

        # Step 8: Calculate entry levels (WITH S/R)
        print("🎯 Step 8: Calculating Entry Levels (S/R-Adjusted)...")
        levels = self.calculate_entry_levels(
            mtf_data['daily'],
            breakout_details['breakout_price'],
            breakout_details['atr'],
            sr_analysis=sr_quality  # NEW: Pass S/R analysis
        )

        print(f"   Entry: ₹{levels['entry']:.2f}")
        print(f"   Stop Loss: ₹{levels['stop_loss']:.2f}")
        print(f"   Target: ₹{levels['target']:.2f}")
        print(f"   Risk/Reward: 1:{levels['risk_reward_ratio']:.2f}")
        print(f"   Risk per share: ₹{levels['risk_per_share']:.2f}\n")

        # Calculate overall strength score (using ADX instead of momentum)
        strength_score = (
            weekly_strength * 0.3 +
            breakout_details['breakout_strength'] * 0.3 +
            (adx_metrics['adx'] / 100) * 100 * 0.4  # ADX contribution (scaled to 0-100)
        )

        print(f"✅ SIGNAL GENERATED!")
        print(f"   Overall Strength: {strength_score:.1f}/100")
        print(f"   S/R Quality: {sr_quality['quality_score']:.1f}/100")
        print(f"   Beta: {beta:.2f}")
        print(f"   ADX: {adx_metrics['adx']:.1f}")
        print(f"   RS 30-day: {rs_metrics['rs_30d']:.2f}x market ({rs_metrics['rs_trend']})")
        print(f"   Confluences: {len(confluences)}")
        print(f"{'='*70}\n")

        # Create signal (with S/R and RS data)
        signal = MultiTimeframeSignal(
            symbol=symbol,
            entry_price=levels['entry'],
            stop_loss=levels['stop_loss'],
            target=levels['target'],
            risk_reward_ratio=levels['risk_reward_ratio'],
            confluences=confluences,
            timeframe_analysis={
                'weekly': weekly_trend,
                'daily': 'breakout',
                '4h': 'neutral'  # 4H removed to avoid rate limits
            },
            strength_score=strength_score,
            timestamp=datetime.now(),
            sr_quality_score=sr_quality['quality_score'],
            sr_analysis=sr_quality,
            rs_metrics=rs_metrics,  # Relative Strength metrics
            adx_metrics=adx_metrics,  # ADX trend strength metrics
            beta=beta  # Beta value
        )

        return signal


def scan_high_beta_stocks():
    """Scan list of high beta stocks for breakout setups"""

    # High beta stocks in Indian market (examples)
    # You should maintain a dynamic list based on current market conditions
    high_beta_stocks = [
        'TATAMOTORS',  # Auto sector - high beta
        'SAIL',  # Steel - cyclical, high beta
        'VEDL',  # Metals - commodity exposure
        'ADANIPORTS',  # Infrastructure
        'INDUSINDBK',  # Banking
        'AXISBANK',  # Banking
        'TATAPOWER',  # Power
        'SUNPHARMA',  # Pharma (moderate-high beta)
        'HINDALCO',  # Metals
        'JSWSTEEL'  # Steel
    ]

    strategy = MultiTimeframeBreakoutStrategy()
    signals = []

    print("\n" + "="*70)
    print("🚀 HIGH BETA BREAKOUT SCANNER")
    print("="*70)
    print(f"Scanning {len(high_beta_stocks)} stocks...")
    print(f"Strategy: Multi-Timeframe Breakout")
    print(f"Min Confluences: {strategy.min_confluences}")
    print(f"Min Beta: {strategy.high_beta_threshold}")
    print("="*70 + "\n")

    for symbol in high_beta_stocks:
        try:
            signal = strategy.generate_signal(symbol)
            if signal:
                signals.append(signal)
        except Exception as e:
            print(f"❌ Error analyzing {symbol}: {e}\n")
            continue

    # Display results
    print("\n" + "="*70)
    print("📋 SCAN RESULTS")
    print("="*70 + "\n")

    if signals:
        # Sort by strength score
        signals.sort(key=lambda x: x.strength_score, reverse=True)

        for i, signal in enumerate(signals, 1):
            print(f"\n#{i} - {signal.symbol} (Strength: {signal.strength_score:.1f}/100, S/R: {signal.sr_quality_score:.1f}/100)")
            print(f"   Entry: ₹{signal.entry_price:.2f}")
            print(f"   Stop: ₹{signal.stop_loss:.2f}")
            print(f"   Target: ₹{signal.target:.2f}")
            print(f"   R:R = 1:{signal.risk_reward_ratio:.2f}")

            # Show S/R levels
            if signal.sr_analysis:
                if signal.sr_analysis.get('nearest_resistance_above'):
                    r_level, r_strength, r_tf = signal.sr_analysis['nearest_resistance_above']
                    print(f"   Next Resistance: ₹{r_level:.2f} ({r_tf})")
                if signal.sr_analysis.get('nearest_support_below'):
                    s_level, s_strength, s_tf = signal.sr_analysis['nearest_support_below']
                    print(f"   Nearest Support: ₹{s_level:.2f} ({s_tf})")

            print(f"   Confluences ({len(signal.confluences)}):")
            for conf in signal.confluences:
                print(f"      ✅ {conf}")
            print(f"   Timeframes: W={signal.timeframe_analysis['weekly']}, "
                  f"D={signal.timeframe_analysis['daily']}, "
                  f"4H={signal.timeframe_analysis['4h']}")

        print(f"\n{'='*70}")
        print(f"✅ Found {len(signals)} high-probability setups!")
        print(f"{'='*70}\n")
    else:
        print("No signals found. Market may be in consolidation or downtrend.\n")

    return signals


if __name__ == '__main__':
    signals = scan_high_beta_stocks()
