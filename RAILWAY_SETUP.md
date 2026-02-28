# Railway Setup — Step by Step
## Two services to create: Backend + Frontend

---

## IMPORTANT: Railway must be configured as TWO separate services
## Each service points to a different subfolder of this repo

---

## Service 1: BACKEND (FastAPI)

### In Railway Dashboard:
1. Click **"New Service"** → **"GitHub Repo"**
2. Select `venkybobby/saro-platform`
3. **Root Directory** → type: `backend`
4. Railway will auto-detect Python ✓
5. Add these **Variables**:
   ```
   SECRET_KEY = saro-demo-secret-2024
   DEBUG = false
   PORT = 8000
   ```
6. Click **Deploy**
7. Go to **Settings → Networking → Generate Domain**
8. Copy your backend URL: `https://saro-backend-xxxx.up.railway.app`

---

## Service 2: FRONTEND (React)

### In Railway Dashboard:
1. In same project, click **"New Service"** → **"GitHub Repo"**  
2. Select `venkybobby/saro-platform`
3. **Root Directory** → type: `frontend`
4. Railway will auto-detect Node.js ✓
5. Add these **Variables**:
   ```
   VITE_API_URL = https://saro-backend-xxxx.up.railway.app
   PORT = 3000
   ```
   (Replace xxxx with your actual backend URL from step 8 above)
6. Click **Deploy**
7. Go to **Settings → Networking → Generate Domain**
8. Your frontend URL: `https://saro-frontend-xxxx.up.railway.app`

---

## Verify Both Services Are Running

Backend health check:
```
https://saro-backend-xxxx.up.railway.app/api/v1/health
```
Should return: `{"status": "healthy", "version": "4.0.0"}`

Frontend:
```
https://saro-frontend-xxxx.up.railway.app
```
Should show the SARO dashboard.

---

## Seed Demo Data (run on your local machine)

```bash
pip install httpx
python seed_demo.py --url https://saro-backend-xxxx.up.railway.app
```

