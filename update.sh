#!/usr/bin/env bash
# Requires SENTRY_AUTH_TOKEN and SENTRY_ORG set in .sentryclirc

old=$(git rev-list HEAD -n 1)
git pull
new=$(git rev-list HEAD -n 1)
if [ ${old} = ${new} ]; then
        version=$(sentry-cli releases propose-version)
        sentry-cli releases new -p royalnet ${version}
        sentry-cli releases set-commits --auto ${version}
fi
sudo python3.6 -m pip install -r requirements.txt
sudo service apache2 restart
python3.6 -OO bots.py
