# Elastic Beanstalk – Troubleshooting Reference

All log commands assume you are inside the `backend/` directory and have run
`eb init` for this project.

---

## 1. ModuleNotFoundError

**Symptom**
```
ModuleNotFoundError: No module named 'fastapi'
ModuleNotFoundError: No module named 'google'
```

**Causes & Fixes**

| Cause | Fix |
|---|---|
| `requirements.txt` missing from deployment zip | Verify `.gitignore` does **not** exclude `requirements.txt`. Run `cat requirements.txt` to confirm it exists. |
| EB installed to the wrong Python | Confirm platform is **Python 3.11 on Amazon Linux 2023**. Run `eb platform show`. |
| Stale EB environment using old code | Run `eb deploy` to force a fresh deployment. |
| Package name changed | `google-genai` (not `google-generativeai`). Check `requirements.txt`. |

**Diagnostic commands**
```bash
eb logs              # Check the full deploy log
eb ssh               # SSH into the instance then:
  python3 -c "import fastapi; print(fastapi.__version__)"
  pip3 list | grep google
```

---

## 2. Procfile Errors

**Symptom**
```
Your WSGIPath refers to a file that does not exist
Error: No web process found in Procfile
```

**Causes & Fixes**

| Cause | Fix |
|---|---|
| `Procfile` has Windows-style CRLF line endings | Open in a Unix-aware editor or run `sed -i 's/\r//' Procfile` |
| `Procfile` not in the root of the zip (must be at `backend/Procfile`) | Make sure you run `eb deploy` from inside the `backend/` directory |
| Typo in module path | The correct path is `app.main:app`. Verify by running `python3 -c "from app.main import app"` locally |
| EB using WSGI mode instead of Procfile | Add `web:` prefix (lowercase) in Procfile. EB detects Procfile automatically on AL2023. |

**Correct Procfile content**
```
web: uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## 3. 502 Bad Gateway

**Symptom**
```
HTTP 502 Bad Gateway from the EB load balancer
```

**Causes & Fixes**

| Cause | Fix |
|---|---|
| App crashed on startup (missing `GEMINI_API_KEY`) | Run `eb setenv GEMINI_API_KEY="..."` then `eb deploy` |
| App listening on wrong port | Procfile must use `--port 8000`. EB ALB routes to port 8000. |
| App bound to `127.0.0.1` instead of `0.0.0.0` | Procfile must use `--host 0.0.0.0` |
| Instance memory exhausted during import of pandas/numpy | Upgrade to `t3.medium` (4 GB RAM). `t3.micro` is too small. |
| EB health check failing (app returns non-200) | Ensure `GET /health` returns HTTP 200. Check `.ebextensions/01_app.config` has `HealthCheckPath: /health`. |
| App takes > 30s to start | WeasyPrint / pandas import is slow. EB default timeout is 60s — if it takes longer, increase `HealthCheckTimeout` in `01_app.config`. |

**Diagnostic commands**
```bash
eb logs                       # Look for "Traceback" or startup exceptions
eb health                     # See per-instance health status
curl http://<eb-url>/health   # Test the health endpoint directly
```

---

## 4. Missing Dependencies

**Symptom**
```
ImportError: cannot import name 'X' from 'Y'
OSError: cannot load library 'libgobject-2.0-0.so.0'  ← WeasyPrint
```

**Causes & Fixes**

| Cause | Fix |
|---|---|
| `reportlab` not in `requirements.txt` | Add `reportlab==4.2.5` (already fixed) |
| WeasyPrint needs Cairo/Pango native libs | These are installed by `.ebextensions/02_packages.config`. If missing, check EB deployment log for yum errors. |
| WeasyPrint version incompatible with Amazon Linux | Pin to `weasyprint==62.3`. Newer versions may require newer libpango. |

**Check yum install log**
```bash
eb logs
# Look for lines containing "packages" or "cairo"
# Or SSH in and run:
eb ssh
  rpm -q cairo pango libffi
