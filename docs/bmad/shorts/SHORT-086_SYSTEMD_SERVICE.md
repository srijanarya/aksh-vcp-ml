# SHORT-086: Systemd Service Configuration

**Status**: 🔲 Not Started
**TDD Status**: N/A (Infrastructure)
**Iteration**: 1
**Category**: Production Deployment

## Problem
Need production-ready service management with auto-restart and logging.

## Solution
Systemd service configuration for Linux deployment.

## Implementation

### Service Features
1. **Auto-Start**: Starts on boot
2. **Auto-Restart**: Restarts on failure
3. **Logging**: Journald integration
4. **User Isolation**: Runs as dedicated user

### Service File

```ini
[Unit]
Description=VCP Trading System
After=network.target

[Service]
Type=simple
User=vcp
WorkingDirectory=/opt/vcp
Environment="PATH=/opt/vcp/venv/bin"
ExecStart=/opt/vcp/venv/bin/python -m src.main
Restart=on-failure
RestartSec=10s
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### Usage

```bash
# Install service
sudo cp vcp-trading.service /etc/systemd/system/
sudo systemctl daemon-reload

# Enable and start
sudo systemctl enable vcp-trading
sudo systemctl start vcp-trading

# Check status
sudo systemctl status vcp-trading

# View logs
sudo journalctl -u vcp-trading -f
```

## Test Requirements
- Service starts
- Auto-restart works
- Logging captured
- Manual stop/start

## Dependencies
- systemd (Linux only)

## Acceptance Criteria
- 🔲 Service definition complete
- 🔲 Auto-restart configured
- 🔲 Logging enabled
- 🔲 Documentation included
- N/A test coverage (infrastructure)

## Files
- Service: `/Users/srijan/Desktop/aksh/deployment/vcp-trading.service` (to create)
- Docs: `/Users/srijan/Desktop/aksh/deployment/README.md` (to create)
