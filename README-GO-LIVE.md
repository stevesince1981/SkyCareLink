# MediFly GO LIVE CHECKLIST

## Pre-Launch Configuration

### 1. Environment Setup
- [ ] Set `env=prod` in `/data/config.json`
- [ ] Verify database connections are production-ready
- [ ] Confirm all secrets are properly configured

### 2. Feature Flags
- [ ] Turn on `email_enabled` flag if email service ready
- [ ] Turn on `sms_enabled` flag if SMS service ready  
- [ ] Confirm `training_mode=false` in production

### 3. Content Verification
- [ ] Verify announcements are appropriate for production
- [ ] Check all banners and notifications
- [ ] Confirm pricing displays are accurate

### 4. Financial Systems
- [ ] Verify invoices path and ACH export functionality
- [ ] Test commission calculation system
- [ ] Confirm payment processing integration

### 5. Security & Monitoring
- [ ] Confirm MFA and security systems operational
- [ ] Verify rate limiting is properly configured
- [ ] Test anomaly detection alerts
- [ ] Confirm `/healthz` endpoint responding

### 6. Data & Backups
- [ ] Run full backup before go-live
- [ ] Verify backup restoration process
- [ ] Confirm audit logging is active

### 7. Final Checks
- [ ] Test all critical user flows end-to-end
- [ ] Verify admin controls and dashboards
- [ ] Confirm affiliate portal functionality
- [ ] Test quote distribution fairness system

## Go-Live Commands

```bash
# Update environment
echo '{"env":"prod","flags":{"training_mode":false,"email_enabled":true,"sms_enabled":true}}' > data/config.json

# Verify health
curl /healthz

# Run final backup
# Use Admin → "Run Backup Now" button
```

## Post-Launch Monitoring

- Monitor `/data/error_log.json` for issues
- Check security logs for anomalies  
- Verify commission calculations
- Monitor quote distribution fairness
- Track user engagement metrics

## Rollback Plan

- Change `env=staging` in config.json
- Use Replit rollback feature if needed
- Restore from backup if database issues occur