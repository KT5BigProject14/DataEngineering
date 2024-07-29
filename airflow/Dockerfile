# Use the official Apache Airflow image
FROM apache/airflow:2.9.2-python3.11

# Set the working directory
WORKDIR /opt/airflow

# Switch to root user to install dependencies
USER root

# Install Chrome and ChromeDriver
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    && wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && dpkg -i google-chrome-stable_current_amd64.deb || apt-get -fy install

# Install a specific version of ChromeDriver compatible with Chrome version 126
RUN wget -N https://storage.googleapis.com/chrome-for-testing-public/126.0.6478.182/linux64/chrome-linux64.zip \
    && unzip chrome-linux64.zip -d /usr/local/bin/ \
    && rm chrome-linux64.zip



# Switch back to the airflow user
USER airflow

# Copy the requirements file into the container
COPY requirements.txt .
COPY logo_data.pem .

USER root
RUN chmod +x /opt/airflow/logo_data.pem
USER airflow

# Install the required Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the dags folder into the container
COPY dags/ /opt/airflow/dags/

# Copy the entrypoint script
COPY entrypoint.sh /opt/airflow/entrypoint.sh

# Make the entrypoint script executable
# RUN chmod +x /opt/airflow/entrypoint.sh

# Expose the port
EXPOSE 8080

# Set the entry point to the custom entrypoint script
ENTRYPOINT ["/opt/airflow/entrypoint.sh"]
