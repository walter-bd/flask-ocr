# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app

COPY ./requirements.txt /app

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt


RUN apt-get update && apt-get install poppler-utils ffmpeg libsm6 libxext6 -y

COPY . /app


# Expose port 80 for the Flask app

EXPOSE 80

# Run the command to start the Flask app when the container launches
CMD ["python", "app.py"]
