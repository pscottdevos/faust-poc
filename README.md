# faust-poc

## Install Kafka (and Zookeeper)

From the main project directory, run:

`$ setup/install.sh`

Re-source your .bashrc file:

`$ . ~/.bashrc`

Or just close and reopen your terminal window.

## Running Kafka and Zookeeper

From the main project directory, run:

```
$ zkServer.sh start
$ env LOG_DIR=/var/local/kafka kafka-server-start.sh -daemon setup/server.properties
```

## Stopping Kafka and Zookeeper

From the main project directory, run:

```
$ kafka-server-stop.sh
$ zkServer.sh stop
```

## To Uninstall

From the main project directory, run:

`$ setup/uninstall.sh`

