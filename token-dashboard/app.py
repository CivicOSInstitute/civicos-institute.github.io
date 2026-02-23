#!/usr/bin/env python3
"""
Token Dashboard - Web UI for token-tracker data
"""

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from collections import defaultdict

from flask import Flask, render_template, jsonify
import plotly.graph_objs as go
import plotly.utils
import pandas as pd

app = Flask(__name__)

# Custom template filters
@app.template_filter('intcomma')
def intcomma_filter(value):
    """Format integer with commas."""
    try:
        return "{:,}".format(int(value))
    except (ValueError, TypeError):
        return value

DATA_DIR = Path(os.environ.get('DATA_DIR', os.path.expanduser('~/.openclaw/token-tracker')))

def load_token_log():
    """Load token usage log."""
    log_file = DATA_DIR / 'token_log.jsonl'
    entries = []
    if log_file.exists():
        with open(log_file) as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))
    return entries

def load_config():
    """Load config with budgets and quotas."""
    config_file = DATA_DIR / 'config.json'
    if config_file.exists():
        with open(config_file) as f:
            return json.load(f)
    return {'budget': {}, 'quotas': {}, 'pricing': {}}

def get_usage_stats(entries, days=30):
    """Calculate usage statistics (local-first aware)."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    daily_usage = defaultdict(lambda: {'tokens': 0, 'cost': 0, 'calls': 0})
    provider_usage = defaultdict(lambda: {'tokens': 0, 'cost': 0, 'calls': 0})
    model_usage = defaultdict(lambda: {'tokens': 0, 'cost': 0, 'calls': 0})

    total_tokens = 0
    total_cost = 0
    local_calls = 0
    api_calls = 0

    for entry in entries:
        try:
            entry_time = datetime.fromisoformat(entry['timestamp'])
        except Exception:
            continue
        if entry_time < cutoff:
            continue

        day = entry_time.strftime('%Y-%m-%d')
        provider = (entry.get('provider') or 'unknown').lower()
        model = f"{provider}/{entry.get('model', 'unknown')}"
        tokens = int(entry.get('total_tokens', 0) or 0)
        cost = float(entry.get('cost_usd', 0) or 0)

        daily_usage[day]['tokens'] += tokens
        daily_usage[day]['cost'] += cost
        daily_usage[day]['calls'] += 1

        provider_usage[provider]['tokens'] += tokens
        provider_usage[provider]['cost'] += cost
        provider_usage[provider]['calls'] += 1

        model_usage[model]['tokens'] += tokens
        model_usage[model]['cost'] += cost
        model_usage[model]['calls'] += 1

        if provider in ('ollama', 'local'):
            local_calls += 1
        else:
            api_calls += 1

        total_tokens += tokens
        total_cost += cost

    total_calls = local_calls + api_calls
    local_share = (local_calls / total_calls * 100) if total_calls else 0

    return {
        'daily': dict(daily_usage),
        'by_provider': dict(provider_usage),
        'by_model': dict(model_usage),
        'total_tokens': total_tokens,
        'total_cost': total_cost,
        'avg_daily_cost': total_cost / days if days > 0 else 0,
        'local_calls': local_calls,
        'api_calls': api_calls,
        'total_calls': total_calls,
        'local_share': round(local_share, 1)
    }

def get_current_month_usage(entries):
    """Get current month usage."""
    now = datetime.now(timezone.utc)
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    total_cost = 0
    total_tokens = 0
    
    for entry in entries:
        entry_time = datetime.fromisoformat(entry['timestamp'])
        if entry_time >= start_of_month:
            total_cost += entry.get('cost_usd', 0)
            total_tokens += entry['total_tokens']
    
    return {'cost': total_cost, 'tokens': total_tokens}

def get_today_usage(entries):
    """Get today's usage."""
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    
    total_cost = 0
    total_tokens = 0
    calls = 0
    
    for entry in entries:
        entry_time = datetime.fromisoformat(entry['timestamp'])
        if entry_time.strftime('%Y-%m-%d') == today:
            total_cost += entry.get('cost_usd', 0)
            total_tokens += entry['total_tokens']
            calls += 1
    
    return {'cost': total_cost, 'tokens': total_tokens, 'calls': calls}

def calculate_forecast(entries, monthly_budget):
    """Calculate budget forecast."""
    now = datetime.now(timezone.utc)
    
    # Days in current month
    if now.month == 12:
        next_month = now.replace(year=now.year + 1, month=1, day=1)
    else:
        next_month = now.replace(month=now.month + 1, day=1)
    days_in_month = (next_month - now.replace(day=1)).days
    days_remaining = days_in_month - now.day + 1
    
    # Current month usage
    current = get_current_month_usage(entries)
    
    # Daily average
    day_of_month = now.day
    avg_daily = current['cost'] / day_of_month if day_of_month > 0 else 0
    
    # Projections
    projected = avg_daily * days_in_month if avg_daily > 0 else current['cost']
    remaining = monthly_budget - current['cost']
    recommended_daily = remaining / days_remaining if days_remaining > 0 else 0
    
    return {
        'monthly_budget': monthly_budget,
        'current_spend': current['cost'],
        'remaining': remaining,
        'percent_used': (current['cost'] / monthly_budget * 100) if monthly_budget > 0 else 0,
        'days_remaining': days_remaining,
        'avg_daily': avg_daily,
        'projected_monthly': projected,
        'recommended_daily': recommended_daily,
        'on_track': projected <= monthly_budget
    }

