# check if Dirrectories doesn't exist on hdfs
docker exec -i namenode hdfs dfs -check /user/heart_disease/raw || exist 0
=> create folder if doesn't exist

docker exec -i namenode hdfs dfs -check /warehouse || exit 
=> create if doesn't exit
docker exec -i namenode chmod 777 /warehouse && chown hive:root  /warehouse\

docker exec -i namenode hdfs dfs -check /hbase || exit 
=> create if doesn't exit
