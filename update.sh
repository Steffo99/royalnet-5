#!/usr/bin/env bash
git pull
sudo service apache2 restart
python3.6 -OO bots.py