# WebNetworkDump
This should help networkengineers for giving an overview of new networks. It will ask for IP-Network to do a tcp portscan. It will try to login and find the devicetype

Then it will login and execute a buntch of "show-commands" depending on devicetype. The ouput will be parsed and some Excelfiles will be generated.

This files can be downloadet and used for deeper analysis

## Easystart with DockerContainer on local mashine!

- Clone Git-Repo:
  - ```git clone https://github.com/edergernot/webnetworkdump```

- Jump into that directory:
  - ```cd webnetworkdump```
- Build Container:
  - ```docker-compose build```

- Start Container:
  - ```docker-compose up```

- Start dumping the Network and browse to:
  - ```http://localhost:5000```

Just add devicecredentials and discovery-network.
Follow the links, Discovery, Dump, then download the result as zip-file or build the CDP-Graph.

## Sceenshots:

![Startscreen](images/StartScreen.png)

![Discover](images/Device%20Discovery.png)

![DiscoverDone](images/DiscoveryDone.png)

![ParseDonw](images/parsing_done.png)




