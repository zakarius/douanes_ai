apt-get update && apt-get install python3-all python3-pip nginx  -y

if [ ! -d /root/venvs/ai ]; then
    python -m venv /root/venvs/ai
fi
source /root/venvs/ai/bin/activate
pip install -r requirements.txt

./update.sh