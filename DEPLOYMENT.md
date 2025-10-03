# Deployment Guide

This guide covers how to deploy the Amadeus Hotels MCP Server using Docker on various platforms.

## Quick Start

### Local Docker Deployment

1. **Build and run with Docker Compose:**
   ```bash
   # Copy environment file
   cp env.example .env
   # Edit .env with your Amadeus API credentials
   nano .env
   
   # Build and run with Docker Compose
   docker-compose up --build
   ```

2. **Or build and run manually:**
   ```bash
   # Build the image
   docker build -t amadeus-hotels-mcp .
   
   # Run with environment variables
   docker run -d \
     -p 3000:3000 \
     -e AMADEUS_API_KEY=your_api_key \
     -e AMADEUS_API_SECRET=your_api_secret \
     --name amadeus-hotels-server \
     amadeus-hotels-mcp
   ```

3. **Test the deployment:**
   ```bash
   curl http://localhost:3000/mcp
   ```

## Render Deployment

### Option 1: Using render.yaml (Recommended)

1. **Push your code to GitHub** (make sure all files are committed)

2. **Connect to Render:**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New +" → "New Web Service"
   - Connect your GitHub repository

3. **Configure Deployment:**
   - Render will automatically detect the `render.yaml` file
   - Or manually configure:
     - Build Command: `docker build -t amadeus-hotels .`
     - Start Command: (leave empty for Dockerfile CMD)
     - Use Dockerfile: Yes

4. **Set Environment Variables:**
   - `AMADEUS_API_KEY`: Your Amadeus API key
   - `AMADEUS_API_SECRET`: Your Amadeus API secret
   - `AMADEUS_BASE_URL`: `https://test.api.amadeus.com` (or production URL)

5. **Deploy:**
   - Click "Create Web Service"
   - Render will build and deploy your service

### Option 2: Manual Configuration

1. **Create Web Service** in Render dashboard
2. **Connect your GitHub repo**
3. **Configure:**
   - Runtime: Docker
   - Build Command: (leave empty)
   - Start Command: (leave empty)
   - Use Dockerfile: Yes
4. **Set Environment Variables** (same as above)
5. **Deploy**

## Other Platform Deployments

### Railway

1. **Create `railway.json`:**
   ```json
   {
     "build": {
       "builder": "dockerfile"
     },
     "deploy": {
       "startCommand": "docker run -p $PORT:3000 $IMAGE_NAME"
     }
   }
   ```

2. **Deploy via Railway CLI or dashboard**

### Fly.io

1. **Create `fly.toml`:**
   ```toml
   app = "amadeus-hotels-mcp"
   primary_region = "iad"
   
   [build]
   
   [http_service]
     internal_port = 3000
     force_https = true
   
   [[vm]]
     cpu_kind = "shared"
     cpus = 1
     memory_mb = 256
   ```

2. **Deploy:**
   ```bash
   fly deploy
   ```

### Heroku

1. **Create `Procfile`:**
   ```
   web: uvicorn src.main:app --host 0.0.0.0 --port $PORT
   ```

2. **Deploy via Heroku CLI or dashboard**

## Environment Variables

Required environment variables for all deployments:

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `AMADEUS_API_KEY` | Your Amadeus API key | `your_api_key_here` | Yes |
| `AMADEUS_API_SECRET` | Your Amadeus API secret | `your_api_secret_here` | Yes |
| `AMADEUS_BASE_URL` | Amadeus API base URL | `https://test.api.amadeus.com` | No (defaults to test) |
| `HOST` | Host to bind to | `0.0.0.0` | No (defaults to 0.0.0.0) |
| `PORT` | Port to bind to | `3000` | No (defaults to 3000) |
| `LOG_LEVEL` | Logging level | `INFO` | No (defaults to INFO) |

## Security Considerations

### Production Environment Variables

For production deployments:

1. **Use Production Amadeus URL:**
   ```
   AMADEUS_BASE_URL=https://api.amadeus.com
   ```

2. **Secure API Credentials:**
   - Never commit credentials to version control
   - Use secure environment variable storage
   - Consider using secrets management for sensitive data

3. **HTTPS Enforcement:**
   - Most platforms automatically provide SSL certificates
   - Ensure HTTPS is enforced at the platform/load balancer level

### Rate Limiting

Consider implementing rate limiting for production use:

- Amadeus APIs have rate limits
- Implement caching for frequent hotel searches
- Consider using Redis or similar for session storage

## Monitoring and Health Checks

The Dockerfile includes health checks that work with:
- Docker health check endpoints
- Kubernetes liveness/readiness probes
- Platform monitoring (Render, Railway, etc.)

Health check endpoint: `http://your-domain/mcp`

## Scaling Considerations

For production scaling:

1. **Container Resources:**
   - Start with 256MB RAM, 0.5 CPU
   - Monitor usage and scale accordingly

2. **Replica Sets:**
   - Use multiple replicas for availability
   - Use load balancers for distribution

3. **Database Integration:**
   - Consider adding a database for caching hotel data
   - Implement session persistence for better UX

## Troubleshooting

### Common Issues

1. **Build Failures:**
   ```
   ERROR: failed to solve: no matching manifest for linux/amd64
   ```
   - Solution: Ensure platform compatibility in Dockerfile

2. **Port Binding Issues:**
   ```
   ERROR: listen tcp :3000: bind: address already in use
   ```
   - Solution: Check if port is configured correctly in platform

3. **Environment Variable Issues:**
   ```
   ERROR: AMADEUS_API_KEY not found
   ```
   - Solution: Verify environment variables are set correctly

### Debug Commands

```bash
# Check container logs
docker logs amadeus-hotels-server

# Check health status
docker inspect amadeus-hotels-server --format='{{.State.Health.Status}}'

# Shell into container
docker exec -it amadeus-hotels-server bash

# Check environment variables
docker exec amadeus-hotels-server printenv | grep AMADEUS
```

## Performance Optimization

### Docker Image Optimization

1. **Multi-stage builds** (already included)
2. **Layer caching** optimization
3. **Minimal base image** (python:3.11-slim)

### Runtime Optimization

1. **Enable Python optimizations:**
   ```
   PYTHONOPTIMIZE=1
   ```

2. **Use production WSGI server:**
   - Current setup uses Uvicorn with Starlette
   - Consider Gunicorn with Uvicorn workers for production

3. **Caching strategies:**
   - Implement Redis for session caching
   - Cache frequently accessed hotel data
   - Use CDN for static assets

## Support

For deployment issues:
- Check the [Render Documentation](https://render.com/docs)
- Review Docker and platform-specific logs
- Refer to the main README.md for application details
