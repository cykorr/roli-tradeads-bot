# Roli TradeAds Bot

A bot for monitoring Roblox inventory changes and sending Discord notifications.

## Features

- Monitors Roblox player inventory using Rolimons API
- Sends Discord webhook notifications when items are added or removed
- Web dashboard showing last run time
- Heroku deployment ready

## Deployment to Heroku

### Prerequisites

- Heroku account
- Heroku CLI installed

### Setup Steps

1. Create a new Heroku app:
   ```bash
   heroku create your-app-name
   ```

2. Set the required environment variable:
   ```bash
   heroku config:set INVENTORY_WEBHOOK=your_discord_webhook_url
   ```

3. Deploy the application:
   ```bash
   git push heroku main
   ```

4. Scale the dynos:
   ```bash
   heroku ps:scale web=1 worker=1
   ```

5. View the dashboard:
   ```
   https://your-app-name.herokuapp.com
   ```

### Environment Variables

- `INVENTORY_WEBHOOK` - Discord webhook URL for notifications (required)
- `PORT` - Port for web server (automatically set by Heroku)

## Local Development

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set environment variables:
   ```bash
   export INVENTORY_WEBHOOK=your_discord_webhook_url
   ```

3. Run the web server:
   ```bash
   python app.py
   ```

4. Run the inventory checker (in a separate terminal):
   ```bash
   python inventory-check.py
   ```

5. Open browser to `http://localhost:5000`

## File Structure

- `app.py` - Flask web server for status dashboard
- `inventory-check.py` - Main inventory monitoring script
- `tradead.py` - Trade advertisement bot
- `config.json` - Configuration file
- `Procfile` - Heroku process definitions
- `requirements.txt` - Python dependencies
- `runtime.txt` - Python version specification

## How It Works

1. The `inventory-check.py` script runs continuously, checking for inventory changes every 61 seconds
2. Every time it runs, it updates a `last_run.txt` file with the current timestamp
3. The `app.py` web server reads this file and displays it on a webpage
4. Both processes run simultaneously on Heroku (web and worker dynos)
