cat > config.py << 'EOF'
"""
Konfigurasi Bot Polymarket AI Trading
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # ===== KONFIGURASI WALLET =====
    # Private key wallet Polygon (untuk signing transaksi)
    WALLET_PRIVATE_KEY = os.getenv("PRIVATE_KEY", "")
    WALLET_ADDRESS = os.getenv("WALLET_ADDRESS", "")
    
    # Untuk pengguna Magic/Email wallet
    PROXY_WALLET_ADDRESS = os.getenv("PROXY_WALLET_ADDRESS", "")
    
    # ===== KONFIGURASI POLYMARKET API =====
    # API Credentials untuk CLOB (buat di Polymarket Settings)
    API_KEY = os.getenv("API_KEY", "")
    API_SECRET = os.getenv("API_SECRET", "")
    API_PASSPHRASE = os.getenv("API_PASSPHRASE", "")
    
    # ===== KONFIGURASI AI =====
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    AI_MODEL = "gpt-3.5-turbo"  # atau "gpt-4"
    AI_TEMPERATURE = 0.3
    
    # ===== NETWORK & CONTRACT ADDRESSES =====
    POLYGON_RPC_URL = "https://polygon-rpc.com"
    POLYGON_CHAIN_ID = 137
    
    # Core Trading Contracts Polymarket
    CTF_EXCHANGE_ADDRESS = "0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E"
    NEG_RISK_ADAPTER_ADDRESS = "0xd91E80cF2E7be2e162c4653eA01dF06E3dAeF963"
    USDC_ADDRESS = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
    CTF_ADDRESS = "0x4D97DCd97eC945f40cF65F87097ACe5EA0476045"
    
    # Wallet Factories untuk Magic wallet
    PROXY_FACTORY_ADDRESS = "0xaB45c5A4B0c941a2F231C04C3f49182e1A254052"
    SAFE_FACTORY_ADDRESS = "0xaacfeEa03eb1561C4e67d661e40682Bd20E3541b"
    
    # ===== API ENDPOINTS =====
    POLYMARKET_GAMMA_API = "https://gamma-api.polymarket.com"
    POLYMARKET_CLOB_API = "https://clob.polymarket.com"
    BINANCE_API_URL = "https://api.binance.com"
    
    # ===== MARKET TARGET =====
    MARKET_SLUG = "bitcoin-up-or-down-5-minutes"
    
    # ===== TRADING CONFIGURATION =====
    DEFAULT_TRADE_SIZE_PERCENT = 0.02    # 2% dari balance
    HIGH_CONFIDENCE_TRADE_SIZE = 0.04     # 4% dari balance
    CONFIDENCE_THRESHOLD_HIGH = 0.7
    CONFIDENCE_THRESHOLD_SKIP = 0.55
    
    # ===== RISK MANAGEMENT =====
    MAX_TRADES_PER_HOUR = 10
    DAILY_STOP_LOSS_PERCENT = 0.10        # Berhenti jika loss 10% dalam sehari
    DAILY_PROFIT_TARGET_PERCENT = 0.20    # Target profit 20% per hari
    MAX_POSITION_SIZE_USDC = 500          # Maksimal $500 per trade
    
    # ===== SAFETY FEATURES =====
    MAX_VOLATILITY_THRESHOLD = 0.05       # Skip jika volatilitas > 5%
    MAX_SPREAD_PERCENT = 0.02             # Skip jika spread > 2%
    COOLDOWN_MINUTES_AFTER_LOSS = 5       # Cooldown 5 menit setelah loss
    MIN_LIQUIDITY_USDC = 1000             # Minimal likuiditas $1000
    
    # ===== BOT CONFIGURATION =====
    BOT_LOOP_INTERVAL_SECONDS = 30
    ENABLE_AI_DECISION = True
    DRY_RUN_MODE = True                   # TRUE = testing, FALSE = live trading
    
    # ===== LOGGING =====
    LOG_FILE_PATH = "logs/trading_log.txt"
    LOG_LEVEL = "INFO"
    
    @classmethod
    def validate(cls):
        """Validasi konfigurasi sebelum bot berjalan"""
        if not cls.DRY_RUN_MODE:
            if not cls.WALLET_PRIVATE_KEY and not cls.PROXY_WALLET_ADDRESS:
                raise ValueError("WALLET_PRIVATE_KEY atau PROXY_WALLET_ADDRESS harus diisi!")
            if not cls.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY harus diisi!")
        return True
    
    @classmethod
    def is_live_mode(cls):
        return not cls.DRY_RUN_MODE
EOF
