# Buat folder baru
cd ~
mkdir polymarket_bot
cd polymarket_bot

# Buat virtual environment dengan Python 3.11
python3.11 -m venv venv

# Aktifkan virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Run Install
chmod +x setup.sh

# Run Script
chmod +x run.sh
