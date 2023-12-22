#!/bin/bash

CLIENT_CERT="/home/jetconf/data/example-client_curl.pem"
CA_CERT="/home/jetconf/data/ca-cert.pem"
CLIENT_KEY="/home/jetconf/data/client-key.key"

echo "--- POST stream"
POST_DATA="@uniPostTester.json"
POST_DATA2="@uniPostTester2.json"
POST_DATA3="@uniPostTester3.json"
POST_DATA4="@multiPostTester.json"
URL="https://127.0.0.1:8443/restconf/data/ieee802-dot1q-tsn-types-upc-version:tsn-uni/"
URL2="https://127.0.0.1:8443/restconf/operations/jetconf:conf-status"
URL3="https://127.0.0.1:8443/restconf/operations/jetconf:conf-commit"
URL4="https://127.0.0.1:8443/restconf/operations/jetconf:conf-reset"


#curl --verbose -v --http2 --keepalive-time 100 --tlsv1 -k -H 'Connection: keep-alive' --cert-type PEM -E $CLIENT_CERT -X POST -d "$POST_DATA" "$URL" > response-Tester.json
#curl --http2 -k --verbose --tlsv1 --cert-type PEM -E $CLIENT_CERT -X POST -d "$POST_DATA" "$URL"
curl --http2-prior-knowledge -H "X-SSL-Client-CN: marc" -X POST -d "$POST_DATA4" http://127.0.0.1:8443/restconf/data/ieee802-dot1q-tsn-types-upc-version:tsn-uni

#curl --http2-prior-knowledge -H "X-SSL-Client-CN: marc" -X POST -d "$POST_DATA2" http://127.0.0.1:8443/restconf/data/ieee802-dot1q-tsn-types-upc-version:tsn-uni

#curl --http2-prior-knowledge -H "X-SSL-Client-CN: marc" -X POST -d "$POST_DATA3" http://127.0.0.1:8443/restconf/data/ieee802-dot1q-tsn-types-upc-version:tsn-uni

#sleep 4

#docker-compose exec jetconf bash -c './jetconf_processing/get_state.sh'
