cat > logger.py << 'EOF'
"""
Modul logging untuk tracking aktivitas bot
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
import json
from typing import Any, Dict

class Colors:
    """Warna untuk console output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

class TradingLogger:
    def __init__(self, log_file_path: str = "logs/trading_log.txt"):
        """Inisialisasi logger"""
        # Buat folder logs jika belum ada
        Path(log_file_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Setup logger
        self.logger = logging.getLogger("PolymarketBot")
        self.logger.setLevel(logging.INFO)
        self.logger.handlers.clear()
        
        # File handler
        file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Format
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_formatter = logging.Formatter('%(message)s')
        
        file_handler.setFormatter(file_formatter)
        console_handler.setFormatter(console_formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Statistik
        self.trade_count = 0
        self.daily_pnl = 0.0
        
    def _format_message(self, msg: str, color: str = "") -> str:
        """Format pesan dengan warna"""
        if color:
            return f"{color}{msg}{Colors.RESET}"
        return msg
    
    def info(self, message: str):
        self.logger.info(message)
        
    def error(self, message: str):
        msg = self._format_message(f"❌ {message}", Colors.RED)
        self.logger.error(msg)
        
    def warning(self, message: str):
        msg = self._format_message(f"⚠️ {message}", Colors.YELLOW)
        self.logger.warning(msg)
        
    def debug(self, message: str):
        self.logger.debug(message)
        
    def success(self, message: str):
        msg = self._format_message(f"✅ {message}", Colors.GREEN)
        self.logger.info(msg)
        
    def trade(self, message: str):
        msg = self._format_message(f"💰 {message}", Colors.CYAN)
        self.logger.info(msg)
        
    def ai(self, message: str):
        msg = self._format_message(f"🤖 {message}", Colors.BLUE)
        self.logger.info(msg)
        
    def log_ai_decision(self, decision: Dict[str, Any]):
        """Log keputusan AI"""
        self.ai(f"Keputusan: {decision.get('decision', 'UNKNOWN')}")
        self.ai(f"Confidence: {decision.get('confidence', 0):.1%}")
        self.ai(f"Alasan: {decision.get('reason', 'N/A')}")
        self.logger.info(f"AI DECISION DETAIL: {json.dumps(decision, indent=2)}")
        
    def log_trade_execution(self, trade_data: Dict[str, Any]):
        """Log eksekusi trade"""
        self.trade_count += 1
        trade_type = trade_data.get('type', 'UNKNOWN')
        amount = trade_data.get('amount', 0)
        self.trade(f"TRADE #{self.trade_count}: {trade_type} ${amount:,.2f}")
        self.logger.info(f"TRADE EXECUTION: {json.dumps(trade_data, indent=2)}")
        
    def log_balance(self, balance: float, currency: str = "USDC"):
        """Log saldo"""
        self.info(f"💵 Saldo: ${balance:,.2f} {currency}")
        
    def log_pnl(self, pnl: float, total_pnl: float):
        """Log profit/loss"""
        self.daily_pnl += pnl
        pnl_symbol = "📈" if pnl >= 0 else "📉"
        self.trade(f"{pnl_symbol} PNL: ${pnl:+.2f} | Daily: ${self.daily_pnl:+.2f}")
        
    def log_skip_reason(self, reason: str):
        """Log alasan skip trade"""
        self.warning(f"Skipped: {reason}")
        
    def log_performance_metrics(self, metrics: Dict[str, Any]):
        """Log metrik performa"""
        self.info(f"📊 METRIK: {json.dumps(metrics, indent=2)}")
        
    def log_safety_trigger(self, trigger_name: str, details: Dict[str, Any]):
        """Log safety trigger"""
        self.warning(f"🛡️ SAFETY: {trigger_name} - {json.dumps(details)}")
        
    def separator(self, char: str = "=", length: int = 60):
        """Buat garis pemisah"""
        self.info(char * length)

# Instance global
trading_logger = TradingLogger()
EOF
