FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy MCP server code
COPY . .

# Default environment variables
ENV BACKEND_API_URL=http://backend:8000

# Expose MCP server port (stdio-based, so no port needed but we document it)
# MCP servers typically run via stdio, but we'll support both

CMD ["python", "server.py"]
