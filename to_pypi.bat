
del /f /q /s dist\*.*
python setup.py sdist bdist_wheel
twine upload dist/*
