#!/bin/bash
# Setup background extraction service for historical announcements

SERVER_IP="13.200.109.29"
USER="ubuntu"
KEY_PATH="$HOME/.ssh/lightsail.pem"

echo "🔧 Setting up continuous intelligence extraction service..."

ssh -i "$KEY_PATH" "$USER@$SERVER_IP" bash << 'EOF'
    # Create systemd service for continuous extraction
    sudo tee /etc/systemd/system/vcp-intelligence-extractor.service > /dev/null << 'SERVICE'
[Unit]
Description=VCP Intelligence Extraction Background Service
After=network.target vcp-intelligence.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/vcp-ml
ExecStart=/home/ubuntu/vcp-ml/venv/bin/python3 -c "
import time
import subprocess
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

while True:
    try:
        logger.info('Running extraction batch...')
        result = subprocess.run(
            ['python3', 'migrate_historical_announcements.py', '--extract', '100'],
            cwd='/home/ubuntu/vcp-ml',
            capture_output=True,
            text=True,
            timeout=600
        )

        if 'No announcements to process' in result.stdout:
            logger.info('All announcements processed! Sleeping for 1 hour...')
            time.sleep(3600)  # Check again in 1 hour for new announcements
        else:
            logger.info('Batch complete, waiting 30 seconds before next batch...')
            time.sleep(30)  # Brief pause between batches

    except subprocess.TimeoutExpired:
        logger.warning('Batch timed out, continuing...')
    except Exception as e:
        logger.error(f'Error: {e}, retrying in 60 seconds...')
        time.sleep(60)
"
Restart=always
RestartSec=60
StandardOutput=append:/home/ubuntu/vcp-ml/extraction_service.log
StandardError=append:/home/ubuntu/vcp-ml/extraction_service.log

[Install]
WantedBy=multi-user.target
SERVICE

    # Reload systemd and enable service
    sudo systemctl daemon-reload
    sudo systemctl enable vcp-intelligence-extractor
    sudo systemctl start vcp-intelligence-extractor

    echo "✅ Extraction service created and started"
    echo ""
    echo "Monitor with: sudo journalctl -u vcp-intelligence-extractor -f"
    echo "Check logs: tail -f /home/ubuntu/vcp-ml/extraction_service.log"
EOF

echo ""
echo "✅ Background extraction service is now running!"
echo "It will process 100 announcements every 30 seconds until complete."
