all: test html

test:
	coverage run --source=../singtcommon -m pytest

html:
	coverage html
	open htmlcov/index.html
