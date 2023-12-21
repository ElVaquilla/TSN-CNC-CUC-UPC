#!/bin/bash

CLIENT_CERT="/home/jetconf/data/example-client_curl.pem"
URL="https://127.0.0.1:8443/restconf/data/ieee802-dot1q-tsn-types-upc-version:tsn-uni"
#URL2="https://127.0.0.1:8443/restconf/data/example-jukebox"
URL3="https://172.19.0.5:8443/restconf/data/ieee802-dot1q-tsn-types-upc-version:tsn-uni"

#curl --http2 -k --cert-type PEM -v -E $CLIENT_CERT -X GET "$URL" > state_data.json

curl --http2-prior-knowledge -H "X-SSL-Client-CN: marc" -X GET http://127.0.0.1:8443/restconf/data/ieee802-dot1q-tsn-types-upc-version:tsn-uni > jetconf_processing/state_data.json

