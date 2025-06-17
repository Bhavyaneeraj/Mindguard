# Use a base image with Python and required tools
FROM python:3.10-slim


# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
  && apt-get install -y build-essential libpq-dev python3-dev curl git

# Install distutils manually (missing in slim)
RUN apt-get install -y python3-distutils

# Copy project files to container
COPY . /app/

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Collect static files (optional)
RUN python manage.py collectstatic --noinput

# Run migrations
RUN python manage.py migrate

# Expose port 8000
EXPOSE 8000

# Start the Django server using gunicorn
CMD ["gunicorn", "browser_tracker.wsgi:application", "--bind", "0.0.0.0:8000"]
