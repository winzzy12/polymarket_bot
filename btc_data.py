cat > btc_data.py << 'EOF'
"""
Modul untuk mengambil data harga Bitcoin dari Binance
"""

import requests
import pandas as pd
from typing import Dict, Optional, Tuple
from datetime import datetime
from logger import trading_logger

class BTCDataFetcher:
    def __init__(self, api_base_url: str = "https://api.binance.com"):
        self.api_base_url = api_base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Polymarket-BTC-Bot/1.0'
        })
        
    def get_current_price(self) -> Optional[float]:
        """Mendapatkan harga Bitcoin terkini"""
        try:
            url = f"{self.api_base_url}/api/v3/ticker/price"
            params = {'symbol': 'BTCUSDT'}
            
            response = self.session.get(url, params=params, timeout=5)
            response.raise_for_status()
            
            price = float(response.json()['price'])
            trading_logger.debug(f"Harga BTC: ${price:,.0f}")
            return price
            
        except Exception as e:
            trading_logger.error(f"Error mengambil harga BTC: {e}")
            return None
            
    def get_price_change(self, minutes: int = 1) -> Tuple[float, float]:
        """Menghitung perubahan harga dalam X menit"""
        try:
            url = f"{self.api_base_url}/api/v3/klines"
            params = {
                'symbol': 'BTCUSDT',
                'interval': '1m',
                'limit': minutes + 1
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            klines = response.json()
            
            if len(klines) >= 2:
                current_price = float(klines[-1][4])
                past_price = float(klines[0][4])
                
                change_abs = current_price - past_price
                change_pct = (change_abs / past_price) * 100
                
                return (change_pct, change_abs)
            
            return (0.0, 0.0)
            
        except Exception as e:
            trading_logger.error(f"Error menghitung perubahan: {e}")
            return (0.0, 0.0)
            
    def get_historical_klines(self, limit: int = 100) -> Optional[pd.DataFrame]:
        """Mendapatkan data historical untuk analisis"""
        try:
            url = f"{self.api_base_url}/api/v3/klines"
            params = {
                'symbol': 'BTCUSDT',
                'interval': '1m',
                'limit': limit
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            klines = response.json()
            
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'buy_base', 'buy_quote', 'ignore'
            ])
            
            # Convert ke numeric
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col])
                
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            return df
            
        except Exception as e:
            trading_logger.error(f"Error mengambil historical data: {e}")
            return None
            
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Menghitung RSI sederhana"""
        if len(prices) < period + 1:
            return 50.0
            
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50.0
        
    def calculate_volatility(self, prices: pd.Series, period: int = 20) -> float:
        """Menghitung volatilitas"""
        if len(prices) < period:
            return 2.0
            
        returns = prices.pct_change()
        volatility = returns.rolling(window=period).std() * 100
        
        return volatility.iloc[-1] if not pd.isna(volatility.iloc[-1]) else 2.0
        
    def get_complete_analysis(self) -> Dict:
        """Mendapatkan analisis lengkap BTC"""
        current_price = self.get_current_price()
        if not current_price:
            return {}
            
        # Perubahan harga
        change_1m_pct, change_1m_abs = self.get_price_change(1)
        change_5m_pct, change_5m_abs = self.get_price_change(5)
        
        # Analisis teknikal
        df = self.get_historical_klines(100)
        rsi = 50.0
        volatility = 2.0
        
        if df is not None and len(df) > 20:
            rsi = self.calculate_rsi(df['close'])
            volatility = self.calculate_volatility(df['close'])
            
        result = {
            'current_price': current_price,
            'change_1m_percent': round(change_1m_pct, 2),
            'change_1m_abs': round(change_1m_abs, 2),
            'change_5m_percent': round(change_5m_pct, 2),
            'change_5m_abs': round(change_5m_abs, 2),
            'rsi': round(rsi, 1),
            'volatility': round(volatility, 2),
            'timestamp': datetime.now().isoformat()
        }
        
        trading_logger.debug(f"BTC Analysis: RSI={rsi:.1f} Vol={volatility:.2f}%")
        return result
EOF
