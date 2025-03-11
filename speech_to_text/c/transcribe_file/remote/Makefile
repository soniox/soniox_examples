CC=gcc
CFLAGS=-Wall
LIBS=-lcurl -ljson-c

remote: remote.c
	$(CC) $(CFLAGS) $^ -o $@ $(LIBS)

clean:
	rm -f remote
