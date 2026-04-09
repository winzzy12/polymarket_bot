cat > risk_manager.py << 'EOF'
"""
Modul manajemen risiko
"""

from typing import Dict
from logger import trading_logger

class RiskManager:
    def __init__(self, config):
        self.config = config
        self.starting_balance = None
        self.current_balance = None
        self.peak_balance = None
        self.drawdown = 0.0
        self.daily_pnl = 0.0
        self.total_trades = 0
        self.winning_trades = 0
        
    def initialize_balance(self, balance: float):
        """Inisialisasi saldo awal"""
        self.starting_balance = balance
        self.current_balance = balance
        self.peak_balance = balance
        trading_logger.success(f"Risk Manager siap dengan saldo: ${balance:,.2f}")
        
    def update_balance(self, new_balance: float):
        """Update saldo terkini"""
        self.current_balance = new_balance
        
        if new_balance > self.peak_balance:
            self.peak_balance = new_balance
            
        if self.peak_balance > 0:
            self.drawdown = (self.peak_balance - new_balance) / self.peak_balance
            
    def check_daily_limits(self) -> tuple:
        """Cek batasan harian"""
        if self.starting_balance:
            daily_loss_pct = (self.starting_balance - self.current_balance) / self.starting_balance
            
            if daily_loss_pct >= self.config.DAILY_STOP_LOSS_PERCENT:
                return False, f"Daily stop loss tercapai: {daily_loss_pct:.1%}"
                
        if self.drawdown >= 0.15:
            return False, f"Max drawdown tercapai: {self.drawdown:.1%}"
            
        return True, "OK"
        
    def record_trade_result(self, pnl: float, is_win: bool = None):
        """Catat hasil trade"""
        self.total_trades += 1
        self.daily_pnl += pnl
        
        if is_win or (is_win is None and pnl > 0):
            self.winning_trades += 1
            
    def get_win_rate(self) -> float:
        """Dapatkan win rate"""
        if self.total_trades == 0:
            return 0.0
        return self.winning_trades / self.total_trades
        
    def get_risk_metrics(self) -> Dict:
        """Dapatkan metrik risiko"""
        return {
            'starting_balance': self.starting_balance,
            'current_balance': self.current_balance,
            'peak_balance': self.peak_balance,
            'drawdown': self.drawdown,
            'daily_pnl': self.daily_pnl,
            'total_trades': self.total_trades,
            'win_rate': self.get_win_rate(),
            'is_dry_run': self.config.DRY_RUN_MODE
        }
        
    def calculate_kelly_fraction(self, win_probability: float, avg_win_loss_ratio: float) -> float:
        """Hitung Kelly Criterion untuk position sizing optimal"""
        if win_probability <= 0 or avg_win_loss_ratio <= 0:
            return 0.0
            
        # f* = (p * b - q) / b
        # p = win probability, q = loss probability, b = win/loss ratio
        kelly = (win_probability * avg_win_loss_ratio - (1 - win_probability)) / avg_win_loss_ratio
        
        # Conservative Kelly (gunakan 25% dari Kelly)
        conservative = max(0, min(0.25, kelly * 0.25))
        
        return conservative
EOF
