git commit -am "publish: %1"
git push && poetry build && poetry publish && hub release create "%1" -m "Royalnet %1" && sentry-cli releases set-commits "%1" --auto && sentry-cli releases deploys "%1" new --env production -n "Version %1"
