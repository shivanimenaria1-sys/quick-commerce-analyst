# Quick Commerce Analyst – AWS Elastic Beanstalk Deployment Guide

## Prerequisites

| Tool | Minimum Version | Install |
|---|---|---|
| AWS CLI | v2 | `pip install awscli` |
| EB CLI | v3.20+ | `pip install awsebcli` |
| Python | 3.11 | [python.org](https://python.org) |
| Git | any | [git-scm.com](https://git-scm.com) |

---

## Environment Variables — Required on Elastic Beanstalk

Set these in the EB Console → Environment → Configuration → Software → Environment Properties, or via `eb setenv`.

| Variable | Purpose | Example Value |
|---|---|---|
| `GEMINI_API_KEY` | Google Gemini AI API key. **Required at startup** — the app will refuse to start without it. | `AIza...` |
| `CORS_ORIGINS` | Comma-separated list of frontend origins allowed to call the API. In production, set this to your frontend domain only. | `https://your-frontend.vercel.app,https://www.yourdomain.com` |
| `APP_ENV` | Controls production mode. When set to `production`, disables `/docs`, `/redoc`, `/openapi.json` and removes localhost CORS origins. | `production` |
| `PORT` | Port uvicorn listens on. EB expects `8000`. Do not change unless you update the Procfile too. | `8000` |
| `PYTHONUNBUFFERED` | Forces Python stdout/stderr to flush immediately (shows logs in real time in EB log viewer). Set in `.ebextensions/01_app.config`. | `1` |
| `PYTHONDONTWRITEBYTECODE` | Prevents Python from writing `.pyc` cache files to the EB instance. Set in `.ebextensions/01_app.config`. | `1` |

### Setting environment variables via CLI

```bash
eb setenv \
  GEMINI_API_KEY="your-actual-key-here" \
  CORS_ORIGINS="https://your-frontend.vercel.app" \
  APP_ENV="production"
```

---

## Deployment Checklist

Run through every item before executing `eb deploy`.

- ✅ `requirements.txt` — all dependencies pinned with exact versions
- ✅ `Procfile` — `web: uvicorn app.main:app --host 0.0.0.0 --port 8000`
- ✅ `runtime.txt` — `python-3.11`
- ✅ Environment variables — set via `eb setenv` (especially `GEMINI_API_KEY`)
- ✅ Health endpoint — `GET /health` returns `{"status": "ok"}` with HTTP 200
- ✅ CORS — `CORS_ORIGINS` env var set to production frontend URL
- ✅ Startup command — app binds to `0.0.0.0:8000`, not `127.0.0.1`
- ✅ `.env` excluded — confirmed in `.gitignore`, secrets only in EB env props
- ✅ `APP_ENV=production` — disables debug docs, locks down dev origins
- ✅ `.ebextensions/` — OS packages (Cairo, Pango for WeasyPrint) installed

---

## Step-by-Step Deployment Commands

### 1. Configure AWS credentials

```bash
aws configure
```

Enter when prompted:
- **AWS Access Key ID** – from your IAM user
- **AWS Secret Access Key** – from your IAM user
- **Default region** – e.g. `ap-south-1` (Mumbai) or `us-east-1`
- **Default output format** – `json`

Verify:
```bash
aws sts get-caller-identity
```

---

### 2. Initialise the EB application (run once per machine)

Run from inside the `backend/` folder:

```bash
cd backend
eb init
```

EB CLI will ask:
1. **Select a region** – choose the same region you configured in `aws configure`
2. **Application name** – e.g. `quick-commerce-analyst`
3. **Platform** – choose **Python** → **Python 3.11 running on 64bit Amazon Linux 2023**
4. **CodeCommit** – No (unless you use CodeCommit)
5. **SSH keypair** – Optional (recommended for debugging)

---

### 3. Create the environment and deploy for the first time

```bash
eb create quick-commerce-prod \
  --instance-type t3.medium \
  --min-instances 1 \
  --max-instances 3
```

> **Note:** `t3.medium` (2 vCPU, 4 GB RAM) is recommended because `pandas`, `scikit-learn`, and `numpy` require significant memory during import. `t3.micro` will likely cause OOM crashes.

EB will:
1. Package the current directory (respecting `.gitignore`)
2. Upload to S3
3. Provision an EC2 instance + ALB
4. Install OS packages from `.ebextensions/02_packages.config`
5. Run `pip install -r requirements.txt`
6. Start the app via `Procfile`

---

### 4. Set environment variables (required before the app works)

```bash
eb setenv \
  GEMINI_API_KEY="your-actual-gemini-key" \
  CORS_ORIGINS="https://your-frontend.vercel.app" \
  APP_ENV="production"
```

The environment will restart automatically after `eb setenv`.

---

### 5. Deploy updates

After making code changes:

```bash
eb deploy
```

---

### 6. Check status

```bash
eb status
```

Look for `Health: Green` and `Status: Ready`.

---

### 7. Open the app in a browser

```bash
eb open
```

Then verify the health endpoint manually:

```bash
curl https://<your-eb-url>/health
# Expected: {"status":"ok","env":"production"}
```

---

### 8. View logs

```bash
eb logs
```

Or stream in real time:

```bash
eb logs --stream
```

---

## IAM Permissions Required

Your IAM user needs the following AWS managed policies:

- `AWSElasticBeanstalkFullAccess`
- `AmazonS3FullAccess` (for EB artifact bucket)
- `AmazonEC2FullAccess` (for instance provisioning)
- `AWSCloudFormationFullAccess` (EB uses CloudFormation internally)

Or attach the `AdministratorAccess` policy for development (restrict in production).

---

## Estimated AWS Costs (ap-south-1, Mumbai)

| Resource | Instance | Est. Monthly Cost |
|---|---|---|
| EC2 (t3.medium × 1) | On-Demand | ~$30/month |
| Application Load Balancer | - | ~$18/month |
| S3 (EB artifacts) | - | < $1/month |
| **Total** | | **~$50/month** |

Use Reserved Instances or Savings Plans to reduce EC2 cost by ~40%.
