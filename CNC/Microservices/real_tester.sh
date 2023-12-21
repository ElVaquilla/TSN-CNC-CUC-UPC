  
CLIENT_CERT="/home/jetconf/data/example-client_curl.pem"
CA_CERT="/home/jetconf/data/ca-cert.pem"
CLIENT_KEY="/home/jetconf/data/client-key.key"

#echo "--- POST stream"
#POST_DATA="@Post-testing.json"
#URL="https://127.0.0.1:8443/restconf/data/ieee802-dot1q-tsn-types-upc-version:tsn-uni"
#curl --verbose --http2 --tlsv1 -k --cert-type PEM -E $CLIENT_CERT -X POST -d "$POST_DATA" "$URL"
#sleep 4

docker-compose exec jetconf bash -c './jetconf_processing/get_state.sh'
sleep 3
docker-compose exec jetconf bash -c 'python3 jetconf_processing/state_data_parser.py'
docker-compose exec preprocessing-microservice bash -c 'python __init__.py'
docker-compose exec ilp bash -c 'source /root/miniconda3/bin/activate base && python __init__.py'
docker-compose exec southconf bash -c 'python __init__.py'


