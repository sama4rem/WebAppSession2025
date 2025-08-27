# Heartbeat pour Supabase
$env:DATABASE_URL="postgresql://postgres.tvoycwfakcxfkqysoaya:sama4rem%40Supabase@aws-1-eu-west-3.pooler.supabase.com:5432/postgres"

psql $env:DATABASE_URL -c "SELECT 1;"
