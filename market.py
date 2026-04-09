cat > market.py << 'EOF'
"""
Modul untuk mengambil data market dari Polymarket
"""

import requests
import time
from typing import Dict, Optional, List
from datetime import datetime
from logger import trading_logger

class PolymarketMarket:
    def __init__(self, api_base_url: str = "https://gamma-api.polymarket.com"):
        self.api_base_url = api_base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Polymarket-Trading-Bot/1.0'
        })
        self.cache = {}
        
    def find_market(self, market_slug: str) -> Optional[Dict]:
        """Mencari market berdasarkan slug"""
        try:
            # Cek cache dulu
            if market_slug in self.cache and time.time() - self.cache[market_slug]['time'] < 60:
                return self.cache[market_slug]['data']
            
            url = f"{self.api_base_url}/markets"
            params = {
                'slug': market_slug,
                'limit': 10,
                'active': 'true'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            markets = response.json()
            
            if markets and len(markets) > 0:
                market = markets[0]
                trading_logger.success(f"Market ditemukan: {market.get('question', 'Unknown')[:50]}...")
                trading_logger.info(f"Market ID: {market.get('id', 'Unknown')}")
                
                # Simpan ke cache
                self.cache[market_slug] = {
                    'data': market,
                    'time': time.time()
                }
                return market
            else:
                trading_logger.warning(f"Market tidak ditemukan: {market_slug}")
                return None
                
        except requests.RequestException as e:
            trading_logger.error(f"Error mencari market: {e}")
            return None
            
    def get_market_prices(self, market_id: str) -> Optional[Dict]:
        """Mendapatkan harga YES/NO terkini"""
        try:
            url = f"{self.api_base_url}/markets/{market_id}"
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract prices
            yes_price = float(data.get('yesPrice', 0.5))
            no_price = 1.0 - yes_price
            
            # Market stats
            volume = float(data.get('volume', 0))
            liquidity = float(data.get('liquidity', 0))
            
            # Hitung spread (estimasi)
            spread = abs(yes_price - 0.5) * 2
            
            result = {
                'yes_price': yes_price,
                'no_price': no_price,
                'volume': volume,
                'liquidity': liquidity,
                'spread': spread,
                'market_id': market_id,
                'timestamp': datetime.now().isoformat()
            }
            
            trading_logger.debug(f"Harga: YES={yes_price:.3f} NO={no_price:.3f}")
            return result
            
        except Exception as e:
            trading_logger.error(f"Error mengambil harga market: {e}")
            return None
            
    def get_order_book(self, market_id: str, token_id: str) -> Optional[Dict]:
        """Mendapatkan order book untuk token tertentu"""
        try:
            url = f"{self.api_base_url}/markets/{market_id}/orderbook/{token_id}"
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            order_book = response.json()
            return order_book
            
        except Exception as e:
            trading_logger.error(f"Error mengambil order book: {e}")
            return None
            
    def get_market_history(self, market_id: str, limit: int = 100) -> Optional[List[Dict]]:
        """Mendapatkan history harga market"""
        try:
            url = f"{self.api_base_url}/markets/{market_id}/prices"
            params = {'limit': limit}
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            history = response.json()
            return history
            
        except Exception as e:
            trading_logger.error(f"Error mengambil history: {e}")
            return None
EOF
