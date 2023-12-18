docker-compose down

docker-compose up -d 

sleep 4

docker-compose exec topology_discovery bash -c 'python __init__.py'


