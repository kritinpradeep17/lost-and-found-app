FROM python:3.9

# Set the working directory in the container
WORKDIR /app

# Copy everything into the container
COPY . .

# Install dependencies
RUN pip install -r requirements.txt

# Expose the Flask port
EXPOSE 5000

# Command to run your app
CMD ["python", "app.py"]
