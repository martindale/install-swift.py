Install script for @OpenStack Swift.

Should be run on a **clean** Ubuntu 12.04 install. 

Will run swift by default.  After reboots, run `/root/bin/startmain` to start swift.

# Check that swift works
```
swift -v -A http://127.0.0.1:8080/auth/v1.0 -U test:tester -K testing stat
swift -v -A http://127.0.0.1:8080/auth/v1.0 -U test:tester -K testing list images
swift -v -A http://127.0.0.1:8080/auth/v1.0 -U test:tester -K testing upload images test.data
swift -v -A http://127.0.0.1:8080/auth/v1.0 -U test:tester -K testing download images test.data


curl -k -D - -H 'X-Storage-User: test:tester' -H 'X-Storage-Pass: testing' http://127.0.0.1:8080/auth/v1.0

HTTP/1.1 200 OK
X-Storage-Url: http://127.0.0.1:8080/v1/AUTH_test
X-Storage-Token: AUTH_tkbf3cb494b8f749b7b34b6d26ac74297b
X-Auth-Token: AUTH_tkbf3cb494b8f749b7b34b6d26ac74297b
Content-Length: 0
Date: Thu, 31 May 2012 15:47:44 GMT


curl -k -X HEAD -D -  -H 'X-Auth-Token: AUTH_tkbf3cb494b8f749b7b34b6d26ac74297b' http://127.0.0.1:8080/v1/AUTH_test
HTTP/1.1 204 No Content
X-Account-Object-Count: 0
X-Timestamp: 1338476353.78581
X-Account-Bytes-Used: 0
X-Account-Container-Count: 0
Accept-Ranges: bytes
Content-Length: 0
Date: Thu, 31 May 2012 15:49:34 GMT


curl -k -X GET -H 'X-Auth-Token: AUTH_tkbf3cb494b8f749b7b34b6d26ac74297b' http://127.0.0.1:8080/v1/AUTH_test/images

curl -k -X GET -H 'X-Auth-Token: AUTH_tkbf3cb494b8f749b7b34b6d26ac74297b' http://127.0.0.1:8080/v1/AUTH_test/images?format=xml

#create container and upload object
curl -k -X PUT -T ./test.data -H 'Content-Type: text/plain' -H 'X-Auth-Token: AUTH_tkbf3cb494b8f749b7b34b6d26ac74297b' http://127.0.0.1:8080/v1/AUTH_test/images/test.data
curl -k -X PUT -H 'Content-Type: text/plain' -H 'X-Auth-Token: AUTH_tkbf3cb494b8f749b7b34b6d26ac74297b' http://127.0.0.1:8080/v1/AUTH_test/images

#download object
curl -k -X GET -H 'X-Auth-Token: AUTH_tkbf3cb494b8f749b7b34b6d26ac74297b' http://127.0.0.1:8080/v1/AUTH_test/images/test.data -o test2.data
curl -k -X GET -H 'X-Auth-Token: AUTH_tkbf3cb494b8f749b7b34b6d26ac74297b' http://127.0.0.1:8080/v1/AUTH_test/images/.bashrc
```

