#!/bin/bash

# docker compose -f docker-compose-ory-hydra.yml up -d
# docker compose -f docker-compose-ory-hydra.yml ps
# docker compose -f docker-compose-ory-hydra.yml down -v

# Register the client and capture JSON
code_client=$(docker compose -f docker-compose-ory-hydra.yml exec -T hydra \
    hydra create client \
    --endpoint http://127.0.0.1:4445 \
    --grant-type authorization_code,refresh_token \
    --response-type code,id_token \
    --format json \
    --scope openid,profile,email,offline \
    --redirect-uri http://localhost:5000/callback)

# Extract values with jq
NEW_ID=$(echo $code_client | jq -r '.client_id')
NEW_SECRET=$(echo $code_client | jq -r '.client_secret')

sed -i "s/^CLIENT_ID=.*/CLIENT_ID=$NEW_ID/" .env
sed -i "s/^CLIENT_SECRET=.*/CLIENT_SECRET=$NEW_SECRET/" .env

echo "-----------------------------------------------"
echo "CLIENT_ID: $NEW_ID"
echo "CLIENT_SECRET: $NEW_SECRET"
echo "-----------------------------------------------"