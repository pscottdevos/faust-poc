SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
. $SCRIPT_DIR/common_env.sh
. $SCRIPT_DIR/bash_cfg.sh

# Install JDK if not already installed
sudo apt-get install default-jdk

# Install zookeeper
cd $SCRIPT_DIR
curl \
  https://dlcdn.apache.org/zookeeper/zookeeper-$ZOOKEEPER_VER/apache-zookeeper-$ZOOKEEPER_VER-bin.tar.gz > zookeeper.tar.gz
sudo tar -xvf zookeeper.tar.gz -C $INSTALL_DIR
cd $INSTALL_DIR
if [ -h zookeeper ]; then
  sudo rm zookeeper;
fi
sudo ln -s apache-zookeeper-$ZOOKEEPER_VER-bin zookeeper

# Configure zookeeper
sudo sed s+ZOOKEEPER_DATA_DIR+$ZOOKEEPER_DATA_DIR+ $SCRIPT_DIR/zoo.log4j.properties \
  > $INSTALL_DIR/zookeeper/conf/log4j.properties
if [ ! -d $ZOOKEEPER_DATA_DIR ]; then
  sudo mkdir $ZOOKEEPER_DATA_DIR;
fi
sudo chown $USER $ZOOKEEPER_DATA_DIR
sed s+ZOOKEEPER_DATA_DIR+$ZOOKEEPER_DATA_DIR+ $SCRIPT_DIR/zoo.cfg \
  > $INSTALL_DIR/zookeeper/conf/zoo.cfg

# Install kafka
cd $SCRIPT_DIR
curl \
  https://archive.apache.org/dist/kafka/$KAFKA_VER/kafka_$SCALA_VER-$KAFKA_VER.tgz \
  > kafka.tar.gz
sudo tar -xvf kafka.tar.gz -C $INSTALL_DIR
cd $INSTALL_DIR
if [ -h kafka ]; then
  sudo rm kafka;
fi
sudo ln -s kafka_$SCALA_VER-$KAFKA_VER kafka


# Configure kafka

if [ ! -d $KAFKA_DATA_DIR ]; then
  sudo mkdir $KAFKA_DATA_DIR
fi
sudo chown $USER $KAFKA_DATA_DIR

# protect from log4j vulnerability
for JAR in $(find . -name log4j-1.2.17.jar); do
  echo removing JMSAppender.class from $JAR;
  sudo zip -d $JAR org/apache/log4j/net/JMSAppender.class;
done
