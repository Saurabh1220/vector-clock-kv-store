# Use Python 3.9 base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy only necessary files
COPY src/ /app/

# Install required Python packages
RUN pip install flask requests

# Expose the Flask port
EXPOSE 5000

# Run the node server
CMD ["python", "node.py"]
