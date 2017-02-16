.PHONY: run tests

run: tests
	sudo avocado --config ../avocado.conf run $(shell ls test-*.py)

clean:
	rm -f *.pyc