```

---

## 5. Environment Variable Errors

**Symptom**
```
RuntimeError: Critical startup error: GEMINI_API_KEY is missing or empty
KeyError: 'GEMINI_API_KEY'
```

**Causes & Fixes**

| Cause | Fix |
|---|---|
| `.env` file not deployed (by design — it is in `.gitignore`) | Set secrets as EB environment properties via `eb setenv` |
| Typo in variable name | Variable is exactly `GEMINI_API_KEY` (case-sensitive) |
| `eb setenv` applied but environment not restarted | EB auto-restarts after `eb setenv`. Wait 60–90 seconds. |
| Variable set in wrong environment | Run `eb use <environment-name>` to select the right environment before `eb setenv` |

**Verify env vars are set**
```bash
eb printenv
```

**Set all required vars at once**
```bash
eb setenv \
  GEMINI_API_KEY="your-key" \
  CORS_ORIGINS="https://your-frontend.com" \
  APP_ENV="production"
```

---

## 6. CORS Errors

**Symptom**
```
Access to fetch at 'https://api.yourdomain.com/api/...' from origin
'https://your-frontend.vercel.app' has been blocked by CORS policy:
No 'Access-Control-Allow-Origin' header is present.
```

**Causes & Fixes**

| Cause | Fix |
|---|---|
| `CORS_ORIGINS` env var not set | `eb setenv CORS_ORIGINS="https://your-frontend.vercel.app"` |
| Frontend URL has trailing slash | Remove it: `https://your-frontend.vercel.app` not `https://your-frontend.vercel.app/` |
| `APP_ENV=production` set but `CORS_ORIGINS` not updated | In production mode, localhost origins are NOT added automatically. You must set `CORS_ORIGINS` explicitly. |
| HTTPS frontend calling HTTP API | Both must be HTTPS in production. Set up ACM certificate on the EB load balancer. |
| Multiple frontends | Comma-separate them: `CORS_ORIGINS="https://app.com,https://www.app.com"` |

**Test CORS preflight manually**
```bash
curl -v -X OPTIONS https://<eb-url>/api/upload \
  -H "Origin: https://your-frontend.vercel.app" \
  -H "Access-Control-Request-Method: POST"
# Should return: Access-Control-Allow-Origin: https://your-frontend.vercel.app
```

---

## 7. Health Check Failures

**Symptom**
```
Environment health has transitioned from Ok to Warning
INFO  Application health check endpoint returned a non-200 response
```

**Causes & Fixes**

| Cause | Fix |
|---|---|
| `/health` endpoint raises an exception | View logs: `eb logs`. Look for the traceback under the health check request. |
| `GEMINI_API_KEY` missing causes startup crash → all routes fail | Set `GEMINI_API_KEY` via `eb setenv`, deploy again. |
| Health check path misconfigured | Verify `.ebextensions/01_app.config` has `HealthCheckPath: /health`. |
| App listening on wrong port | Procfile must use `--port 8000`. Verify with `eb logs`. |
| Response takes > 5 seconds | Increase `HealthCheckTimeout` in `01_app.config` to `"10"`. |

**Quick health check test**
```bash
# After eb deploy, get the URL:
eb status | grep CNAME

# Test health directly:
curl https://<cname>/health
# Expected: {"status":"ok","env":"production"}
```

---

## General Debug Workflow

```bash
# 1. Check environment status
eb status

# 2. Pull recent logs
eb logs

# 3. SSH into instance for live debugging
eb ssh
  sudo journalctl -u web        # See uvicorn process logs
  sudo cat /var/log/eb-engine.log | tail -100

# 4. Check which Python is active
eb ssh
  which python3
  python3 --version
  pip3 list

# 5. Force a clean re-deploy
eb deploy --staged   # Deploy committed changes
# OR
eb deploy            # Deploy current working directory
```
