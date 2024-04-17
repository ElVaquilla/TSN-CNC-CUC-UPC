#sudo python3 Topology_discovery/test.py
docker-compose down 

docker-compose up -d
#docker-compose run --service-ports jetconf
sleep 4

docker-compose exec topology_discovery bash -c 'python __init__.py'

sleep 4

#docker-compose exec opendaylight bash -c './bin/karaf' -d

sudo docker-compose exec jetconf bash -c './configuration_deployer.sh' 


