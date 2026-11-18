#!/bin/bash
for db in postiz postiz-db-local; do
  docker exec twenty-db psql -U postgres -d "$db" -c 'SELECT id, name, identifier, profile, "internalId", disabled FROM "Integration" WHERE "providerIdentifier"='"'"'facebook'"'"' OR identifier='"'"'facebook'"'"';' 2>&1 | head -n 10
done
grep -rln "facebook.com/techstarz101" /var/www/ 2>/dev/null | head -n 20

