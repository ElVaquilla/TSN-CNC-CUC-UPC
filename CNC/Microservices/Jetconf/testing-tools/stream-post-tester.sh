CLIENT_CERT="/home/jetconf/data/example-client_curl.pem"
CA_CERT="/home/jetconf/data/ca-cert.pem"
CLIENT_KEY="/home/jetconf/data/client-key.key"

echo "--- POST new artist"
POST_DATA="@Post-testing.json"
URL="https://127.0.0.1:8443/restconf/data/ieee802-dot1q-tsn-types-upc-version:tsn-uni"
curl --verbose --http2 --tlsv1 -k --cert-type PEM -E $CLIENT_CERT -X POST -d "$POST_DATA" "$URL"
