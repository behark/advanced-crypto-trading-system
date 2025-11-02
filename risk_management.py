"""
Advanced Risk Management System
Kelly Criterion, Position Sizing, Drawdown Protection, Portfolio Heat Management
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, List, Optional
from dataclasses import dataclass


@dataclass
class RiskProfile:
    """User's risk profile and account settings"""
    account_balance: float
    max_risk_per_trade: float = 0.02  # 2% risk per trade
    max_portfolio_heat: float = 0.06  # 6% total exposure
    max_drawdown: float = 0.20  # 20% max drawdown
    confidence_threshold: float = 75  # Min confidence for trade
    win_rate: float = 0.55  # Historical win rate
    avg_win_loss_ratio: float = 1.5  # Avg win / Avg loss


class RiskManager:
    """Advanced risk management calculations"""
    
    def __init__(self, risk_profile: RiskProfile):
        self.profile = risk_profile
        self.open_trades = []
        self.trade_history = []
        self.peak_balance = risk_profile.account_balance
        self.current_balance = risk_profile.account_balance
    
    def calculate_position_size(self, entry: float, stop_loss: float, 
                               confidence: float) -> Dict:
        """
        Calculate optimal position size using multiple methods
        
        Args:
            entry: Entry price
            stop_loss: Stop loss price
            confidence: Signal confidence (0-100)
        
        Returns:
            Dict with position sizing recommendations
        """
        risk_per_trade = self.profile.max_risk_per_trade
        account = self.current_balance
        
        # Calculate risk in dollars
        risk_dollars = account * risk_per_trade
        
        # Calculate risk per unit
        risk_per_unit = abs(entry - stop_loss)
        
        # Standard position size
        std_position_size = risk_dollars / risk_per_unit if risk_per_unit > 0 else 0
        
        # Kelly Criterion (adjusted)
        kelly_fraction = self._kelly_criterion()
        kelly_position_size = account * kelly_fraction / risk_per_unit if risk_per_unit > 0 else 0
        
        # Confidence-adjusted sizing
        confidence_factor = confidence / 100.0  # 0.75-0.95 range
        adjusted_position_size = std_position_size * confidence_factor
        
        # Portfolio heat check
        max_position_for_heat = self._max_position_for_heat(risk_per_unit)
        
        # Conservative (70% of max)
        conservative_size = std_position_size * 0.7
        
        # Aggressive (100% of max)
        aggressive_size = std_position_size * 1.0
        
        return {
            'standard_position_size': std_position_size,
            'kelly_position_size': kelly_position_size,
            'confidence_adjusted_size': adjusted_position_size,
            'max_position_for_heat': max_position_for_heat,
            'conservative_size': conservative_size,
            'aggressive_size': aggressive_size,
            'recommended_size': adjusted_position_size,  # Default recommendation
            'risk_dollars': risk_dollars,
            'risk_per_unit': risk_per_unit,
            'kelly_fraction': kelly_fraction,
        }
    
    def _kelly_criterion(self) -> float:
        """
        Calculate Kelly Criterion fraction
        Kelly % = (bp - q) / b
        where: b = odds, p = win prob, q = loss prob (1-p)
        
        For trading: Kelly % = (win_rate * avg_win - loss_rate * avg_loss) / avg_win
        """
        w = self.profile.win_rate
        l = 1 - w
        ratio = self.profile.avg_win_loss_ratio
        
        kelly = (w * ratio - l) / ratio
        
        # Cap at 25% to reduce volatility
        kelly = max(0, min(kelly, 0.25))
        
        # Apply safety factor (use 25% of kelly)
        kelly_safe = kelly * 0.25
        
        return kelly_safe
    
    def _max_position_for_heat(self, risk_per_unit: float) -> float:
        """Calculate max position size to respect portfolio heat limit"""
        current_heat = self._calculate_portfolio_heat()
        available_heat = self.profile.max_portfolio_heat - current_heat
        
        if available_heat <= 0:
            return 0
        
        heat_dollars = self.current_balance * available_heat
        max_size = heat_dollars / risk_per_unit if risk_per_unit > 0 else 0
        
        return max_size
    
    def validate_trade(self, entry: float, stop_loss: float, 
                      confidence: float, pair: str) -> Dict:
        """
        Validate if trade should be taken based on risk management rules
        
        Returns:
            Dict with validation result and reasons
        """
        result = {
            'approved': True,
            'reasons': [],
            'warnings': [],
            'risk_score': 0,
        }
        
        # Check 1: Confidence threshold
        if confidence < self.profile.confidence_threshold:
            result['approved'] = False
            result['reasons'].append(f"❌ Confidence {confidence}% < threshold {self.profile.confidence_threshold}%")
        else:
            result['reasons'].append(f"✅ Confidence {confidence}% > threshold")
        
        # Check 2: Portfolio heat
        current_heat = self._calculate_portfolio_heat()
        if current_heat >= self.profile.max_portfolio_heat:
            result['approved'] = False
            result['reasons'].append(f"❌ Portfolio heat {current_heat*100:.1f}% >= max {self.profile.max_portfolio_heat*100:.1f}%")
        else:
            result['reasons'].append(f"✅ Portfolio heat {current_heat*100:.1f}% < max")
        
        # Check 3: Drawdown limit
        current_dd = self._calculate_drawdown()
        if current_dd >= self.profile.max_drawdown:
            result['warnings'].append(f"⚠️  Current drawdown {current_dd*100:.1f}% approaching limit {self.profile.max_drawdown*100:.1f}%")
        
        # Check 4: Risk per unit
        risk_per_unit = abs(entry - stop_loss)
        if risk_per_unit == 0:
            result['approved'] = False
            result['reasons'].append("❌ Invalid risk (entry == stop loss)")
        else:
            result['reasons'].append(f"✅ Valid risk per unit: ${risk_per_unit:.8f}")
        
        # Calculate risk score (0-100)
        result['risk_score'] = self._calculate_trade_risk_score(
            confidence, risk_per_unit, current_heat
        )
        
        return result
    
    def _calculate_portfolio_heat(self) -> float:
        """Calculate total portfolio heat (% of account at risk)"""
        if not self.open_trades:
            return 0
        
        total_risk = sum(trade['risk_dollars'] for trade in self.open_trades)
        return total_risk / self.current_balance
    
    def _calculate_drawdown(self) -> float:
        """Calculate current drawdown from peak"""
        if self.current_balance >= self.peak_balance:
            return 0
        return (self.peak_balance - self.current_balance) / self.peak_balance
    
    def _calculate_trade_risk_score(self, confidence: float, risk_per_unit: float,
                                   portfolio_heat: float) -> int:
        """Score trade from 0-100 (higher = safer)"""
        score = 0
        
        # Confidence component (30 pts)
        conf_score = (confidence - 50) / 50 * 30  # 50-100 → 0-30
        score += max(0, min(conf_score, 30))
        
        # Risk component (40 pts)
        risk_factor = risk_per_unit / (self.current_balance * 0.01)  # Risk as % of 1% of account
        risk_score = 40 - (risk_factor * 10)  # Lower risk = higher score
        score += max(0, min(risk_score, 40))
        
        # Portfolio heat component (30 pts)
        heat_score = (1 - portfolio_heat / self.profile.max_portfolio_heat) * 30
        score += max(0, min(heat_score, 30))
        
        return int(score)
    
    def add_trade(self, pair: str, entry: float, stop_loss: float,
                 position_size: float, confidence: float) -> None:
        """Track an open trade"""
        trade = {
            'pair': pair,
            'entry': entry,
            'stop_loss': stop_loss,
            'position_size': position_size,
            'confidence': confidence,
            'risk_dollars': position_size * abs(entry - stop_loss),
            'risk_pct': (position_size * abs(entry - stop_loss)) / self.current_balance * 100,
        }
        self.open_trades.append(trade)
    
    def close_trade(self, pair: str, exit_price: float) -> Dict:
        """Close a trade and update balance"""
        trade_idx = next((i for i, t in enumerate(self.open_trades) if t['pair'] == pair), None)
        
        if trade_idx is None:
            return {'status': 'error', 'message': f'Trade {pair} not found'}
        
        trade = self.open_trades.pop(trade_idx)
        pnl = (exit_price - trade['entry']) * trade['position_size']
        pnl_pct = (pnl / (trade['entry'] * trade['position_size'])) * 100
        
        self.current_balance += pnl
        if self.current_balance > self.peak_balance:
            self.peak_balance = self.current_balance
        
        result = {
            'pair': pair,
            'entry': trade['entry'],
            'exit': exit_price,
            'position_size': trade['position_size'],
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'balance': self.current_balance,
        }
        
        self.trade_history.append(result)
        return result
    
    def get_risk_report(self) -> Dict:
        """Generate comprehensive risk report"""
        current_heat = self._calculate_portfolio_heat()
        current_dd = self._calculate_drawdown()
        
        return {
            'account_balance': self.current_balance,
            'peak_balance': self.peak_balance,
            'current_drawdown': current_dd,
            'portfolio_heat': current_heat,
            'open_trades_count': len(self.open_trades),
            'max_heat_available': self.profile.max_portfolio_heat - current_heat,
            'trades_closed': len(self.trade_history),
            'kelly_fraction': self._kelly_criterion(),
            'status': 'Healthy' if current_heat < self.profile.max_portfolio_heat * 0.8 else 'High Heat',
        }


