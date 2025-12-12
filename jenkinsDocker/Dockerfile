FROM ubuntu:24.04

# Install Python and pip
RUN apt update && apt -y install python3 python3-pip

# Copy requirements and install Python dependencies
COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . /app

# Expose port if your app runs on it
EXPOSE 80

# Default command (adjust if needed)
CMD ["python3"]

