source /root/venvs/ai/bin/activate
pip install -r requirements.txt


# Enable the service, if it's already enabled,stop and disable it first
if [ -f /etc/systemd/system/douanes-ai.service ]; then
    systemctl stop douanes-ai.service
    systemctl disable douanes-ai.service
    rm /etc/systemd/system/douanes-ai.service
fi
cp douanes-ai.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable douanes-ai.service
systemctl start douanes-ai.service


# Enable the site. if it's already enabled, disable it first
apt update && apt install -y nginx
cp douanes-api.conf /etc/nginx/sites-available/
if [ -f /etc/nginx/sites-enabled/douanes-api.conf ]; then
    rm /etc/nginx/sites-enabled/douanes-api.conf
fi
ln -s /etc/nginx/sites-available/douanes-api.conf /etc/nginx/sites-enabled/douanes-api.conf
systemctl stop nginx.service
systemctl start nginx.service
systemctl enable nginx.service