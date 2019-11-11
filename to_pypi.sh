#!/bin/bash

# Royalnet must be installed with `develop`
VERSION=$(python3.7 -m royalnet.version)

rm -rf dist
python setup.py sdist bdist_wheel
twine upload "dist/royalnet-$VERSION"*
git add *
git commit -m "$VERSION"
git push
hub release create --message "Royalnet $VERSION" --prerelease "$VERSION"
