cat > trade_executor.py << 'EOF'
"""
Modul eksekusi trade di Polymarket
"""

from web3 import Web3
from typing import Dict, Optional
from logger import trading_logger

class TradeExecutor:
    def __init__(self, config):
        self.config = config
        self.dry_run = config.DRY_RUN_MODE
        
        if not self.dry_run and config.WALLET_PRIVATE_KEY:
            try:
                self.web3 = Web3(Web3.HTTPProvider(config.POLYGON_RPC_URL))
                if self.web3.is_connected():
                    self.account = self.web3.eth.account.from_key(config.WALLET_PRIVATE_KEY)
                    self.wallet_address = self.account.address
                    trading_logger.success(f"Wallet connected: {self.wallet_address[:10]}...")
                else:
                    trading_logger.error("Gagal koneksi ke Polygon")
                    self.dry_run = True
            except Exception as e:
                trading_logger.error(f"Error init wallet: {e}")
                self.dry_run = True
        else:
            self.dry_run = True
            
        if self.dry_run:
            trading_logger.warning("⚠️ DRY RUN MODE - Tidak ada transaksi real")
            
    def get_balance(self) -> float:
        """Dapatkan saldo wallet"""
        if self.dry_run:
            return 10000.0  # Simulasi balance untuk testing
            
        try:
            # USDC contract
            usdc_address = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
            usdc_abi = [{
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            }]
            
            usdc_contract = self.web3.eth.contract(
                address=Web3.to_checksum_address(usdc_address),
                abi=usdc_abi
            )
            
            balance = usdc_contract.functions.balanceOf(self.wallet_address).call()
            return balance / 1e6  # USDC decimals = 6
            
        except Exception as e:
            trading_logger.error(f"Error get balance: {e}")
            return 0.0
            
    def get_token_ids(self, market_id: str) -> Dict[str, str]:
        """Dapatkan token IDs untuk market"""
        # TODO: Implement query ke contract untuk mendapatkan token IDs
        # Untuk sekarang return placeholder
        return {
            'yes_token_id': f"{market_id}_YES",
            'no_token_id': f"{market_id}_NO"
        }
        
    def _estimate_gas(self, transaction: Dict) -> int:
        """Estimasi gas untuk transaksi"""
        try:
            if not self.dry_run:
                gas = self.web3.eth.estimate_gas(transaction)
                return int(gas * 1.2)  # Buffer 20%
        except:
            pass
        return 200000  # Default gas limit
        
    def _get_gas_price(self) -> int:
        """Dapatkan gas price terkini"""
        try:
            if not self.dry_run:
                gas_price = self.web3.eth.gas_price
                return int(gas_price * 1.1)  # Naikkan 10% untuk faster confirmation
        except:
            pass
        return 50 * 10**9  # 50 Gwei default
        
    def place_yes_order(self, amount: float, token_id: str, market_address: str) -> Optional[Dict]:
        """Place BUY YES order"""
        if self.dry_run:
            trading_logger.trade(f"🔵 [DRY RUN] BUY YES: ${amount:,.2f}")
            return {
                'success': True,
                'dry_run': True,
                'amount': amount,
                'token_id': token_id,
                'type': 'BUY_YES'
            }
            
        # TODO: Implement actual on-chain order placement
        trading_logger.warning("Live trading belum diimplementasikan sepenuhnya")
        return {
            'success': True,
            'simulated': True,
            'amount': amount
        }
        
    def place_no_order(self, amount: float, token_id: str, market_address: str) -> Optional[Dict]:
        """Place BUY NO order"""
        if self.dry_run:
            trading_logger.trade(f"🔴 [DRY RUN] BUY NO: ${amount:,.2f}")
            return {
                'success': True,
                'dry_run': True,
                'amount': amount,
                'token_id': token_id,
                'type': 'BUY_NO'
            }
            
        # TODO: Implement actual on-chain order placement
        trading_logger.warning("Live trading belum diimplementasikan sepenuhnya")
        return {
            'success': True,
            'simulated': True,
            'amount': amount
        }
        
    def check_allowance(self, spender_address: str) -> int:
        """Cek allowance USDC untuk spender"""
        if self.dry_run:
            return 10**18  # Simulasi allowance unlimited
            
        try:
            usdc_address = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
            usdc_abi = [{
                "constant": True,
                "inputs": [
                    {"name": "_owner", "type": "address"},
                    {"name": "_spender", "type": "address"}
                ],
                "name": "allowance",
                "outputs": [{"name": "", "type": "uint256"}],
                "type": "function"
            }]
            
            usdc_contract = self.web3.eth.contract(
                address=Web3.to_checksum_address(usdc_address),
                abi=usdc_abi
            )
            
            allowance = usdc_contract.functions.allowance(
                self.wallet_address,
                Web3.to_checksum_address(spender_address)
            ).call()
            
            return allowance
            
        except Exception as e:
            trading_logger.error(f"Error check allowance: {e}")
            return 0
EOF
