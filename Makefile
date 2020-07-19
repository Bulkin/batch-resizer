all:
	cp header.py batch-resizer.py
	python -c "import sys; print(sys.stdin.read().replace('QML_CODE=None', 'QML_CODE=\'\'\'' + open('resizer.qml').read() + '\'\'\''))" < resizer-qml.py >> batch-resizer.py
	chmod +x batch-resizer.py

