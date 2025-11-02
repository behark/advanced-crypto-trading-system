"""
Smart Money Concepts (SMC) System
Converts TradingView Pine Script SMC strategy to Python
Detects: Order Blocks, Fair Value Gaps, Liquidity Zones, Market Structure
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, List, Optional

class SMCSystem:
    """Smart Money Concepts indicator system"""
    
    def __init__(self, ob_lookback: int = 14, vol_multiplier: float = 2.0, 
                 displacement_pct: float = 0.5, fvg_min_gap_pct: float = 0.5,
                 liq_tolerance: float = 1.0, atr_period: int = 14):
        """
        Initialize SMC System
        
        Args:
            ob_lookback: Order Block lookback period
            vol_multiplier: Volume spike multiplier
            displacement_pct: Displacement percentage threshold
            fvg_min_gap_pct: Fair Value Gap minimum gap percentage
            liq_tolerance: Liquidity tolerance percentage
            atr_period: ATR period for stop loss calculation
        """
        self.ob_lookback = ob_lookback
        self.vol_multiplier = vol_multiplier
        self.displacement_pct = displacement_pct
        self.fvg_min_gap_pct = fvg_min_gap_pct
        self.liq_tolerance = liq_tolerance
        self.atr_period = atr_period
        
        self.bullish_ob = {'price': None, 'tested': False}
        self.bearish_ob = {'price': None, 'tested': False}
        self.bullish_fvg = {'top': None, 'bottom': None, 'filled': False}
        self.bearish_fvg = {'top': None, 'bottom': None, 'filled': False}
        self.trend = 'bullish'
        self.choch_signal = None
    
    def calculate(self, df: pd.DataFrame) -> Dict:
        """
        Calculate SMC signals
        
        Args:
            df: DataFrame with OHLCV data (open, high, low, close, volume)
            
        Returns:
            Dict with SMC analysis
        """
        if len(df) < max(self.ob_lookback, self.atr_period, 20):
            return self._empty_result()
        
        # Calculate market structure
        bos_lookback = 20
        # Handle both lowercase and uppercase column names
        high_col = 'High' if 'High' in df.columns else 'high'
        low_col = 'Low' if 'Low' in df.columns else 'low'
        close_col = 'Close' if 'Close' in df.columns else 'close'
        open_col = 'Open' if 'Open' in df.columns else 'open'
        vol_col = 'Volume' if 'Volume' in df.columns else 'volume'
        
        highest_high = df[high_col].rolling(window=bos_lookback).max()
        lowest_low = df[low_col].rolling(window=bos_lookback).min()
        
        bos_bullish = df[close_col] > highest_high.shift(1)
        bos_bearish = df[close_col] < lowest_low.shift(1)
        
        # Detect trend and CHoCH (Change of Character)
        current_trend = self._detect_trend(bos_bullish, bos_bearish)
        choch_bullish, choch_bearish = self._detect_choch(current_trend)
        
        # Calculate volume analysis
        vol_ma = df[vol_col].rolling(window=20).mean()
        vol_spike = df[vol_col] > vol_ma * self.vol_multiplier
        displacement = ((df[close_col] - df[close_col].shift(3)) / df[close_col].shift(3) * 100)
        
        # Detect Order Blocks
        bull_ob, bull_ob_price = self._detect_bullish_ob(df, vol_spike, displacement, high_col, low_col, close_col, open_col)
        bear_ob, bear_ob_price = self._detect_bearish_ob(df, vol_spike, displacement, high_col, low_col, close_col, open_col)
        
        # Detect Fair Value Gaps
        bull_fvg, bull_fvg_price = self._detect_bullish_fvg(df, high_col, low_col)
        bear_fvg, bear_fvg_price = self._detect_bearish_fvg(df, high_col, low_col)
        
        # Detect Liquidity Zones
        equal_highs = (np.abs(df[high_col] - df[high_col].shift(1)) / df[high_col] * 100) < self.liq_tolerance
        equal_lows = (np.abs(df[low_col] - df[low_col].shift(1)) / df[low_col] * 100) < self.liq_tolerance
        
        liq_sweep_bull = equal_lows.iloc[-1]
        liq_sweep_bear = equal_highs.iloc[-1]
        
        # Detect confirmation candles
        bullish_engulf = self._bullish_engulf(df, close_col, open_col)
        bearish_engulf = self._bearish_engulf(df, close_col, open_col)
        hammer = self._hammer(df, high_col, low_col, close_col, open_col)
        shooting_star = self._shooting_star(df, high_col, low_col, close_col, open_col)
        
        confirmation_bull = bullish_engulf or hammer
        confirmation_bear = bearish_engulf or shooting_star
        
        # Calculate ATR
        atr = self._calculate_atr(df, self.atr_period)
        
        # Long Setup
        long_setup = (current_trend == 'bullish' and 
                     bull_ob and 
                     (bull_fvg or True) and
                     (liq_sweep_bull or True) and
                     confirmation_bull)
        
        # Short Setup
        short_setup = (current_trend == 'bearish' and 
                      bear_ob and 
                      (bear_fvg or True) and
                      (liq_sweep_bear or True) and
                      confirmation_bear)
        
        return {
            'trend': current_trend,
            'choch_bullish': choch_bullish,
            'choch_bearish': choch_bearish,
            'bullish_ob': bull_ob,
            'bullish_ob_price': bull_ob_price,
            'bearish_ob': bear_ob,
            'bearish_ob_price': bear_ob_price,
            'bullish_fvg': bull_fvg,
            'bullish_fvg_price': bull_fvg_price,
            'bearish_fvg': bear_fvg,
            'bearish_fvg_price': bear_fvg_price,
            'liq_sweep_bull': liq_sweep_bull,
            'liq_sweep_bear': liq_sweep_bear,
            'confirmation_bull': confirmation_bull,
            'confirmation_bear': confirmation_bear,
            'long_setup': long_setup,
            'short_setup': short_setup,
            'atr': atr,
        }
    
    def _detect_trend(self, bos_bullish: pd.Series, bos_bearish: pd.Series) -> str:
        """Detect current trend based on break of structure"""
        if bos_bullish.iloc[-1]:
            self.trend = 'bullish'
        elif bos_bearish.iloc[-1]:
            self.trend = 'bearish'
        return self.trend
    
    def _detect_choch(self, trend: str) -> Tuple[bool, bool]:
        """Detect Change of Character"""
        current_choch = trend != self.trend
        choch_bull = current_choch and trend == 'bullish'
        choch_bear = current_choch and trend == 'bearish'
        self.trend = trend
        return choch_bull, choch_bear
    
    def _detect_bullish_ob(self, df: pd.DataFrame, vol_spike: pd.Series, 
                          displacement: pd.Series, high_col: str, low_col: str,
                          close_col: str, open_col: str) -> Tuple[bool, Optional[float]]:
        """Detect bullish order block"""
        idx = len(df) - 1 - self.ob_lookback
        if idx < 0:
            return False, None
        
        candle = df.iloc[idx]
        if candle[close_col] < candle[open_col] and vol_spike.iloc[idx] and displacement.iloc[idx] > self.displacement_pct:
            ob_top = candle[high_col]
            ob_bottom = candle[low_col]
            
            # Check if price tested the OB
            current_low = df[low_col].iloc[-1]
            if current_low <= ob_top:
                self.bullish_ob = {'price': (ob_bottom, ob_top), 'tested': True}
                return True, ob_top
        
        return False, None
    
    def _detect_bearish_ob(self, df: pd.DataFrame, vol_spike: pd.Series, 
                          displacement: pd.Series, high_col: str, low_col: str,
                          close_col: str, open_col: str) -> Tuple[bool, Optional[float]]:
        """Detect bearish order block"""
        idx = len(df) - 1 - self.ob_lookback
        if idx < 0:
            return False, None
        
        candle = df.iloc[idx]
        if candle[close_col] > candle[open_col] and vol_spike.iloc[idx] and displacement.iloc[idx] < -self.displacement_pct:
            ob_top = candle[high_col]
            ob_bottom = candle[low_col]
            
            # Check if price tested the OB
            current_high = df[high_col].iloc[-1]
            if current_high >= ob_bottom:
                self.bearish_ob = {'price': (ob_bottom, ob_top), 'tested': True}
                return True, ob_bottom
        
        return False, None
    
    def _detect_bullish_fvg(self, df: pd.DataFrame, high_col: str, low_col: str) -> Tuple[bool, Optional[Tuple[float, float]]]:
        """Detect bullish Fair Value Gap"""
        if len(df) < 3:
            return False, None
        
        # FVG: Gap between candle[2].high and candle[0].low
        gap_low = df[low_col].iloc[-1]
        gap_high = df[high_col].iloc[-3]
        
        if gap_low > gap_high:
            gap_pct = ((gap_low - gap_high) / gap_high * 100)
            if gap_pct >= self.fvg_min_gap_pct:
                self.bullish_fvg = {'top': gap_low, 'bottom': gap_high, 'filled': False}
                return True, (gap_high, gap_low)
        
        return False, None
    
    def _detect_bearish_fvg(self, df: pd.DataFrame, high_col: str, low_col: str) -> Tuple[bool, Optional[Tuple[float, float]]]:
        """Detect bearish Fair Value Gap"""
        if len(df) < 3:
            return False, None
        
        gap_high = df[high_col].iloc[-1]
        gap_low = df[low_col].iloc[-3]
        
        if gap_high < gap_low:
            gap_pct = ((gap_low - gap_high) / gap_low * 100)
            if gap_pct >= self.fvg_min_gap_pct:
                self.bearish_fvg = {'top': gap_low, 'bottom': gap_high, 'filled': False}
                return True, (gap_high, gap_low)
        
        return False, None
    
    def _bullish_engulf(self, df: pd.DataFrame, close_col: str, open_col: str) -> bool:
        """Detect bullish engulfing candle"""
        if len(df) < 2:
            return False
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        return (curr[close_col] > curr[open_col] and 
                prev[close_col] < prev[open_col] and
                curr[close_col] > prev[open_col] and 
                curr[open_col] < prev[close_col])
    
    def _bearish_engulf(self, df: pd.DataFrame, close_col: str, open_col: str) -> bool:
        """Detect bearish engulfing candle"""
        if len(df) < 2:
            return False
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        return (curr[close_col] < curr[open_col] and 
                prev[close_col] > prev[open_col] and
                curr[close_col] < prev[open_col] and 
                curr[open_col] > prev[close_col])
    
    def _hammer(self, df: pd.DataFrame, high_col: str, low_col: str, close_col: str, open_col: str) -> bool:
        """Detect hammer candle"""
        if len(df) < 1:
            return False
        candle = df.iloc[-1]
        body = candle[close_col] - candle[open_col]
        upper_wick = candle[high_col] - max(candle[close_col], candle[open_col])
        lower_wick = min(candle[close_col], candle[open_col]) - candle[low_col]
        
        return (candle[close_col] > candle[open_col] and 
                upper_wick < body * 0.3 and 
                lower_wick > body * 2)
    
    def _shooting_star(self, df: pd.DataFrame, high_col: str, low_col: str, close_col: str, open_col: str) -> bool:
        """Detect shooting star candle"""
        if len(df) < 1:
            return False
        candle = df.iloc[-1]
        body = candle[open_col] - candle[close_col]
        upper_wick = candle[high_col] - max(candle[close_col], candle[open_col])
        lower_wick = min(candle[close_col], candle[open_col]) - candle[low_col]
        
        return (candle[close_col] < candle[open_col] and 
                lower_wick < body * 0.3 and 
                upper_wick > body * 2)
    
    def _calculate_atr(self, df: pd.DataFrame, period: int) -> float:
        """Calculate Average True Range"""
        high_col = 'High' if 'High' in df.columns else 'high'
        low_col = 'Low' if 'Low' in df.columns else 'low'
        close_col = 'Close' if 'Close' in df.columns else 'close'
        
        tr = pd.concat([
            df[high_col] - df[low_col],
            (df[high_col] - df[close_col].shift()).abs(),
            (df[low_col] - df[close_col].shift()).abs()
        ], axis=1).max(axis=1)
        return tr.rolling(window=period).mean().iloc[-1]
    
    def _empty_result(self) -> Dict:
        """Return empty SMC result"""
        return {
            'trend': 'unknown',
            'choch_bullish': False,
            'choch_bearish': False,
            'bullish_ob': False,
            'bullish_ob_price': None,
            'bearish_ob': False,
            'bearish_ob_price': None,
            'bullish_fvg': False,
            'bullish_fvg_price': None,
            'bearish_fvg': False,
            'bearish_fvg_price': None,
            'liq_sweep_bull': False,
            'liq_sweep_bear': False,
            'confirmation_bull': False,
            'confirmation_bear': False,
            'long_setup': False,
            'short_setup': False,
            'atr': 0,
        }
