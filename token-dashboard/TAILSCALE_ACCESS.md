# Tailscale Access Guide

## Dashboard Access

Your Token Dashboard is now running and accessible via Tailscale:

### Direct Tailscale IP
```
http://100.81.239.69:8081
```

### Tailscale Machine Name
```
http://nicholass-laptop:8081
```

## For HTTPS/Funnel Access (Optional)

To get a proper HTTPS URL via Tailscale Funnel:

```bash
# Enable funnel (requires Tailscale admin approval)
tailscale funnel --bg 8081

# Then access at:
# https://nicholass-laptop.<your-tailnet>.ts.net
```

## Dashboard Features

- **Real-time token usage tracking**
- **Budget forecasting with daily recommendations**
- **Visual charts**: Daily costs, token trends, provider breakdown
- **Quota monitoring**: Progress bars for provider limits
- **Auto-refresh**: Updates every 60 seconds

## Local Access

```
http://localhost:8081
```

## Data Source

Dashboard reads from: `~/.openclaw/token-tracker/`
- Updates automatically as token-tracker logs usage
- No configuration needed

## Management Commands

```bash
# View logs
docker-compose logs -f

# Restart
docker-compose restart

# Stop
docker-compose down

# Update
docker-compose pull && docker-compose up -d
```
