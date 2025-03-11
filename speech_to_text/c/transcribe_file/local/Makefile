CC=gcc
CFLAGS=-Wall
LIBS=-lcurl -ljson-c

local: local.c
	$(CC) $(CFLAGS) $^ -o $@ $(LIBS)

clean:
	rm -f local
