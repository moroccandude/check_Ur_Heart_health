# Create Presto configuration directories
mkdir -p presto/etc/catalog

# Create config.properties
cat > presto/etc/config.properties << EOF
coordinator=true
node-scheduler.include-coordinator=true
http-server.http.port=8080
query.max-memory=5GB
query.max-memory-per-node=1GB
discovery-server.enabled=true
discovery.uri=http://presto-coordinator:8080
EOF

# Create jvm.config
cat > presto/etc/jvm.config << EOF
-server
-Xmx16G
-XX:+UseG1GC
-XX:G1HeapRegionSize=32M
-XX:+UseGCOverheadLimit
-XX:+ExplicitGCInvokesConcurrent
-XX:+HeapDumpOnOutOfMemoryError
-XX:+ExitOnOutOfMemoryError
EOF

# Create log.properties
cat > presto/etc/log.properties << EOF
com.facebook.presto=INFO
EOF

# Create node.properties
cat > presto/etc/node.properties << EOF
node.environment=production
node.id=presto-coordinator
node.data-dir=/var/presto/data
EOF

# Create Hive catalog properties
cat > presto/etc/catalog/hive.properties << EOF
connector.name=hive-hadoop2
hive.metastore.uri=thrift://hive-metastore:9083
hive.allow-drop-table=true
hive.allow-rename-table=true
hive.storage-format=ORC
EOF