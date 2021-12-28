SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
. $SCRIPT_DIR/common_env.sh
cd $INSTALL_DIR

# Uninstall zookeeper
if [ -h zookeeper ]; then
  sudo rm zookeeper;
fi
if [ -d apache-zookeeper-$ZOOKEEPER_VER-bin ]; then
  sudo rm -rf apache-zookeeper-$ZOOKEEPER_VER-bin;
fi
if [ -d $ZOOKEEPER_DATA_DIR ]; then
  sudo rm -rf $ZOOKEEPER_DATA_DIR;
fi

# Uninstall kafka

if [ -h kafka ]; then
  sudo rm kafka;
fi
if [ -d  kafka_$SCALA_VER-$KAFKA_VER ]; then
  sudo rm -rf kafka_$SCALA_VER-$KAFKA_VER;
fi
if [ -d $KAFKA_DATA_DIR ]; then
  sudo rm -rf $KAFKA_DATA_DIR;
fi

# Remove paths from .bashrc
mv ~/.bashrc ~/.bashrc.save
egrep -v 'export (PATH=\$|)(ZOOKEEPER_HOME|ZOO_LOG_DIR|KAFKA_HOME)(=|\/bin)' ~/.bashrc.save > ~/.bashrc
