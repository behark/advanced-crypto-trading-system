#!/usr/bin/env python3
"""
Automated Trade Tracker
Logs all signals, entries, exits, and calculates statistics
"""

import json
import csv
from datetime import datetime
from pathlib import Path


class TradeTracker:
    """Track all trades and signals for accuracy analysis"""
    
    def __init__(self, log_file="trade_log.json"):
        self.log_file = log_file
        self.trades = self._load_trades()
    
    def _load_trades(self):
        """Load existing trades from log file"""
        if Path(self.log_file).exists():
            with open(self.log_file, 'r') as f:
                return json.load(f)
        return []
    
    def _save_trades(self):
        """Save trades to log file"""
        with open(self.log_file, 'w') as f:
            json.dump(self.trades, f, indent=2, default=str)
    
    def log_signal(self, signal_data):
        """Log a new signal"""
        trade = {
            'id': len(self.trades) + 1,
            'timestamp': datetime.now().isoformat(),
            'symbol': signal_data.get('symbol', 'UNKNOWN'),
            'timeframe': signal_data.get('timeframe', '5m'),
            'signal': signal_data.get('action', 'WAIT'),
            'entry_price': signal_data.get('entry'),
            'stop_loss': signal_data.get('stop_loss'),
            'tp1': signal_data.get('take_profit_1'),
            'tp2': signal_data.get('take_profit_2'),
            'base_confidence': signal_data.get('confidence', 0),
            'weighted_confidence': signal_data.get('weighted_confidence', 0),
            'multi_tf_confirmed': signal_data.get('multi_tf_confirmed', False),
            'divergences': signal_data.get('divergences_count', 0),
            'risk_reward': signal_data.get('risk_reward', 0),
            'channel': signal_data.get('channel', 'local'),
            'country': signal_data.get('country', 'Global'),
            'status': 'OPEN',
            'exit_price': None,
            'exit_time': None,
            'pnl': None,
            'pnl_pct': None,
            'exit_reason': None,
        }
        
        self.trades.append(trade)
        self._save_trades()
        
        return trade['id']
    
    def close_trade(self, trade_id, exit_price, exit_reason="MANUAL"):
        """Close an open trade"""
        for trade in self.trades:
            if trade['id'] == trade_id:
                trade['exit_price'] = exit_price
                trade['exit_time'] = datetime.now().isoformat()
                trade['status'] = 'CLOSED'
                trade['exit_reason'] = exit_reason
                
                # Calculate P&L
                if trade['signal'] == 'BUY':
                    pnl = exit_price - trade['entry_price']
                else:  # SELL
                    pnl = trade['entry_price'] - exit_price
                
                trade['pnl'] = pnl
                trade['pnl_pct'] = (pnl / trade['entry_price']) * 100
                
                self._save_trades()
                return trade
        
        return None
    
    def get_stats(self):
        """Calculate trading statistics"""
        closed_trades = [t for t in self.trades if t['status'] == 'CLOSED']
        
        if not closed_trades:
            return {
                'total_trades': 0,
                'wins': 0,
                'losses': 0,
                'win_rate': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'win_loss_ratio': 0,
                'total_pnl': 0,
                'avg_pnl_pct': 0,
                'best_trade': None,
                'worst_trade': None,
            }
        
        wins = [t for t in closed_trades if t['pnl'] > 0]
        losses = [t for t in closed_trades if t['pnl'] < 0]
        
        win_rate = (len(wins) / len(closed_trades)) * 100
        avg_win = sum(t['pnl'] for t in wins) / len(wins) if wins else 0
        avg_loss = sum(abs(t['pnl']) for t in losses) / len(losses) if losses else 0
        total_pnl = sum(t['pnl'] for t in closed_trades)
        avg_pnl_pct = sum(t['pnl_pct'] for t in closed_trades) / len(closed_trades)
        
        return {
            'total_trades': len(closed_trades),
            'wins': len(wins),
            'losses': len(losses),
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'win_loss_ratio': avg_win / avg_loss if avg_loss > 0 else 0,
            'total_pnl': total_pnl,
            'avg_pnl_pct': avg_pnl_pct,
            'best_trade': max(closed_trades, key=lambda t: t['pnl']) if closed_trades else None,
            'worst_trade': min(closed_trades, key=lambda t: t['pnl']) if closed_trades else None,
        }
    
    def export_csv(self, filename="trades.csv"):
        """Export trades to CSV"""
        if not self.trades:
            return
        
        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.trades[0].keys())
            writer.writeheader()
            writer.writerows(self.trades)
    
    def print_stats(self):
        """Print trading statistics"""
        stats = self.get_stats()
        
        print(f"\n{'='*80}")
        print("TRADING STATISTICS")
        print(f"{'='*80}\n")
        
        print(f"Total Trades: {stats['total_trades']}")
        print(f"Wins: {stats.get('wins', 0)} | Losses: {stats.get('losses', 0)}")
        print(f"Win Rate: {stats['win_rate']:.1f}%\n")
        
        print(f"Average Win: ${stats['avg_win']:.4f}")
        print(f"Average Loss: ${stats['avg_loss']:.4f}")
        print(f"Win/Loss Ratio: {stats['win_loss_ratio']:.2f}\n")
        
        print(f"Total P&L: ${stats['total_pnl']:.4f}")
        print(f"Average P&L: {stats['avg_pnl_pct']:.2f}%\n")
        
        if stats['best_trade']:
            print(f"Best Trade: {stats['best_trade']['symbol']} +{stats['best_trade']['pnl_pct']:.2f}%")
        if stats['worst_trade']:
            print(f"Worst Trade: {stats['worst_trade']['symbol']} {stats['worst_trade']['pnl_pct']:.2f}%")
        
        print(f"\n{'='*80}\n")
    
    def print_open_trades(self):
        """Print all open trades"""
        open_trades = [t for t in self.trades if t['status'] == 'OPEN']
        
        if not open_trades:
            print("No open trades")
            return
        
        def _fmt(val, fmt="{:.8f}"):
            if val is None:
                return "N/A"
            try:
                return fmt.format(val)
            except Exception:
                return str(val)
        
        print(f"\n{'='*80}")
        print("OPEN TRADES")
        print(f"{'='*80}\n")
        
        for trade in open_trades:
            print(f"Trade #{trade['id']}: {trade.get('symbol', 'UNKNOWN')} {trade.get('signal', 'WAIT')}")
            print(f"  Entry: ${_fmt(trade.get('entry_price'))} @ {trade.get('timestamp', '')}")
            print(f"  Stop: ${_fmt(trade.get('stop_loss'))}")
            print(f"  TP1: ${_fmt(trade.get('tp1'))}")
            print(f"  TP2: ${_fmt(trade.get('tp2'))}")
            base_conf = trade.get('base_confidence')
            w_conf = trade.get('weighted_confidence')
            bc = f"{base_conf}%" if base_conf is not None else "N/A"
            wc = f"{w_conf:.1f}%" if isinstance(w_conf, (int, float)) else "N/A"
            print(f"  Confidence: {bc} (Weighted: {wc})")
            print()


def main():
    """Example usage"""
    tracker = TradeTracker()
    
    # Example: Log a signal
    signal_data = {
        'symbol': 'BTC/USDT',
        'timeframe': '5m',
        'action': 'BUY',
        'entry': 42000,
        'stop_loss': 41500,
        'take_profit_1': 42500,
        'take_profit_2': 43000,
        'confidence': 85,
        'weighted_confidence': 78.5,
        'multi_tf_confirmed': True,
        'divergences_count': 0,
        'risk_reward': 2.0,
    }
    
    trade_id = tracker.log_signal(signal_data)
    print(f"✅ Signal logged: Trade #{trade_id}")
    
    # Print open trades
    tracker.print_open_trades()
    
    # Print statistics
    tracker.print_stats()
    
    # Export to CSV
    tracker.export_csv()
    print("✅ Exported to trades.csv")


if __name__ == "__main__":
    main()
