# Use Python 3.7 as base image
FROM python:3.7

# Set environment variables
ENV PYTHONPATH=/opt/pipeline/:$PYTHONPATH
ENV PATH=/opt/pipeline/:$PATH

# Set working directory in container
WORKDIR /opt/pipeline

# Copy the requirements file into the container
COPY ./requirements.txt /opt/pipeline

# Upgrade pip and install required packages
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the entire project into the container
COPY ./ ./

# Make the pipeline script executable and create a symlink
RUN chmod +x /opt/pipeline/market_scout/scout.py && ln -s /opt/pipeline/market_scout/scout.py /usr/local/bin/scout

# Set etl/pipeline.py as the default command to execute
ENTRYPOINT ["python", "market_scout/scout.py"]