#!/bin/bash

# Create the configuration files
mkdir -p hadoop-config
cd hadoop-config

# Create core-site.xml
cat > core-site.xml << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
    <property>
        <name>fs.defaultFS</name>
        <value>hdfs://namenode:8020</value>
    </property>
</configuration>
EOF

# Create hdfs-site.xml
cat > hdfs-site.xml << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
    <property>
        <name>dfs.replication</name>
        <value>1</value>
    </property>
    <property>
        <name>dfs.namenode.name.dir</name>
        <value>file:///hadoop/dfs/name</value>
    </property>
    <property>
        <name>dfs.datanode.data.dir</name>
        <value>file:///hadoop/dfs/data</value>
    </property>
    <property>
        <name>dfs.namenode.rpc-bind-host</name>
        <value>0.0.0.0</value>
    </property>
    <property>
        <name>dfs.namenode.servicerpc-bind-host</name>
        <value>0.0.0.0</value>
    </property>
    <property>
        <name>dfs.namenode.http-bind-host</name>
        <value>0.0.0.0</value>
    </property>
    <property>
        <name>dfs.namenode.https-bind-host</name>
        <value>0.0.0.0</value>
    </property>
    <property>
        <name>dfs.client.use.datanode.hostname</name>
        <value>true</value>
    </property>
    <property>
        <name>dfs.datanode.use.datanode.hostname</name>
        <value>true</value>
    </property>
</configuration>
EOF

# Create yarn-site.xml
cat > yarn-site.xml << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
    <property>
        <name>yarn.nodemanager.aux-services</name>
        <value>mapreduce_shuffle</value>
    </property>
    <property>
        <name>yarn.nodemanager.aux-services.mapreduce_shuffle.class</name>
        <value>org.apache.hadoop.mapred.ShuffleHandler</value>
    </property>
    <property>
        <name>yarn.resourcemanager.hostname</name>
        <value>resourcemanager</value>
    </property>
    <property>
        <name>yarn.resourcemanager.address</name>
        <value>resourcemanager:8032</value>
    </property>
    <property>
        <name>yarn.resourcemanager.scheduler.address</name>
        <value>resourcemanager:8030</value>
    </property>
    <property>
        <name>yarn.resourcemanager.resource-tracker.address</name>
        <value>resourcemanager:8031</value>
    </property>
    <property>
        <name>yarn.resourcemanager.bind-host</name>
        <value>0.0.0.0</value>
    </property>
    <property>
        <name>yarn.nodemanager.bind-host</name>
        <value>0.0.0.0</value>
    </property>
</configuration>
EOF

# Create docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3'

services:
  namenode:
    image: apache/hadoop:3.3.5
    hostname: namenode
    container_name: namenode
    ports:
      - "9870:9870"   # NameNode web UI
      - "8020:8020"   # NameNode IPC
    environment:
      - HADOOP_CONF_DIR=/etc/hadoop
    volumes:
      - ./hdfs-site.xml:/etc/hadoop/hdfs-site.xml
      - ./core-site.xml:/etc/hadoop/core-site.xml
      - namenode_data:/hadoop/dfs/name
    command: ["hdfs", "namenode"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://namenode:9870"]
      interval: 30s
      timeout: 10s
      retries: 3

  datanode1:
    image: apache/hadoop:3.3.5
    hostname: datanode1
    container_name: datanode1
    depends_on:
      - namenode
    ports:
      - "9864:9864"   # DataNode web UI
    environment:
      - HADOOP_CONF_DIR=/etc/hadoop
    volumes:
      - ./hdfs-site.xml:/etc/hadoop/hdfs-site.xml
      - ./core-site.xml:/etc/hadoop/core-site.xml
      - datanode1_data:/hadoop/dfs/data
    command: ["hdfs", "datanode"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://datanode1:9864"]
      interval: 30s
      timeout: 10s
      retries: 3

  resourcemanager:
    image: apache/hadoop:3.3.5
    hostname: resourcemanager
    container_name: resourcemanager
    depends_on:
      - namenode
    ports:
      - "8088:8088"   # ResourceManager web UI
    environment:
      - HADOOP_CONF_DIR=/etc/hadoop
    volumes:
      - ./yarn-site.xml:/etc/hadoop/yarn-site.xml
      - ./core-site.xml:/etc/hadoop/core-site.xml
    command: ["yarn", "resourcemanager"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://resourcemanager:8088"]
      interval: 30s
      timeout: 10s
      retries: 3

  nodemanager:
    image: apache/hadoop:3.3.5
    hostname: nodemanager
    container_name: nodemanager
    depends_on:
      - resourcemanager
    ports:
      - "8042:8042"   # NodeManager web UI
    environment:
      - HADOOP_CONF_DIR=/etc/hadoop
    volumes:
      - ./yarn-site.xml:/etc/hadoop/yarn-site.xml
      - ./core-site.xml:/etc/hadoop/core-site.xml
    command: ["yarn", "nodemanager"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://nodemanager:8042"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  namenode_data:
  datanode1_data:
EOF

# Format the HDFS NameNode
echo "Starting HDFS setup..."
docker-compose up -d namenode

# Wait for NameNode to start up
echo "Waiting for NameNode to start..."
sleep 10

# Format the HDFS NameNode
echo "Formatting NameNode..."
docker exec -it namenode hdfs namenode -format

# Start the rest of the services
echo "Starting all services..."
docker-compose up -d

# Show the status
echo "HDFS cluster is now running. Service status:"
docker-compose ps

echo "You can access the HDFS NameNode UI at http://localhost:9870"
echo "You can access the YARN ResourceManager UI at http://localhost:8088"