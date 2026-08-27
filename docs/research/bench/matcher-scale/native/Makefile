libscan.dylib: scan.c
	cc -O2 -shared -fPIC -o libscan.dylib scan.c

libscan.so: scan.c
	cc -O2 -shared -fPIC -o libscan.so scan.c

clean:
	rm -f libscan.dylib libscan.so
