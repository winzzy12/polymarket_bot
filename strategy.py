cat > strategy.py << 'EOF'
"""
Modul strategi trading dan risk management
"""

from datetime import datetime, timedelta
from collections import deque
from typing import Dict, Tuple
from logger import trading_logger

class TradingStrategy:
    def __init__(self, config):
        self.config = config
        self.trade_history = deque(maxlen=100)
        self.hourly_trades = deque(maxlen=config.MAX_TRADES_PER_HOUR)
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.consecutive_losses = 0
        self.cooldown_until = None
        self.daily_reset_time = datetime.now().date()
        
    def _check_daily_reset(self):
        """Reset counter harian jika perlu"""
        today = datetime.now().date()
        if today != self.daily_reset_time:
            trading_logger.info("--- Reset counter harian ---")
            self.daily_pnl = 0.0
            self.daily_trades = 0
            self.daily_reset_time = today
            
    def _check_cooldown(self) -> Tuple[bool, str]:
        """Cek apakah dalam masa cooldown"""
        if self.cooldown_until and datetime.now() < self.cooldown_until:
            remaining = (self.cooldown_until - datetime.now()).seconds // 60
            return False, f"Cooldown {remaining} menit tersisa"
        return True, "OK"
        
    def _check_hourly_limit(self) -> Tuple[bool, str]:
        """Cek batasan trade per jam"""
        now = datetime.now()
        cutoff = now - timedelta(hours=1)
        
        # Bersihkan trade lama
        self.hourly_trades = deque(
            [t for t in self.hourly_trades if t.get('timestamp', datetime.min) > cutoff],
            maxlen=self.config.MAX_TRADES_PER_HOUR
        )
        
        if len(self.hourly_trades) >= self.config.MAX_TRADES_PER_HOUR:
            return False, f"Melebihi {self.config.MAX_TRADES_PER_HOUR} trade/jam"
        return True, "OK"
        
    def _check_daily_limits(self) -> Tuple[bool, str]:
        """Cek batasan harian"""
        self._check_daily_reset()
        
        # Stop loss harian
        if self.daily_pnl <= -self.config.DAILY_STOP_LOSS_PERCENT * 10000:
            return False, f"Daily stop loss reached: ${self.daily_pnl:.2f}"
            
        # Profit target tercapai (tetap lanjut tapi hati-hati)
        if self.daily_pnl >= self.config.DAILY_PROFIT_TARGET_PERCENT * 10000:
            trading_logger.warning(f"Daily profit target tercapai: ${self.daily_pnl:.2f}")
            
        return True, "OK"
        
    def _check_consecutive_losses(self) -> Tuple[bool, str]:
        """Cek kerugian beruntun"""
        if self.consecutive_losses >= 3:
            return False, f"{self.consecutive_losses} kerugian beruntun"
        return True, "OK"
        
    def calculate_position_size(self, balance: float, confidence: float) -> float:
        """Hitung ukuran posisi berdasarkan confidence"""
        if confidence < self.config.CONFIDENCE_THRESHOLD_SKIP:
            return 0.0
            
        # Pilih persentase berdasarkan confidence
        if confidence > self.config.CONFIDENCE_THRESHOLD_HIGH:
            size_pct = self.config.HIGH_CONFIDENCE_TRADE_SIZE
        else:
            size_pct = self.config.DEFAULT_TRADE_SIZE_PERCENT
            
        position_size = balance * size_pct
        
        # Batasi maksimum
        position_size = min(position_size, self.config.MAX_POSITION_SIZE_USDC)
        
        return position_size
        
    def apply_safety_filters(self, btc_data: Dict, market_data: Dict) -> Tuple[bool, str]:
        """Terapkan filter keamanan"""
        # Cek volatilitas
        volatility = btc_data.get('volatility', 0)
        if volatility > self.config.MAX_VOLATILITY_THRESHOLD * 100:
            return False, f"Volatilitas terlalu tinggi: {volatility:.1f}%"
            
        # Cek spread
        spread = market_data.get('spread', 0)
        if spread > self.config.MAX_SPREAD_PERCENT:
            return False, f"Spread terlalu lebar: {spread:.3f}"
            
        # Cek likuiditas
        liquidity = market_data.get('liquidity', 0)
        if liquidity < self.config.MIN_LIQUIDITY_USDC:
            return False, f"Likuiditas rendah: ${liquidity:,.0f}"
            
        # Cek RSI extreme
        rsi = btc_data.get('rsi', 50)
        if rsi > 85:
            return False, f"RSI overbought ekstrem: {rsi}"
        if rsi < 15:
            return False, f"RSI oversold ekstrem: {rsi}"
            
        return True, "OK"
        
    def should_trade(self, ai_decision: Dict, btc_data: Dict, 
                     market_data: Dict, balance: float) -> Tuple[bool, str, float]:
        """Putuskan apakah harus trade"""
        
        # Cek cooldown
        ok, reason = self._check_cooldown()
        if not ok:
            return False, reason, 0.0
            
        # Cek batasan harian
        ok, reason = self._check_daily_limits()
        if not ok:
            return False, reason, 0.0
            
        # Cek batasan per jam
        ok, reason = self._check_hourly_limit()
        if not ok:
            return False, reason, 0.0
            
        # Cek kerugian beruntun
        ok, reason = self._check_consecutive_losses()
        if not ok:
            return False, reason, 0.0
            
        # Cek keputusan AI
        if ai_decision.get('decision') == 'SKIP':
            return False, f"AI skip: {ai_decision.get('reason', 'No reason')}", 0.0
            
        # Cek confidence AI
        confidence = ai_decision.get('confidence', 0)
        if confidence < self.config.CONFIDENCE_THRESHOLD_SKIP:
            return False, f"Confidence terlalu rendah: {confidence:.1%}", 0.0
            
        # Terapkan safety filters
        ok, reason = self.apply_safety_filters(btc_data, market_data)
        if not ok:
            return False, reason, 0.0
            
        # Hitung posisi size
        position_size = self.calculate_position_size(balance, confidence)
        if position_size < 10:
            return False, f"Posisi terlalu kecil: ${position_size:.2f}", 0.0
            
        # Value check (apakah ada edge)
        yes_price = market_data.get('yes_price', 0.5)
        if ai_decision['decision'] == 'BUY_YES':
            expected_prob = confidence
            if expected_prob < yes_price + 0.03:
                return False, f"Tidak ada edge: expected {expected_prob:.1%} vs market {yes_price:.1%}", 0.0
        elif ai_decision['decision'] == 'BUY_NO':
            no_price = market_data.get('no_price', 0.5)
            expected_prob = 1 - confidence
            if expected_prob < no_price + 0.03:
                return False, f"Tidak ada edge: expected {expected_prob:.1%} vs market {no_price:.1%}", 0.0
                
        return True, "Semua pemeriksaan OK", position_size
        
    def update_after_trade(self, trade_result: Dict):
        """Update status setelah trade"""
        self.trade_history.append(trade_result)
        self.hourly_trades.append({
            'timestamp': datetime.now(),
            'result': trade_result
        })
        self.daily_trades += 1
        
        pnl = trade_result.get('pnl', 0)
        self.daily_pnl += pnl
        
        if pnl < 0:
            self.consecutive_losses += 1
            if self.consecutive_losses >= 2:
                self.set_cooldown()
        else:
            self.consecutive_losses = 0
            
        trading_logger.log_pnl(pnl, self.daily_pnl)
        
    def set_cooldown(self):
        """Aktifkan cooldown setelah loss"""
        self.cooldown_until = datetime.now() + timedelta(minutes=self.config.COOLDOWN_MINUTES_AFTER_LOSS)
        trading_logger.warning(f"Cooldown aktif sampai {self.cooldown_until.strftime('%H:%M:%S')}")
        
    def get_metrics(self) -> Dict:
        """Dapatkan metrik performa"""
        return {
            'daily_pnl': self.daily_pnl,
            'daily_trades': self.daily_trades,
            'consecutive_losses': self.consecutive_losses,
            'hourly_trades': len(self.hourly_trades),
            'total_trades': len(self.trade_history)
        }
EOF
