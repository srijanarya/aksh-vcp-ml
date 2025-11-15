# Open Port 8002 on AWS LightSail - Step-by-Step Guide

**Required Action**: Configure AWS LightSail security group to allow external access to ML API on port 8002

**Current Status**:
- ✅ ML API running on port 8002 (internal access working)
- ❌ Port 8002 not accessible externally
- Instance: 13.200.109.29

---

## Method 1: AWS Console (Recommended - 2 minutes)

### Step 1: Login to AWS LightSail Console
1. Go to https://lightsail.aws.amazon.com/
2. Login with your AWS credentials
3. Select the correct region (appears to be Mumbai `ap-south-1` based on IP)

### Step 2: Find Your Instance
1. Click on "Instances" in the left sidebar
2. Look for your instance (IP: 13.200.109.29)
3. Click on the instance name to open details

### Step 3: Open Networking Tab
1. Click on the "Networking" tab at the top
2. Scroll down to "IPv4 Firewall" section
3. You'll see existing rules (SSH on port 22, possibly 8001 for VCP API)

### Step 4: Add Custom Port Rule
1. Click "+ Add rule" button
2. Configure the new rule:
   - **Application**: Custom
   - **Protocol**: TCP
   - **Port or range**: `8002`
   - **Restrict to IP address**: Leave blank for "Any IPv4 address" (0.0.0.0/0)
     - OR specify your specific IP for security
3. Click "Create" or "Save"

### Step 5: Verify
Wait 30 seconds, then test from your local machine:
```bash
curl http://13.200.109.29:8002/health
```

Expected response:
```json
{"status":"healthy","timestamp":"...","version":"1.0.0"}
```

---

## Method 2: AWS CLI (If Available)

### Install AWS CLI
```bash
# macOS
brew install awscli

# Configure
aws configure
```

### Open Port
```bash
aws lightsail open-instance-public-ports \
  --port-info fromPort=8002,toPort=8002,protocol=TCP \
  --instance-name <your-instance-name>
```

### Verify
```bash
aws lightsail get-instance-port-states --instance-name <your-instance-name>
```

---

## Method 3: SSH Tunnel (Temporary Solution)

If you need immediate access while waiting to configure the security group:

```bash
# Create SSH tunnel (run in a separate terminal)
ssh -i ~/.ssh/lightsail.pem -L 8002:localhost:8002 ubuntu@13.200.109.29

# Then access locally
curl http://localhost:8002/health
```

This creates a secure tunnel, but closes when you disconnect.

---

## Security Considerations

### Option A: Open to Public (Development/Testing)
- **Port**: 8002
- **Source**: 0.0.0.0/0 (Any IPv4)
- **Use Case**: Development, testing, public API
- **Risk**: Medium - API has no authentication
- **Recommendation**: Add API key authentication before production

### Option B: Restrict to Your IP (More Secure)
- **Port**: 8002
- **Source**: Your specific IP (e.g., 203.0.113.1/32)
- **Use Case**: Private testing, internal tools
- **Risk**: Low
- **How to find your IP**: Visit https://whatismyipaddress.com/

### Option C: VPC Only (Most Secure)
- Keep port closed externally
- Access only via SSH tunnel or VPN
- **Use Case**: Internal services, staging environments
- **Risk**: Minimal

---

## After Opening Port - Immediate Tests

### 1. Health Check
```bash
curl http://13.200.109.29:8002/health
```

### 2. API Documentation
Open in browser:
```
http://13.200.109.29:8002/docs
```

### 3. Make a Prediction
```bash
curl -X POST http://13.200.109.29:8002/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{"symbol": "RELIANCE"}'
```

### 4. List Models
```bash
curl http://13.200.109.29:8002/api/v1/models
```

---

## Troubleshooting

### Port Still Not Accessible After Opening

**Check 1**: Verify service is running
```bash
ssh -i ~/.ssh/lightsail.pem ubuntu@13.200.109.29 'sudo systemctl status vcp-ml-api'
```

**Check 2**: Verify internal access works
```bash
ssh -i ~/.ssh/lightsail.pem ubuntu@13.200.109.29 'curl http://localhost:8002/health'
```

**Check 3**: Check Ubuntu firewall (ufw)
```bash
ssh -i ~/.ssh/lightsail.pem ubuntu@13.200.109.29 'sudo ufw status'
```

If ufw is active and blocking:
```bash
ssh -i ~/.ssh/lightsail.pem ubuntu@13.200.109.29 'sudo ufw allow 8002/tcp'
```

**Check 4**: Verify LightSail firewall was updated
- Go back to AWS Console > Networking tab
- Confirm the rule appears in the list
- Check the protocol is TCP (not UDP)
- Verify port number is exactly 8002

---

## Next Steps After Port is Open

1. ✅ Test all API endpoints externally
2. Add API key authentication
3. Setup rate limiting
4. Configure HTTPS/SSL (recommended for production)
5. Setup monitoring and alerting
6. Deploy actual ML models (currently using placeholder)

---

## Production Checklist

Before opening to public internet in production:

- [ ] Add authentication (API keys, JWT tokens)
- [ ] Implement rate limiting
- [ ] Setup HTTPS with SSL certificate
- [ ] Add request logging
- [ ] Configure CORS properly
- [ ] Add input validation
- [ ] Setup monitoring (Prometheus/Grafana)
- [ ] Create backup of databases
- [ ] Document API usage limits
- [ ] Test under load

---

## Quick Reference

| Task | Command |
|------|---------|
| Check API status | `ssh -i ~/.ssh/lightsail.pem ubuntu@13.200.109.29 'sudo systemctl status vcp-ml-api'` |
| View logs | `ssh -i ~/.ssh/lightsail.pem ubuntu@13.200.109.29 'sudo journalctl -u vcp-ml-api -f'` |
| Restart API | `ssh -i ~/.ssh/lightsail.pem ubuntu@13.200.109.29 'sudo systemctl restart vcp-ml-api'` |
| Test internal | `ssh -i ~/.ssh/lightsail.pem ubuntu@13.200.109.29 'curl localhost:8002/health'` |
| Test external | `curl http://13.200.109.29:8002/health` |

---

**Status**: ⏳ Waiting for manual AWS console action

Once completed, the ML API will be publicly accessible and ready for integration with your VCP alert system!
