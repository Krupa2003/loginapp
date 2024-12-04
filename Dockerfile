# Use the official Python base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements.txt to the working directory
COPY requirements.txt .

# Install the dependencies from the requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire backend folder to the working directory inside the container
COPY ./backend ./backend

# Expose port 8000 for FastAPI to listen on
EXPOSE 8000

# Define the command to run the FastAPI app using Uvicorn
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
