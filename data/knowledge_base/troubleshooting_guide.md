# System Troubleshooting Guide

## Database Issues

### Connection Pool Exhausted
**Symptoms:**
- "Connection pool exhausted" error
- Timeouts on database operations
- Application hanging

**Root Cause:**
- Usually caused by Microservice-B not closing connections
- Known issue: #247

**Immediate Fix:**
```bash
# Restart affected service
kubectl restart deployment/service-b

# Check active connections
SELECT * FROM pg_stat_activity WHERE state = 'active';
```

**Permanent Fix:**

- Deploy PR #456 (connection timeout middleware)
- Review code for unclosed connections

**Related Incidents:**

- Dec 15, 2025: Same issue, fixed by adding connection timeout

---

### Slow Queries

**Symptoms:**

- API response time > 2 seconds
- Database CPU > 80%
- Query timeouts

**Common Causes:**

1. Missing indexes
2. Table scans on large tables
3. N+1 query problems

**Diagnostic Commands:**

```sql
-- Find slow queries
SELECT query, mean_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Check missing indexes
SELECT schemaname, tablename, attname
FROM pg_stats
WHERE n_distinct > 100
AND correlation < 0.1;

```

**Fix:**

```sql
-- Add index
CREATE INDEX idx_table_column ON table_name(column_name);

-- Reindex if needed
REINDEX TABLE table_name;

```

---

## Authentication Issues

### JWT Token Expired

**Symptoms:**

- 401 Unauthorized errors
- Users logged out unexpectedly

**Root Cause:**

- JWT tokens expire after 1 hour
- Refresh token not implemented in client

**Fix:**

- Implement token refresh in frontend
- Use refresh tokens (expire after 7 days)

**Configuration:**

```
JWT_EXPIRY=3600        # 1 hour
REFRESH_EXPIRY=604800  # 7 days

```

---

### Session Timeout

**Symptoms:**

- Users logged out after inactivity

**Expected Behavior:**

- Session expires after 30 minutes of inactivity
- This is by design per security policy SEC-101

**User Education:**

- Inform users about 30-minute timeout
- Suggest using "Remember Me" for longer sessions

---

## Performance Issues

### High API Latency

**Symptoms:**

- API response time > 500ms
- Increased error rates
- User complaints

**Diagnostic Steps:**

1. Check database performance
2. Check external API calls
3. Check cache hit rate
4. Review recent deployments

**Monitoring Dashboards:**

- Grafana: http://grafana/api-health
- Datadog: http://datadog/services

**Common Fixes:**

1. Enable Redis caching
2. Optimize database queries
3. Add CDN for static assets
4. Scale horizontally (add more pods)

---

### Memory Leaks

**Symptoms:**

- Gradual memory increase
- OOM (Out of Memory) errors
- Pod restarts

**Investigation:**

```bash
# Check memory usage
kubectl top pods

# Get heap dump (Java)
kubectl exec -it pod-name -- jmap -dump:live,format=b,file=/tmp/heap.bin 1

# Analyze with tools
# - Java: Eclipse MAT
# - Node: Chrome DevTools
# - Python: memory_profiler

```

**Known Issues:**

- Service-A: Memory leak in PDF generation (fixed in v2.3.4)
- Service-C: WebSocket connections not cleaned up (PR #789)

---

## Deployment Issues

### Pod Crash Loop

**Symptoms:**

- Pod restarts repeatedly
- Status: CrashLoopBackOff

**Common Causes:**

1. Missing environment variables
2. Failed health checks
3. Port conflicts
4. Database connection failures

**Debug:**

```bash
# Check pod logs
kubectl logs pod-name

# Describe pod for events
kubectl describe pod pod-name

# Check env vars
kubectl exec -it pod-name -- env

```

---

### Migration Failed

**Symptoms:**

- Database migration errors
- Application won't start

**Recovery:**

```bash
# Rollback migration
npm run migrate:rollback

# Or manually fix
psql -h db-host -d dbname -f rollback.sql

# Redeploy previous version
kubectl rollout undo deployment/service-name

```

---

## Network Issues

### API Gateway Timeout

**Symptoms:**

- 504 Gateway Timeout
- Requests taking > 30 seconds

**Investigation:**

1. Check downstream service health
2. Review nginx/ingress logs
3. Check for network partitions

**Temporary Fix:**

```bash
# Increase timeout (nginx)
kubectl edit configmap nginx-config
# Set: proxy_read_timeout 60s;

```

---

## Escalation

**On-Call Contacts:**

- Database Team: @john-db (Slack)
- Backend Team: @sarah-backend (Slack)
- DevOps Team: @mike-devops (Slack)

**Escalation Path:**

1. Check runbook (this document)
2. Contact on-call engineer
3. If not resolved in 15 min → Page team lead
4. If critical + not resolved in 30 min → Page VP Engineering

**Incident Management:**

- Create Jira ticket: INC-XXXX
- Update status page: [https://status.company.com](https://status.company.com/)
- Post in #incidents Slack channel

```