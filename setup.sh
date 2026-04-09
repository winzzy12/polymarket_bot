cat > setup.sh << 'EOF'
#!/bin/bash

echo "=========================================="
echo "Polymarket AI Trading Bot - Setup Script"
echo "=========================================="

# Warna
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Cek Python
echo -e "\n${YELLOW}[1/5] Checking Python version...${NC}"
if command -v python3.11 &> /dev/null; then
    echo -e "${GREEN}✓ Python 3.11 found${NC}"
    PYTHON_CMD="python3.11"
elif command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    if [[ "$PYTHON_VERSION" == "3.11" || "$PYTHON_VERSION" == "3.12" ]]; then
        echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"
        PYTHON_CMD="python3"
    else
        echo -e "${RED}✗ Python 3.11+ required. Found: $PYTHON_VERSION${NC}"
        exit 1
    fi
else
    echo -e "${RED}✗ Python not found${NC}"
    exit 1
fi

# Buat virtual environment
echo -e "\n${YELLOW}[2/5] Creating virtual environment...${NC}"
$PYTHON_CMD -m venv venv
source venv/bin/activate

# Upgrade pip
echo -e "\n${YELLOW}[3/5] Upgrading pip...${NC}"
pip install --upgrade pip

# Install dependencies
echo -e "\n${YELLOW}[4/5] Installing dependencies...${NC}"
pip install -r requirements.txt

# Buat folder logs
mkdir -p logs

# Cek file .env
echo -e "\n${YELLOW}[5/5] Checking configuration...${NC}"
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  File .env tidak ditemukan. Membuat template...${NC}"
    cat > .env << 'ENVEOF'
# OpenAI API Key (WAJIB)
OPENAI_API_KEY=sk-

# Wallet Configuration (untuk live trading)
PRIVATE_KEY=
WALLET_ADDRESS=

# Polymarket API Credentials (opsional)
API_KEY=
API_SECRET=
API_PASSPHRASE=
ENVEOF
    echo -e "${RED}✗ Silakan edit file .env dan isi OPENAI_API_KEY terlebih dahulu!${NC}"
    echo -e "${YELLOW}   nano .env${NC}"
else
    echo -e "${GREEN}✓ File .env ditemukan${NC}"
fi

echo -e "\n=========================================="
echo -e "${GREEN}✅ Setup Selesai!${NC}"
echo -e "=========================================="
echo -e "\nUntuk menjalankan bot:"
echo -e "  ${YELLOW}source venv/bin/activate${NC}"
echo -e "  ${YELLOW}python bot.py${NC}"
echo -e "\nAtau gunakan: ${YELLOW}./run.sh${NC}"
EOF


