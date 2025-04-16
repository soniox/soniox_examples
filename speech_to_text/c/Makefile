CC = gcc
CFLAGS = -Wall
ASYNC_LIBS = -lcurl -ljson-c
REAL_TIME_LIBS = -lwebsockets -ljson-c

async_remote_file: async/remote_file.c
	$(CC) $(CFLAGS) $^ -o $@ $(ASYNC_LIBS)

async_local_file: async/local_file.c
	$(CC) $(CFLAGS) $^ -o $@ $(ASYNC_LIBS)

real_time_stream_file: real_time/stream_file.c
	$(CC) $(CFLAGS) $^ -o $@ $(REAL_TIME_LIBS)

clean:
	rm -f async_remote_file
	rm -f async_local_file
	rm -f real_time_stream_file
