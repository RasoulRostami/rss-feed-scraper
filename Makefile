compile_requirements:
	pip-compile requirements/prod.in
	pip-compile requirements/dev.in

test:
	coverage run manage.py test

test.only_show_errors:
	ERROR_ONLY=true coverage run manage.py test

coverage.shell_report:
	coverage report

coverage.html_report:
	coverage html

check_black:
	black --skip-string-normalization --line-length 128 .
