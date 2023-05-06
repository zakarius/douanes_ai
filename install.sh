apt-get install python3.10 python3-pip pyton-is-python3 -y

if [ ! -d /root/venvs/ai ]; then
    python -m venv /root/venvs/ai
fi
source /root/venvs/ai/bin/activate
pip install -r requirements.txt

./update.sh