cat > run.sh << 'EOF'
#!/bin/bash

# Warna
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=========================================="
echo "Polymarket AI Trading Bot"
echo "=========================================="

# Aktifkan virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo -e "${RED}Virtual environment tidak ditemukan!${NC}"
    echo "Jalankan ./setup.sh terlebih dahulu"
    exit 1
fi

# Cek API key
if ! grep -q "OPENAI_API_KEY=sk-" .env 2>/dev/null || grep -q "OPENAI_API_KEY=sk-$" .env 2>/dev/null; then
    echo -e "${RED}❌ OPENAI_API_KEY belum diisi!${NC}"
    echo "Edit file .env dan isi API key Anda"
    exit 1
fi

echo -e "${GREEN}✅ Konfigurasi OK${NC}"
echo -e "Memulai bot...\n"

# Jalankan bot
python bot.py
EOF

chmod +x run.sh