class SignalOptimizer:
    """Optimize signal accuracy through multi-timeframe confirmation and weighting"""
    
    def __init__(self):
        self.indicator_weights = {
            'sbst': 0.20,          # 20% - Primary trend
            'halftrend': 0.12,     # 12% - Support/resistance
            'psar': 0.10,          # 10% - Reversals
            'swift_algo': 0.15,    # 15% - Momentum
            'chandelier': 0.08,    # 8% - Exits
            'nrtr': 0.10,          # 10% - Trailing reversal
            'smc': 0.12,           # 12% - Structure
            'rsi': 0.05,           # 5% - Extremes
            'macd': 0.05,          # 5% - Histogram
            'adx': 0.03,           # 3% - Trend strength
        }
    
    def calculate_weighted_confidence(self, indicators: Dict) -> float:
        """
        Calculate confidence using weighted indicator scoring
        
        Args:
            indicators: Dict with indicator signals/values
            
        Returns:
            Weighted confidence score (0-100)
        """
        score = 0
        
        # SBST (20%)
        sbst_score = (indicators.get('sbst_trend_aligned', 0) * 15 +
                     indicators.get('sbst_buy_signal', 0) * 5)
        score += sbst_score * self.indicator_weights['sbst']
        
        # HalfTrend (12%)
        ht_score = (indicators.get('halftrend_trend_match', 0) * 10 +
                   indicators.get('halftrend_signal', 0) * 2)
        score += ht_score * self.indicator_weights['halftrend']
        
        # Parabolic SAR (10%)
        psar_score = (indicators.get('psar_trend_match', 0) * 10)
        score += psar_score * self.indicator_weights['psar']
        
        # Swift Algo (15%)
        swift_score = (indicators.get('swift_strong', 0) * 15)
        score += swift_score * self.indicator_weights['swift_algo']
        
        # Chandelier (8%)
        ce_score = indicators.get('chandelier_signal', 0) * 8
        score += ce_score * self.indicator_weights['chandelier']
        
        # NRTR (10%)
        nrtr_score = (indicators.get('nrtr_trend_match', 0) * 10)
        score += nrtr_score * self.indicator_weights['nrtr']
        
        # SMC (12%)
        smc_score = (indicators.get('smc_setup', 0) * 12)
        score += smc_score * self.indicator_weights['smc']
        
        # RSI (5%)
        rsi_score = indicators.get('rsi_extreme', 0) * 5
        score += rsi_score * self.indicator_weights['rsi']
        
        # MACD (5%)
        macd_score = indicators.get('macd_bullish', 0) * 5
        score += macd_score * self.indicator_weights['macd']
        
        # ADX (3%)
        adx_score = indicators.get('adx_strong', 0) * 3
        score += adx_score * self.indicator_weights['adx']
        
        return min(100, max(0, score))
    
    def detect_divergences(self, indicators: Dict) -> List[Dict]:
        """
        Detect when indicators diverge (potential false signal)
        
        Returns:
            List of divergences found
        """
        divergences = []
        
        # Price making new high but momentum (RSI/MACD) not confirming
        if indicators.get('price_new_high') and not indicators.get('rsi_high'):
            divergences.append({
                'type': 'Bearish Divergence',
                'severity': 'High',
                'description': 'Price new high but RSI not confirming',
            })
        
        # SBST and SMC conflicting on trend
        if indicators.get('sbst_uptrend') != indicators.get('smc_uptrend'):
            divergences.append({
                'type': 'Structure Divergence',
                'severity': 'Medium',
                'description': 'SBST and SMC disagreeing on trend direction',
            })
        
        # Multiple indicators suggesting reversal
        reversal_count = sum([
            indicators.get('halftrend_reversal', 0),
            indicators.get('psar_reversal', 0),
            indicators.get('nrtr_reversal', 0),
        ])
        
        if reversal_count >= 2:
            divergences.append({
                'type': 'Multi-Reversal Signal',
                'severity': 'High',
                'description': f'{reversal_count} indicators signaling reversal',
            })
        
        return divergences
    
    def require_multi_timeframe_confirmation(self, signal: Dict,
                                            tf_5m: Dict, tf_15m: Dict,
                                            tf_1h: Dict) -> Dict:
        """
        Validate signal across multiple timeframes
        
        Returns:
            Validation result with strength score
        """
        result = {
            'approved': False,
            'strength': 0,
            'confirmations': 0,
            'timeframes_aligned': [],
            'reasoning': [],
        }
        
        # 5m signal direction
        signal_direction = 'buy' if signal['action'] == 'BUY' else 'sell'
        
        # Check 15m alignment
        if (signal_direction == 'buy' and tf_15m.get('trend') == 'UPTREND') or \
           (signal_direction == 'sell' and tf_15m.get('trend') == 'DOWNTREND'):
            result['confirmations'] += 1
            result['timeframes_aligned'].append('15m')
            result['reasoning'].append('✅ 15m confirms direction')
        else:
            result['reasoning'].append('⚠️  15m does not confirm')
        
        # Check 1h alignment
        if (signal_direction == 'buy' and tf_1h.get('trend') == 'UPTREND') or \
           (signal_direction == 'sell' and tf_1h.get('trend') == 'DOWNTREND'):
            result['confirmations'] += 1
            result['timeframes_aligned'].append('1h')
            result['reasoning'].append('✅ 1h confirms direction')
        else:
            result['reasoning'].append('⚠️  1h does not confirm')
        
        # Check 4h (already in Swift Algo HTF)
        if tf_1h.get('htf_bullish') == (signal_direction == 'buy'):
            result['confirmations'] += 1
            result['timeframes_aligned'].append('4h')
            result['reasoning'].append('✅ 4h HTF confirms (Swift Algo)')
        
        # Decision logic
        result['strength'] = (result['confirmations'] / 3) * 100  # 0-100
        result['approved'] = result['confirmations'] >= 2  # Need at least 2 TF confirmations
        
        return result
