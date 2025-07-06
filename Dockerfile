# Dockerfile

# 1. Use an official Python runtime as a parent image
# Using 'slim' is a good practice for smaller image sizes
FROM python:3.11-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy the dependencies file first
# This leverages Docker's layer caching. This step will only be re-run
# if requirements.txt changes, speeding up future builds.
COPY requirements.txt .

# 4. Install the dependencies
# --no-cache-dir keeps the image size smaller
# --upgrade pip ensures we have the latest version
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of your application code into the container
COPY . .

# 6. Expose the port the app will run on
# This is documentation for the user; it doesn't actually open the port.
# The port is opened with the -p flag in the `docker run` command.
EXPOSE 8000

# 7. Define the command to run your application
# We run uvicorn directly.
# --host 0.0.0.0 makes the app accessible from outside the container.
# --port 8000 matches the port we exposed.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
