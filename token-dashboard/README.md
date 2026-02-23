# Token Dashboard

A beautiful web dashboard for visualizing AI API token usage, costs, and quotas. Built with Flask and Plotly.

![Dashboard Preview](https://via.placeholder.com/800x400/0f172a/60a5fa?text=Token+Dashboard)

## Features

- **Real-time Metrics**: Today's usage, monthly spend, budget remaining
- **Budget Forecasting**: Projected monthly spend, recommended daily budget
- **Visual Charts**: Daily cost/token trends, provider breakdown, top models
- **Quota Tracking**: Visual progress bars for provider token limits
- **Dark Mode**: Easy-on-the-eyes dark UI
- **Auto-refresh**: Updates every 60 seconds
- **Mobile Responsive**: Works on all devices

## Quick Start

### Prerequisites

- Docker & docker-compose
- Tailscale (optional, for secure remote access)

### Installation

1. Navigate to the dashboard directory:
```bash
cd ~/.openclaw/workspace/token-dashboard
```

2. Run the setup script:
```bash
./setup.sh
```

Or manually:
```bash
docker-compose up --build -d
```

3. Access the dashboard:
- Local: http://localhost:8080

## Tailscale Access (Secure Remote)

### Option 1: Using Tailscale Serve (Recommended)

If Tailscale is installed on the host:

```bash
# Start the dashboard
docker-compose up -d

# Expose via Tailscale
tailscale serve --bg --set-path=/ localhost:8080

# Get your Tailscale URL
tailscale serve status
```

Access at: `https://<your-machine>.<tailnet-name>.ts.net/`

### Option 2: Using Tailscale Sidecar

1. Get your Tailscale auth key:
   - Go to https://login.tailscale.com/admin/settings/keys
   - Generate auth key (enable "Reusable" and "Ephemeral")

2. Set the auth key:
```bash
export TS_AUTHKEY=tskey-auth-xxx
```

3. Start with Tailscale sidecar:
```bash
docker-compose -f docker-compose.yml -f docker-compose.tailscale.yml up -d
```

Access at: `https://token-dashboard.<tailnet-name>.ts.net/`

## Dashboard Sections

### 📊 Budget Forecast
- Monthly budget vs current spend
- Days remaining in month
- Recommended daily spend to stay on budget
- Overspend warnings

### 💰 Key Metrics
- Today's usage (cost, tokens, API calls)
- This month's totals
- 30-day historical totals
- Average daily spend

### 📈 Charts
- **Daily Cost Trend**: Bar chart of daily spending (30 days)
- **Daily Token Usage**: Bar chart of daily token consumption
- **Cost by Provider**: Pie chart showing provider breakdown
- **Top Models**: Bar chart of most expensive models

### 📋 Quota Status
- Visual progress bars for each provider
- Daily token usage vs limits
- Color-coded warnings (green/yellow/red)

## API Endpoint

Raw data available at `/api/data`:

```bash
curl http://localhost:8080/api/data
```

Returns JSON with:
- Recent entries
- Usage stats
- Budget forecast
- Configuration

## Data Source

The dashboard reads from `~/.openclaw/token-tracker/`:
- `token_log.jsonl` — Usage history
- `config.json` — Budgets and quotas

Data is updated in real-time as token-tracker logs new entries.

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATA_DIR` | `/data` | Path to token-tracker data |
| `FLASK_ENV` | `production` | Flask environment |

### Docker Volumes

The container mounts your local token-tracker directory:
```yaml
volumes:
  - ~/.openclaw/token-tracker:/data:ro
```

## Commands

```bash
# Start dashboard
docker-compose up -d

# View logs
docker-compose logs -f

# Stop dashboard
docker-compose down

# Restart
docker-compose restart

# Update after code changes
docker-compose up --build -d
```

## Troubleshooting

### Dashboard shows no data
- Ensure token-tracker has logged entries: `tt status`
- Check volume mount: `docker-compose exec token-dashboard ls /data`

### Tailscale URL not working
- Verify Tailscale is running: `tailscale status`
- Check serve status: `tailscale serve status`
- Ensure MagicDNS is enabled in Tailscale admin

### Port already in use
Change port in `docker-compose.yml`:
```yaml
ports:
  - "8081:8080"  # Use 8081 instead
```

## Customization

### Change Refresh Interval
Edit `templates/dashboard.html`:
```javascript
setTimeout(() => location.reload(), 60000); // Change 60000 (ms)
```

### Add Custom Charts
Edit `app.py` to add new Plotly charts, then add corresponding HTML in `templates/dashboard.html`.

## Security Notes

- Dashboard is read-only (no write operations)
- Tailscale provides encrypted, authenticated access
- No authentication on local access (assumes trusted network)
- For public internet access, add a reverse proxy with auth

## Integration with token-tracker

The dashboard automatically reflects token-tracker data:

```bash
# Log some usage
tt log openai gpt-4o 1000 500

# View in dashboard (refresh or wait 60s)
open http://localhost:8080
```

## Files

```
token-dashboard/
├── app.py                      # Flask application
├── Dockerfile                  # Container definition
├── docker-compose.yml          # Standard compose
├── docker-compose.tailscale.yml # Tailscale sidecar
├── setup.sh                    # Setup script
├── requirements.txt            # Python deps
├── templates/
│   └── dashboard.html          # Main UI
└── README.md                   # This file
```
