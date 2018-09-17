#!/usr/bin/env bash
git pull
sudo python3.6 -m pip install -r requirements.txt
sudo service apache2 restart
python3.6 -OO bots.py