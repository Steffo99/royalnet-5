#!/bin/bash

# Royalnet must be installed with `develop`
VERSION=$(python3.7 -m royalnet.version)

rm -rf dist
python setup.py sdist bdist_wheel
twine upload "dist/royalnet-$VERSION"*
hub commit -m "$VERSION"
hub push
hub release create -m "Royalnet $VERSION" "$VERSION"
