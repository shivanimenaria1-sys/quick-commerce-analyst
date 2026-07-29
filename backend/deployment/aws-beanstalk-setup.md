# AWS Elastic Beanstalk – Architecture & Setup Reference

## Architecture Overview

```
Internet
    │
    ▼
Route 53 (optional custom domain)
    │
    ▼
Application Load Balancer (ALB)  ← EB provisions this
    │  (HTTPS :443 → HTTP :8000)
    ▼
EC2 Instance (Amazon Linux 2023, Python 3.11)
    │
    ├── Procfile → uvicorn app.main:app --host 0.0.0.0 --port 8000
    ├── .ebextensions/ → OS packages, EB config
    └── /health → HTTP 200 (ALB health check target)
```

---

## Elastic Beanstalk Platform Versions

When running `eb init`, select exactly:

```
Platform:  Python
Version:   Python 3.11 running on 64bit Amazon Linux 2023
```

Do **not** select Amazon Linux 2 — it ships an older yum package tree that
may be missing some WeasyPrint dependencies.

---

## How EB Starts the Application

1. EB CLI zips the `backend/` directory (honouring `.gitignore`)
2. Uploads the zip to the EB S3 bucket
3. On the EC2 instance, EB:
   a. Runs `.ebextensions/02_packages.config` → installs yum packages
   b. Runs `.ebextensions/01_app.config` → applies env settings
   c. Runs `pip install -r requirements.txt`
   d. Reads `Procfile` → starts `uvicorn app.main:app --host 0.0.0.0 --port 8000`
4. The ALB polls `GET /health` every 15 seconds
5. After 3 consecutive HTTP 200 responses, the instance turns **Green**

---

## HTTPS Configuration (Recommended for Production)

EB handles HTTPS termination at the ALB level. The app itself only needs to
listen on HTTP port 8000.

### Steps

1. **Request an ACM certificate** in the same region as your EB environment:
   ```
   AWS Console → Certificate Manager → Request → Public Certificate
   ```
   Enter your domain (e.g. `api.yourdomain.com`). Validate via DNS or email.

2. **Attach the certificate to the EB load balancer**:
   ```
   EB Console → Environment → Configuration → Load Balancer
   → Add Listener → Port 443, Protocol HTTPS, Certificate: <your ACM ARn>
   ```

3. **Add a CORS_ORIGINS entry** for your HTTPS frontend:
   ```bash
   eb setenv CORS_ORIGINS="https://your-frontend.vercel.app"
   ```

4. The app already sets `X-Forwarded-Proto` trust via `TrustedHostMiddleware`,
   so redirect logic (if added later) will correctly detect HTTPS.

---

## Environment Properties Reference

Set all of these in:
`EB Console → Environment → Configuration → Software → Environment Properties`

```
GEMINI_API_KEY   = <your google ai api key>
CORS_ORIGINS     = https://your-frontend.vercel.app
APP_ENV          = production
PORT             = 8000
```

### Via CLI (recommended for automation)
```bash
eb setenv GEMINI_API_KEY="..." CORS_ORIGINS="https://..." APP_ENV="production"
```

---

## Scaling Configuration

```bash
# Set min/max instance count via CLI
eb scale 2  # immediately sets desired count to 2

# Or configure auto-scaling via EB Console:
# Configuration → Capacity → Auto Scaling → Min: 1, Max: 3
```

Recommended triggers:
- Scale up when CPU > 60% for 3 minutes
- Scale down when CPU < 20% for 10 minutes

---

## Deployment Slots / Blue-Green

To deploy without downtime:

```bash
# Clone current environment to a staging slot
eb clone quick-commerce-prod --clone_name quick-commerce-staging

# Deploy to staging first
eb use quick-commerce-staging
eb deploy

# Test staging, then swap URLs (zero downtime)
eb swap quick-commerce-prod --destination_name quick-commerce-staging
```

---

## Monitoring & Alarms

Enable Enhanced Health Reporting:
```
EB Console → Configuration → Monitoring → Health Reporting: Enhanced
```

Recommended CloudWatch alarms:
- `HealthyHostCount < 1` → notify immediately
- `HTTPCode_Target_5XX_Count > 10` in 5 min → notify
- `CPUUtilization > 80%` for 5 min → scale up

---

## S3 Bucket for Deployment Artifacts

EB automatically creates a bucket named:
```
elasticbeanstalk-<region>-<account-id>
```

Application versions are stored there. EB retains the last 200 versions by
default. Clean up old versions to control S3 costs:

```bash
# List versions
aws elasticbeanstalk describe-application-versions \
  --application-name quick-commerce-analyst

# Delete a specific version
aws elasticbeanstalk delete-application-version \
  --application-name quick-commerce-analyst \
  --version-label <label> \
  --delete-source-bundle
```
