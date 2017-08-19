all:

install:
	install -D beautify_bash.py $(DESTDIR)/usr/bin/beautify_bash

test:
	prove -f
	prove -v -f t_todo || true

.PHONY: all install test
