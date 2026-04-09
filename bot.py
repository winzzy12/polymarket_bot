cat > bot.py << 'EOF'
#!/usr/bin/env python3
"""
Polymarket AI Trading Bot - Main Entry Point
"""

import time
import signal
import sys
from datetime import datetime

from config import Config
from logger import trading_logger
from market import PolymarketMarket
from btc_data import BTCDataFetcher
from ai_engine import AIDecisionEngine
from strategy import TradingStrategy
from trade_executor import TradeExecutor
from risk_manager import RiskManager

class PolymarketTradingBot:
    def __init__(self):
        """Inisialisasi bot"""
        trading_logger.separator("=")
        trading_logger.info("🤖 POLYMARKET AI TRADING BOT v1.0")
        trading_logger.separator("=")
        
        # Validasi config
        try:
            Config.validate()
        except ValueError as e:
            trading_logger.error(f"Config error: {e}")
            sys.exit(1)
            
        # Inisialisasi komponen
        trading_logger.info("📡 Menghubungkan ke API...")
        self.market = PolymarketMarket(Config.POLYMARKET_GAMMA_API)
        self.btc = BTCDataFetcher(Config.BINANCE_API_URL)
        
        trading_logger.info("🧠 Inisialisasi AI Engine...")
        self.ai = AIDecisionEngine(
            Config.OPENAI_API_KEY,
            Config.AI_MODEL,
            Config.AI_TEMPERATURE
        )
        
        trading_logger.info("⚙️ Inisialisasi Strategy & Risk...")
        self.strategy = TradingStrategy(Config)
        self.executor = TradeExecutor(Config)
        self.risk = RiskManager(Config)
        
        # State
        self.running = True
        self.current_market = None
        self.cycle_count = 0
        
        # Signal handlers
        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)
        
        # Inisialisasi market & balance
        self._init_market()
        initial_balance = self.executor.get_balance()
        self.risk.initialize_balance(initial_balance)
        
        # Tampilkan status
        self._show_status()
        
    def _init_market(self):
        """Inisialisasi market target"""
        trading_logger.info(f"🔍 Mencari market: {Config.MARKET_SLUG}")
        self.current_market = self.market.find_market(Config.MARKET_SLUG)
        
    def _show_status(self):
        """Tampilkan status bot"""
        trading_logger.separator("-")
        trading_logger.info("📊 STATUS BOT")
        trading_logger.info(f"  Mode: {'🔴 TESTING (DRY RUN)' if Config.DRY_RUN_MODE else '🟢 LIVE TRADING'}")
        trading_logger.info(f"  AI Model: {Config.AI_MODEL}")
        trading_logger.info(f"  Interval: {Config.BOT_LOOP_INTERVAL_SECONDS} detik")
        trading_logger.info(f"  Max Trade/Jam: {Config.MAX_TRADES_PER_HOUR}")
        trading_logger.info(f"  Max Position: ${Config.MAX_POSITION_SIZE_USDC:,.0f}")
        trading_logger.separator("-")
        
    def _fetch_data(self):
        """Ambil semua data yang diperlukan"""
        # Cek market
        if not self.current_market:
            self._init_market()
            if not self.current_market:
                return None, None
                
        # Data market
        market_id = self.current_market.get('id')
        market_data = self.market.get_market_prices(market_id)
        
        # Data BTC
        btc_data = self.btc.get_complete_analysis()
        
        return btc_data, market_data
        
    def _execute_cycle(self):
        """Eksekusi satu siklus trading"""
        self.cycle_count += 1
        
        trading_logger.separator("-")
        trading_logger.info(f"🔄 CYCLE #{self.cycle_count} - {datetime.now().strftime('%H:%M:%S')}")
        
        # Ambil data
        btc_data, market_data = self._fetch_data()
        
        if not btc_data or not market_data:
            trading_logger.warning("Data tidak lengkap, skip cycle")
            return
            
        # Tampilkan data ringkas
        trading_logger.info(f"💰 BTC: ${btc_data.get('current_price', 0):,.0f} | "
                          f"1m: {btc_data.get('change_1m_percent', 0):+.2f}% | "
                          f"RSI: {btc_data.get('rsi', 50):.0f}")
        trading_logger.info(f"🎲 Polymarket: YES={market_data.get('yes_price', 0.5):.3f} | "
                          f"NO={market_data.get('no_price', 0.5):.3f}")
        
        # Keputusan AI
        ai_decision = self.ai.make_decision(btc_data, market_data)
        
        # Cek apakah boleh trade
        balance = self.executor.get_balance()
        should_trade, reason, position_size = self.strategy.should_trade(
            ai_decision, btc_data, market_data, balance
        )
        
        if not should_trade:
            trading_logger.log_skip_reason(reason)
            return
            
        # Eksekusi trade
        trading_logger.success(f"✅ TRADE: {ai_decision['decision']} | "
                              f"${position_size:,.2f} | "
                              f"Conf: {ai_decision['confidence']:.1%}")
        
        if ai_decision['decision'] == 'BUY_YES':
            result = self.executor.place_yes_order(
                position_size, 
                "YES_TOKEN", 
                self.current_market.get('address', '')
            )
        else:
            result = self.executor.place_no_order(
                position_size, 
                "NO_TOKEN", 
                self.current_market.get('address', '')
            )
            
        if result:
            trading_logger.log_trade_execution({
                'type': ai_decision['decision'],
                'amount': position_size,
                'confidence': ai_decision['confidence'],
                'reason': ai_decision.get('reason', ''),
                'cycle': self.cycle_count
            })
            
            # Update strategy
            self.strategy.update_after_trade({'pnl': 0, 'size': position_size})
            
    def run(self):
        """Main loop"""
        trading_logger.info("🚀 Memulai bot...")
        trading_logger.info("Tekan Ctrl+C untuk berhenti\n")
        
        while self.running:
            try:
                cycle_start = time.time()
                
                self._execute_cycle()
                
                # Hitung waktu tunggu
                elapsed = time.time() - cycle_start
                sleep_time = max(0, Config.BOT_LOOP_INTERVAL_SECONDS - elapsed)
                
                if sleep_time > 0:
                    trading_logger.debug(f"💤 Tidur {sleep_time:.1f} detik...")
                    
                    # Tidur dengan pengecekan running state
                    for _ in range(int(sleep_time)):
                        if not self.running:
                            break
                        time.sleep(1)
                        
            except KeyboardInterrupt:
                break
            except Exception as e:
                trading_logger.error(f"Error di cycle: {e}")
                import traceback
                trading_logger.error(traceback.format_exc())
                time.sleep(10)
                
        self._shutdown()
        
    def _shutdown(self, signum=None, frame=None):
        """Shutdown bot"""
        if not self.running:
            return
            
        trading_logger.info("\n🛑 Mematikan bot...")
        self.running = False
        
        # Tampilkan ringkasan
        trading_logger.separator("=")
        trading_logger.info("📊 RINGKASAN AKHIR")
        trading_logger.info(f"  Total Cycles: {self.cycle_count}")
        trading_logger.info(f"  Total Trades: {self.strategy.daily_trades}")
        trading_logger.info(f"  Daily PnL: ${self.strategy.daily_pnl:+.2f}")
        
        metrics = self.risk.get_risk_metrics()
        trading_logger.info(f"  Win Rate: {metrics.get('win_rate', 0):.1%}")
        trading_logger.info(f"  Drawdown: {metrics.get('drawdown', 0):.1%}")
        trading_logger.separator("=")
        
        trading_logger.info("👋 Bot berhenti. Selamat tinggal!")
        sys.exit(0)

def main():
    """Entry point"""
    bot = PolymarketTradingBot()
    bot.run()

if __name__ == "__main__":
    main()
EOF
