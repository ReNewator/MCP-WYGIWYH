# WYGIWYH API MCP Server


A production-ready Model Context Protocol (MCP) server that provides a universal interface to the WYGIWYH expense tracking API. The server dynamically generates 75 MCP tools from an OpenAPI specification, enabling AI agents and automation platforms like n8n to interact with the expense tracking system through standardized tool calls.

## ✨ Features

- 🔄 **Dynamic Tool Generation** - Automatically generates 75 MCP tools from OpenAPI specification
- 🔐 **Secure Authentication** - Bearer token authentication for MCP endpoints + Basic Auth for API access
- 🚀 **HTTP Streamable Transport** - Full compatibility with n8n and other MCP clients
- 🐳 **Production-Ready Docker** - Optimized multi-stage build with health checks
- ⚡ **Async/Await** - Efficient non-blocking API communication
- 📊 **Comprehensive API Coverage** - All WYGIWYH API endpoints exposed as tools

## 🎯 Use Cases

- Automate expense tracking workflows with n8n
- Build AI assistants that manage financial data
- Create custom integrations with WYGIWYH API
- Implement voice-controlled expense logging
- Develop automated reporting systems

## 📦 Quick Start

### Prerequisites

- Docker & Docker Compose
- WYGIWYH API credentials
- MCP Bearer token

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/ReNewator/MCP-WYGIWYH.git
   cd MCP-WYGIWYH
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. **Deploy with Docker**
   ```bash
   ./deploy.sh
   ```

   Or manually:
   ```bash
   docker-compose up -d
   ```

4. **Verify deployment**
   ```bash
   curl http://localhost:5000/health
   ```

## 🔧 Configuration

Create a `.env` file with the following variables:

```env
# WYGIWYH API Credentials
API_USERNAME=your_email@example.com
API_PASSWORD=your_password_here

# MCP Server Authentication
MCP_TOKEN=your_mcp_bearer_token_here
```

## 🌐 n8n Integration

Configure the n8n MCP Client node:

- **Endpoint:** `http://your-server:5000/`
- **Transport:** HTTP Streamable
- **Authentication:** Header Auth
  - Name: `Authorization`
  - Value: `Bearer YOUR_MCP_TOKEN`

## 🛠️ Available Tools

The server exposes **75 MCP tools** organized by category:

### Account Management
- `account-groups_*` - Account group operations (6 tools)
- `accounts_*` - Account CRUD operations (6 tools)

### Transaction Management
- `transactions_*` - Transaction operations (6 tools)
- `recurring-transactions_*` - Recurring transaction management (6 tools)
- `installment-plans_*` - Installment plan handling (6 tools)

### Financial Tools
- `categories_*` - Expense category management (6 tools)
- `tags_*` - Transaction tagging (6 tools)
- `currencies_*` - Currency management (6 tools)
- `exchange-rates_*` - Exchange rate operations (6 tools)

### Investment Features
- `dca_*` - Dollar-cost averaging strategies (15 tools)
- `entities_*` - Entity management (6 tools)

Use the `tools/list` method to see all available tools with their schemas.

## 📁 Project Structure

```
.
├── mcp_sse_server.py      # Main MCP server with HTTP Streamable
├── server.py              # Core MCP implementation
├── test_server.py         # Validation script
├── Dockerfile             # Production Docker image
├── docker-compose.yml     # Docker Compose config
├── deploy.sh              # Automated deployment
├── requirements.txt       # Python dependencies
├── DEPLOYMENT.md          # Detailed deployment guide
├── PROJECT.md             # Technical documentation
└── attached_assets/
    └── WYGIWYH API.yaml   # OpenAPI specification
```

## 🚀 Deployment

### Docker (Recommended)

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop server
docker-compose down
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: wygiwyh-mcp-server
spec:
  replicas: 2
  template:
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
```

### Cloud Platforms

- **AWS ECS/Fargate** - Use the Docker image with environment variables
- **Google Cloud Run** - Deploy as container with secrets management
- **Azure Container Instances** - Direct deployment from Docker Hub

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed cloud deployment instructions.

## 🧪 Testing

Run the validation script to verify the setup:

```bash
python test_server.py
```

This displays all 75 generated MCP tools grouped by category.

## 📊 API Endpoints

- `POST /` - MCP JSON-RPC endpoint (requires Bearer token)
- `GET /health` - Health check (no authentication)

## 🔒 Security Features

- ✅ Bearer token authentication for MCP access
- ✅ Basic Auth for WYGIWYH API requests
- ✅ Non-root container user
- ✅ Secrets managed via environment variables
- ✅ No exposed credentials in logs

## 🏗️ Architecture

### Dynamic Tool Generation

The server automatically generates MCP tools from the OpenAPI specification:

1. Parses WYGIWYH API OpenAPI YAML
2. Converts schemas to JSON Schema format
3. Creates Tool objects for all operations
4. Handles `allOf` merging for complex types
5. Exposes tools via MCP protocol

**Benefits:**
- Single source of truth (OpenAPI spec)
- Automatic updates when API changes
- Zero manual endpoint definitions
- Consistent tool schemas

### Authentication Flow

```
┌─────────────┐     Bearer Token     ┌─────────────┐
│   n8n/MCP   │ ──────────────────> │  MCP Server │
│   Client    │                      │             │
└─────────────┘                      └─────────────┘
                                            │
                                            │ Basic Auth
                                            ▼
                                     ┌─────────────┐
                                     │  WYGIWYH    │
                                     │     API     │
                                     └─────────────┘
```

## 🐛 Troubleshooting

### Server won't start

```bash
# Check logs
docker-compose logs

# Verify environment
cat .env
```

### Authentication errors

- Ensure `API_USERNAME` is your WYGIWYH email
- Verify `API_PASSWORD` is correct
- Check `MCP_TOKEN` matches client configuration

### Connection refused

```bash
# Check server status
docker-compose ps

# Test health endpoint
curl http://localhost:5000/health
```

## 📚 Documentation

- [DEPLOYMENT.md](DEPLOYMENT.md) - Comprehensive deployment guide
- [PROJECT.md](PROJECT.md) - Technical architecture documentation

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## 📄 License

Copyright (c) 2025 ReNewator.com. All rights reserved.

## 🔗 Links

- [WYGIWYH API Documentation](https://fin.vigitix.com/api/docs/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [n8n Automation](https://n8n.io/)

## 💬 Support

For issues and questions:
- Open an issue on GitHub
- Check existing documentation
- Review deployment logs

---

**Built with ❤️ by ReNewator.com**
