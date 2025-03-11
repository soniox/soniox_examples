CC = gcc
CFLAGS = -Wall
LIBS = -lwebsockets -ljson-c

realtime: realtime.c
	$(CC) $(CFLAGS) $^ -o $@ $(LIBS)

clean:
	rm -f realtime
