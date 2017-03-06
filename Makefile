.PHONY: run tests

run: tests
	sudo avocado --show app,test,debug --config ../avocado.conf run $(shell ls test-*.py)

clean:
	rm -f *.pyc
