#! bin/bash

curl -X POST -H "Content-Type: application/json" \
    -d $WEBHOOK_PAYLOAD \
    $WEBHOOK_URL