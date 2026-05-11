#!/bin/sh

while ! python manage.py shell -c "from django.db import connection; connection.ensure_connection()" 2>/dev/null; do
    sleep 0.5
done

python manage.py migrate --noinput

python manage.py collectstatic --noinput

python manage.py shell <<EOF
import os
from infrastructure.admin import register_admin

print(register_admin(
  email=os.environ.get('ADMIN_EMAIL'),
  name=os.environ.get('ADMIN_NAME'),
  surname=os.environ.get('ADMIN_SURNAME'),
  password=os.environ.get('ADMIN_PASSWORD')
))
EOF

exec "$@"