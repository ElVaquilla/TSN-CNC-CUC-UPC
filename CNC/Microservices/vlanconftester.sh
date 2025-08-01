docker compose down

docker compose up -d 

sleep 4

docker compose exec vlan_configurator bash -c 'python __init__.py'
