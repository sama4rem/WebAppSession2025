# Use an official lightweight Python image
FROM python:3.10

# Set the working directory in the container
WORKDIR /app

# Copy the application files to the container
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set the Flask app environment variable
ENV FLASK_APP=run.py
ENV FLASK_ENV=production

# Run Gunicorn server
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "run:app"]
