BUMP := 'patch'

setup:
	@pip install -U -r requirements.txt

test:
	@nosetests -v --with-coverage --cover-branches --cover-erase \
		--cover-package tornado_stale_client \
		tests/

coverage:
	@coverage html -i

patch:
	@$(eval BUMP := 'patch')

minor:
	@$(eval BUMP := 'minor')

major:
	@$(eval BUMP := 'major')

bump:
	@bumpversion ${BUMP}

release:
	@python setup.py -q sdist upload
	@git push
	@git push --tags

register:
	@python setup.py register
