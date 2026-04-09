cat > ai_engine.py << 'EOF'
"""
AI Decision Engine menggunakan OpenAI GPT
"""

import json
import openai
from typing import Dict
from datetime import datetime
from logger import trading_logger

class AIDecisionEngine:
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo", temperature: float = 0.3):
        openai.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.decision_history = []
        
    def _create_prompt(self, btc_data: Dict, market_data: Dict) -> str:
        """Membuat prompt untuk AI"""
        prompt = f"""Anda adalah trader kripto profesional yang sangat berpengalaman.

DATA MARKET SAAT INI:

Bitcoin Price: ${btc_data.get('current_price', 0):,.0f}
Perubahan 1 menit: {btc_data.get('change_1m_percent', 0):+.2f}%
Perubahan 5 menit: {btc_data.get('change_5m_percent', 0):+.2f}%
RSI (14): {btc_data.get('rsi', 50):.1f}
Volatilitas: {btc_data.get('volatility', 0):.2f}%

Polymarket:
- Harga YES: {market_data.get('yes_price', 0.5):.3f}
- Harga NO: {market_data.get('no_price', 0.5):.3f}
- Volume: ${market_data.get('volume', 0):,.0f}

TUGAS:
Prediksi apakah harga Bitcoin akan NAIK atau TURUN dalam 5 menit ke depan.

PERTIMBANGKAN:
1. Momentum harga (perubahan 1m dan 5m)
2. Kondisi overbought/oversold (RSI >70 overbought, <30 oversold)
3. Volatilitas pasar
4. Implied probability dari Polymarket

FORMAT RESPONSE (hanya JSON, tanpa teks lain):
{{
    "decision": "BUY_YES atau BUY_NO atau SKIP",
    "confidence": 0.75,
    "reason": "penjelasan singkat dalam bahasa Indonesia",
    "key_factors": ["faktor1", "faktor2"]
}}

Keterangan:
- BUY_YES = Prediksi NAIK
- BUY_NO = Prediksi TURUN  
- SKIP = Tidak yakin / kondisi tidak bagus
- Confidence = 0-1 (semakin tinggi semakin yakin)

Bersikap konservatif dan fokus pada peluang high-probability.
"""
        return prompt
        
    def _parse_response(self, response_text: str) -> Dict:
        """Parse response dari AI"""
        try:
            # Bersihkan response
            response_text = response_text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            # Parse JSON
            decision = json.loads(response_text)
            
            # Validasi
            if decision.get('decision') not in ['BUY_YES', 'BUY_NO', 'SKIP']:
                decision['decision'] = 'SKIP'
                
            confidence = float(decision.get('confidence', 0.5))
            decision['confidence'] = max(0.0, min(1.0, confidence))
            
            if 'reason' not in decision:
                decision['reason'] = 'Tidak ada alasan'
                
            decision['timestamp'] = datetime.now().isoformat()
            decision['model'] = self.model
            
            return decision
            
        except Exception as e:
            trading_logger.error(f"Error parsing AI response: {e}")
            return {
                'decision': 'SKIP',
                'confidence': 0.0,
                'reason': f'Error parsing: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
            
    def make_decision(self, btc_data: Dict, market_data: Dict) -> Dict:
        """Membuat keputusan trading menggunakan AI"""
        if not btc_data or not market_data:
            return {
                'decision': 'SKIP',
                'confidence': 0.0,
                'reason': 'Data tidak lengkap'
            }
            
        try:
            prompt = self._create_prompt(btc_data, market_data)
            
            trading_logger.ai("Meminta analisis ke AI...")
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Anda adalah trader profesional. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=200
            )
            
            response_text = response.choices[0].message.content
            decision = self._parse_response(response_text)
            
            # Log keputusan
            trading_logger.log_ai_decision(decision)
            
            # Simpan history
            self.decision_history.append(decision)
            if len(self.decision_history) > 100:
                self.decision_history.pop(0)
                
            return decision
            
        except Exception as e:
            trading_logger.error(f"AI error: {e}")
            return {
                'decision': 'SKIP',
                'confidence': 0.0,
                'reason': f'AI Error: {str(e)[:100]}',
                'timestamp': datetime.now().isoformat()
            }
EOF
