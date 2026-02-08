#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask web server to display inventory check status
"""

from flask import Flask, render_template_string
import os
from datetime import datetime

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Inventory Check Status</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            border-bottom: 2px solid #007bff;
            padding-bottom: 10px;
        }
        .status {
            font-size: 18px;
            margin: 20px 0;
        }
        .timestamp {
            font-size: 24px;
            color: #007bff;
            font-weight: bold;
            margin: 20px 0;
        }
        .last-updated {
            color: #666;
            font-style: italic;
        }
        .running {
            color: #28a745;
        }
        .not-running {
            color: #dc3545;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Roli TradeAds Bot - Inventory Check Status</h1>
        
        {% if last_run %}
        <div class="status running">
            <strong>Status:</strong> Active ✓
        </div>
        <div class="timestamp">
            Last Run: {{ last_run }}
        </div>
        {% else %}
        <div class="status not-running">
            <strong>Status:</strong> Not yet started
        </div>
        <div class="timestamp">
            Waiting for first run...
        </div>
        {% endif %}
        
        <div class="last-updated">
            Page updated: {{ current_time }}
        </div>
    </div>
</body>
</html>
"""

def read_last_run_time():
    """Read the last run timestamp from file"""
    try:
        if os.path.exists('last_run.txt'):
            with open('last_run.txt', 'r') as f:
                return f.read().strip()
    except Exception as e:
        print(f"Error reading last run time: {e}")
    return None

@app.route('/')
def index():
    """Display the inventory check status page"""
    last_run = read_last_run_time()
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    return render_template_string(
        HTML_TEMPLATE,
        last_run=last_run,
        current_time=current_time
    )

@app.route('/health')
def health():
    """Health check endpoint for Heroku"""
    return {"status": "ok"}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
