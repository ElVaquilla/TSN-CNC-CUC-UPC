# TSN-CNC-CUC-UPC
Time-Sensitive-Networking Controller developed by EETAC-UPC

This Time Sensitive Networking Controller is developed by the Universitat Politècnica de Catalunya - Escola d'Enginyeria de Telecomunicació i Aeroespacial de Castelldefels following the directions of the IEEE 802.1Qcc IEEE Standard for Local and Metropolitan Area Networks--Bridges and Bridged Networks

## Deployment
```
cd TSN-CNC-CUC-UPC/CNC/Microservices
sudo ./wakeup_jetopo.sh #This will discover the topology and wake up the netconf server. Make sure to write switch IP addresses at Topology_discovery/sw_addresses.conf

In another bash:
cd TSN-CNC-CUC-UPC/CNC/Microservices
sudo ./Jetconf/jetconfTester.sh #Send stream list. Make sure source/destination IP addr in uniPostTester.json appear in the topology.

sudo ./real_tester.sh #Calculates scheduling and configures directly connected TSN switches.

```

