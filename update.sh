# Copy the files to the right place
cp douanes-api.conf /etc/nginx/sites-available/
cp douanes-ai.service /etc/systemd/system/

# Enable the service
systemctl daemon-reload
systemctl enable douanes-ai.service
systemctl start douanes-ai.service


# Enable the site. if it's already enabled, disable it first
if [ -f /etc/nginx/sites-enabled/douanes-api.conf ]; then
    rm /etc/nginx/sites-enabled/douanes-api.conf
fi
ln -s /etc/nginx/sites-available/douanes-api.conf /etc/nginx/sites-enabled/douanes-api.conf
systemctl restart nginx.service



