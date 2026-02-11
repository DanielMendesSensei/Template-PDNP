FROM python:3.12-slim

WORKDIR /app

# Copy the django_clamav package
COPY .. /app/django_clamav_pkg/
COPY requirements.txt /app/
COPY app.py /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set Python path to include the parent package
ENV PYTHONPATH="/app/django_clamav_pkg/.."

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