@app.route('/')
def dashboard():
    """Main dashboard page."""
    entries = load_token_log()
    config = load_config()
    
    stats = get_usage_stats(entries, days=30)
    today = get_today_usage(entries)
    current_month = get_current_month_usage(entries)
    
    monthly_budget = config.get('budget', {}).get('monthly_limit', 100)
    forecast = calculate_forecast(entries, monthly_budget)
    
    # Prepare chart data
    daily_df = pd.DataFrame([
        {'date': k, 'tokens': v['tokens'], 'cost': v['cost'], 'calls': v['calls']}
        for k, v in sorted(stats['daily'].items())
    ])
    
    # Daily cost chart
    if not daily_df.empty:
        daily_cost_chart = go.Figure(data=[
            go.Bar(x=daily_df['date'], y=daily_df['cost'], name='Daily Cost ($)')
        ])
        daily_cost_chart.update_layout(
            title='Daily Cost (Last 30 Days)',
            xaxis_title='Date',
            yaxis_title='Cost ($)',
            template='plotly_white'
        )
        daily_cost_json = json.dumps(daily_cost_chart, cls=plotly.utils.PlotlyJSONEncoder)
        
        # Daily tokens chart
        daily_tokens_chart = go.Figure(data=[
            go.Bar(x=daily_df['date'], y=daily_df['tokens'], name='Daily Tokens', marker_color='green')
        ])
        daily_tokens_chart.update_layout(
            title='Daily Token Usage (Last 30 Days)',
            xaxis_title='Date',
            yaxis_title='Tokens',
            template='plotly_white'
        )
        daily_tokens_json = json.dumps(daily_tokens_chart, cls=plotly.utils.PlotlyJSONEncoder)
    else:
        daily_cost_json = '{}'
        daily_tokens_json = '{}'
    
    # Provider pie chart
    provider_data = stats['by_provider']
    if provider_data:
        provider_chart = go.Figure(data=[
            go.Pie(
                labels=list(provider_data.keys()),
                values=[v['cost'] for v in provider_data.values()],
                hole=0.4
            )
        ])
        provider_chart.update_layout(title='Cost by Provider')
        provider_json = json.dumps(provider_chart, cls=plotly.utils.PlotlyJSONEncoder)
    else:
        provider_json = '{}'
    
    # Model bar chart
    model_data = stats['by_model']
    if model_data:
        sorted_models = sorted(model_data.items(), key=lambda x: x[1]['cost'], reverse=True)[:10]
        model_chart = go.Figure(data=[
            go.Bar(
                x=[m[0] for m in sorted_models],
                y=[m[1]['cost'] for m in sorted_models]
            )
        ])
        model_chart.update_layout(
            title='Top Models by Cost',
            xaxis_title='Model',
            yaxis_title='Cost ($)',
            template='plotly_white'
        )
        model_json = json.dumps(model_chart, cls=plotly.utils.PlotlyJSONEncoder)
    else:
        model_json = '{}'
    
    # Top model by calls
    top_model = 'n/a'
    if stats['by_model']:
        top_model = sorted(stats['by_model'].items(), key=lambda x: x[1]['calls'], reverse=True)[0][0]

    # Quota status
    quotas = config.get('quotas', {})
    quota_status = []
    for provider, quota in quotas.items():
        # Calculate usage for this provider
        provider_tokens_today = sum(
            e['total_tokens'] for e in entries
            if e['provider'] == provider and 
            datetime.fromisoformat(e['timestamp']).strftime('%Y-%m-%d') == datetime.now(timezone.utc).strftime('%Y-%m-%d')
        )
        quota_status.append({
            'provider': provider,
            'daily_limit': quota.get('daily_limit', 'N/A'),
            'daily_used': provider_tokens_today,
            'daily_pct': (provider_tokens_today / quota['daily_limit'] * 100) if quota.get('daily_limit') else 0
        })
    
    return render_template('dashboard.html',
                         stats=stats,
                         today=today,
                         current_month=current_month,
                         forecast=forecast,
                         daily_cost_chart=daily_cost_json,
                         daily_tokens_chart=daily_tokens_json,
                         provider_chart=provider_json,
                         model_chart=model_json,
                         quota_status=quota_status,
                         top_model=top_model,
                         local_target=70,
                         config=config)

@app.route('/api/data')
def api_data():
    """API endpoint for raw data."""
    entries = load_token_log()
    config = load_config()
    
    return jsonify({
        'entries': entries[-100:],  # Last 100 entries
        'config': config,
        'stats': get_usage_stats(entries, days=30),
        'today': get_today_usage(entries),
        'forecast': calculate_forecast(entries, config.get('budget', {}).get('monthly_limit', 100))
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
