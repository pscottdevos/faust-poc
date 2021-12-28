if [ $(egrep '^export ZOOKEEPER_HOME=/usr/share/zookeeper$' ~/.bashrc | wc -l) = 0 ];
then
  echo 'export ZOOKEEPER_HOME=/usr/share/zookeeper' >> ~/.bashrc;
fi
if [ $(egrep '^export PATH=\$ZOOKEEPER_HOME/bin:\$PATH$' ~/.bashrc | wc -l) = 0 ];
then
  echo 'export PATH=$ZOOKEEPER_HOME/bin:$PATH' >> ~/.bashrc;
fi
if [ $(egrep '^export ZOO_LOG_DIR=/var/local/zookeeper/logs$' ~/.bashrc | wc -l) = 0 ];
then
  echo 'export ZOO_LOG_DIR=/var/local/zookeeper/logs' >> ~/.bashrc;
fi

if [ $(egrep '^export KAFKA_HOME=/usr/share/kafka$' ~/.bashrc | wc -l) = 0 ];
then
  echo 'export KAFKA_HOME=/usr/share/kafka' >> ~/.bashrc;
fi
if [ $(egrep '^export PATH=\$KAFKA_HOME/bin:\$PATH$' ~/.bashrc | wc -l) = 0 ];
then
  echo 'export PATH=$KAFKA_HOME/bin:$PATH' >> ~/.bashrc;
fi
