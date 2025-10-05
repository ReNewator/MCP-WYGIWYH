# Production Deployment Guide

**Copyright (c) 2025 ReNewator.com**

## Quick Start

### 1. Prerequisites
- Docker & Docker Compose installed
- WYGIWYH API credentials
- MCP Bearer token for authentication

### 2. Configuration

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```env
API_USERNAME=your_email@example.com
API_PASSWORD=your_password_here
MCP_TOKEN=your_mcp_bearer_token_here
```

### 3. Deploy

Run the deployment script:

```bash
./deploy.sh
```

Or manually with Docker Compose:

```bash
docker-compose up -d
```

## Endpoints

- **Main endpoint:** `http://localhost:5000/`
- **Health check:** `http://localhost:5000/health`

## n8n Integration

Configure n8n MCP Client:
- **URL:** `http://your-server:5000/`
- **Transport:** HTTP Streamable
- **Authentication:** Header Auth
  - Name: `Authorization`
  - Value: `Bearer YOUR_MCP_TOKEN`

## Management Commands

```bash
# View logs
docker-compose logs -f

# Restart server
docker-compose restart

# Stop server
docker-compose down

# Rebuild and restart
docker-compose up -d --build

# View container status
docker-compose ps
```

## Production Considerations

### Security
- ✅ Runs as non-root user
- ✅ Bearer token authentication
- ✅ No exposed secrets in logs
- ✅ Health checks enabled

### Monitoring
- Health check endpoint: `/health`
- Docker health checks configured
- Automatic container restart on failure

### Performance
- Multi-stage Docker build
- Optimized Python dependencies
- Async/await request handling
- Connection pooling via httpx

## Cloud Deployment

### Docker Hub
```bash
# Tag image
docker tag wygiwyh-mcp-server:latest your-username/wygiwyh-mcp-server:latest

# Push to Docker Hub
docker push your-username/wygiwyh-mcp-server:latest
```

### AWS ECS / Azure Container Instances / Google Cloud Run

Use the built image with environment variables:
- `API_USERNAME`
- `API_PASSWORD`
- `MCP_TOKEN`

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: wygiwyh-mcp-server
spec:
  replicas: 2
  selector:
    matchLabels:
      app: wygiwyh-mcp-server
  template:
    metadata:
      labels:
        app: wygiwyh-mcp-server
    spec:
      containers:
      - name: mcp-server
        image: wygiwyh-mcp-server:latest
        ports:
        - containerPort: 5000
        env:
        - name: API_USERNAME
          valueFrom:
            secretKeyRef:
              name: wygiwyh-secrets
              key: api-username
        - name: API_PASSWORD
          valueFrom:
            secretKeyRef:
              name: wygiwyh-secrets
              key: api-password
        - name: MCP_TOKEN
          valueFrom:
            secretKeyRef:
              name: wygiwyh-secrets
              key: mcp-token
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 30
```

## Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose logs

# Verify .env file
cat .env
```

### Connection refused
```bash
# Check if container is running
docker-compose ps

# Check health
curl http://localhost:5000/health
```

### API authentication errors
- Verify `API_USERNAME` and `API_PASSWORD` are correct
- Ensure credentials are in correct order (email as username)

## Available Tools

The server exposes 75 MCP tools for WYGIWYH API:
- Account management (groups, accounts)
- Transaction management
- Categories & tags
- Currencies & exchange rates
- Recurring transactions & installments
- DCA strategies
- And more...

Use `tools/list` method to see all available tools.
