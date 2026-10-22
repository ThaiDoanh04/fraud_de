#!/usr/bin/env bash
# Kiểm tra nhanh toàn bộ hệ thống: mọi service trả lời được, và Trino ghi/đọc
# được một bảng Iceberg thật (Trino -> REST catalog -> Postgres + MinIO).
set -uo pipefail

COMPOSE="docker compose --env-file .env -f infra/docker-compose.yml"
TIMEOUT=${SMOKE_TIMEOUT:-240}
failed=0

wait_for() {  # wait_for <tên> <lệnh kiểm tra...>
  local name=$1; shift
  local start=$SECONDS
  until "$@" > /dev/null 2>&1; do
    if (( SECONDS - start > TIMEOUT )); then
      echo "FAIL  $name (không phản hồi sau ${TIMEOUT}s)"; failed=1; return
    fi
    sleep 3
  done
  echo "OK    $name"
}

wait_for "postgres"        $COMPOSE exec -T postgres pg_isready
wait_for "kafka"           $COMPOSE exec -T kafka /opt/kafka/bin/kafka-broker-api-versions.sh --bootstrap-server localhost:9092
wait_for "kafka-ui"        curl -sf -o /dev/null http://localhost:8088/
wait_for "schema-registry" curl -sf http://localhost:8081/subjects
wait_for "minio"           curl -sf http://localhost:9000/minio/health/live
wait_for "iceberg-rest"    curl -sf http://localhost:8181/v1/config
wait_for "trino"           bash -c "curl -sf http://localhost:8080/v1/info | grep -q '\"starting\":false'"
wait_for "redis"           bash -c "$COMPOSE exec -T redis redis-cli ping | grep -q PONG"
wait_for "mlflow"          curl -sf http://localhost:5001/health
wait_for "kafka-connect"  curl -sf http://localhost:8083/connector-plugins

if (( failed == 0 )); then
  result=$($COMPOSE exec -T trino trino --output-format TSV --execute "
    CREATE SCHEMA IF NOT EXISTS iceberg.smoke;
    DROP TABLE IF EXISTS iceberg.smoke.ping;
    CREATE TABLE iceberg.smoke.ping (id INT);
    INSERT INTO iceberg.smoke.ping VALUES (1);
    SELECT count(*) FROM iceberg.smoke.ping;
    DROP TABLE iceberg.smoke.ping;
    DROP SCHEMA iceberg.smoke;" 2>&1)
  if grep -qx "1" <<< "$result"; then
    echo "OK    iceberg round trip (create, insert, select, drop)"
  else
    echo "FAIL  iceberg round trip:"; echo "$result" | tail -5; failed=1
  fi
fi

exit $failed
