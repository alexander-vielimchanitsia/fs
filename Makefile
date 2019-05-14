# make fat mkdir /foo
# make fat mkdir /foo/bar
# make fat touch /foo/bar/test.txt
# make fat write /foo/bar/test.txt data="some test data"
# make fat read /foo/bar/test.txt

%:
	@:

install:
	pipenv install --dev

test:
	pipenv run pytest test/ -s

fat:
	pipenv run python fat $(filter-out $@,$(MAKECMDGOALS)) --data "$(data)"

clean:
	rm fat/data/volume

.PHONY: test fat clean
