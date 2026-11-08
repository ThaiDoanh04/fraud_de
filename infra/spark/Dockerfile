FROM apache/spark:3.5.9-java17-python3

# Spark không kèm sẵn connector Kafka/Avro/Iceberg -> tải jar vào thư mục jars lúc build
ARG MVN=https://repo1.maven.org/maven2
ADD --chmod=644 ${MVN}/org/apache/spark/spark-sql-kafka-0-10_2.12/3.5.9/spark-sql-kafka-0-10_2.12-3.5.9.jar \
                ${MVN}/org/apache/spark/spark-token-provider-kafka-0-10_2.12/3.5.9/spark-token-provider-kafka-0-10_2.12-3.5.9.jar \
                ${MVN}/org/apache/kafka/kafka-clients/3.4.1/kafka-clients-3.4.1.jar \
                ${MVN}/org/apache/commons/commons-pool2/2.11.1/commons-pool2-2.11.1.jar \
                ${MVN}/org/apache/spark/spark-avro_2.12/3.5.9/spark-avro_2.12-3.5.9.jar \
                ${MVN}/org/apache/iceberg/iceberg-spark-runtime-3.5_2.12/1.9.2/iceberg-spark-runtime-3.5_2.12-1.9.2.jar \
                ${MVN}/org/apache/iceberg/iceberg-aws-bundle/1.9.2/iceberg-aws-bundle-1.9.2.jar \
                /opt/spark/jars/


# volume checkpoint mount vào đây; tạo sẵn với quyền của user spark (uid 185) để Spark ghi được
USER root
RUN mkdir -p /checkpoints && chown 185:185 /checkpoints
USER 185
