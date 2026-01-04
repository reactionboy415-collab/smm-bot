# 1. Use an official Python runtime
FROM python:3.10-slim

# 2. Set the working directory
WORKDIR /app

# 3. Install system dependencies (optional but good for safety)
RUN apt-get update && apt-get install -y sqlite3 && rm -rf /var/lib/apt/lists/*

# 4. Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of the code
COPY . .

# 6. Create the data folder for your SQLite database
RUN mkdir -p /app/data

# 7. EXPOSE the port (Render uses 10000 by default)
# Note: This is only needed if you add a web server for health checks.
EXPOSE 10000

# 8. Start the bot
CMD ["python", "bot.py"]