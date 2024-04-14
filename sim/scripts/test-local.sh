#! /usr/bin/env bash

set -o errexit
set -o pipefail
set -o nounset

# move to project root
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd $script_dir
cd ..

docker-compose kill
docker-compose rm -f


if [ $(uname -s) = "Linux" ]; then
    echo "Remove __pycache__ files"
    sudo find . -type d -name __pycache__ -exec rm -r {} \+
fi

docker-compose build
docker-compose up -d db

while docker-compose exec -T db psql -a -U postgres -l | grep appeeeee; do
    sleep 0.1
done


migration/migrate migration/schema.sql
docker-compose up -d
docker-compose exec -T backend bash /app/tests-start.sh "$@"
