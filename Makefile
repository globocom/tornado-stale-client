setup:
	@pip install -U -r requirements.txt

test:
	@nosetests -v --with-coverage --cover-branches --cover-erase \
		--cover-package tornado_stale_client \
		tests/

coverage:
	@coverage html -i
