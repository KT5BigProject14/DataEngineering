#!/bin/bash
# Initialize the Airflow database
airflow db init

# Create an admin user
airflow users create \
    --username ${_AIRFLOW_WWW_USER_USERNAME:-airflow} \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com \
    --password ${_AIRFLOW_WWW_USER_PASSWORD:-airflow}

# Start the scheduler and webserver
airflow scheduler &
exec airflow webserver
