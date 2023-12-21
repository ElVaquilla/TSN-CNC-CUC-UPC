#!/bin/bash

CLIENT_CERT="/home/jetconf/data/example-client_curl.pem"
CA_CERT="/home/jetconf/data/ca-cert.pem"
CLIENT_KEY="/home/jetconf/data/client-key.key"

echo "--- POST stream"
POST_DATA="@uniPostTester.json"
POST_DATA2="@uniPostTester2.json"
POST_DATA3="@uniPostTester3.json"
URL="https://172.21.0.9:8443/restconf/data/ieee802-dot1q-tsn-types-upc-version:tsn-uni/"
URL2="https://127.0.0.1:8443/restconf/operations/jetconf:conf-status"
URL3="https://127.0.0.1:8443/restconf/operations/jetconf:conf-commit"
URL4="https://127.0.0.1:8443/restconf/operations/jetconf:conf-reset"

#curl --verbose -v --http2 --keepalive-time 100 --tlsv1 -k -H 'Connection: keep-alive' --cert-type PEM -E $CLIENT_CERT -X POST -d "$POST_DATA" "$URL" > response-Tester.json
#curl --http2 -k --verbose --tlsv1.2 -v -H 'Accept: */*' -H 'Content-Type:yang.api+json' --cert-type PEM -E $CLIENT_CERT -X POST -d "$POST_DATA" "$URL"
curl --http2 -k --verbose --tlsv1 -v --cert-type PEM -E $CLIENT_CERT -X POST -d "$POST_DATA" "$URL"
curl --http2 -k --verbose --tlsv1 -v --cert-type PEM -E $CLIENT_CERT -X POST -d "$POST_DATA2" "$URL"
curl --http2 -k --verbose --tlsv1 -v --cert-type PEM -E $CLIENT_CERT -X POST -d "$POST_DATA3" "$URL"

#curl -http2 -k --verbose --tlsv1 -v --cert-type PEM -E $CLIENT_CERT -X POST -d "$URL4"

#curl --http2-prior-knowledge -k --verbose -H "X-SSL-Client-CN: marc" -X POST -d "$POST_DATA" "$URL"
sleep 4

#docker-compose exec jetconf bash -c './jetconf_processing/get_state.sh'
