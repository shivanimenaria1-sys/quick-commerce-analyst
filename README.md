# Quick Commerce Analyst AI Platform

A premium full-stack AI-driven business intelligence and operational diagnostics platform tailored for quick commerce (q-commerce) companies. Features recursive data cleansing, feature engineering calculations, interactive charts, and Gemini-compiled reports.

---

## 1. Project Structure

- `backend/`: FastAPI application containing analysis services, models, and utility tools.
- `frontend/`: Vite + React + Tailwind CSS web interface.

---

## 2. Environment Variables

### Backend Configuration (`backend/.env`)
Create a `.env` file inside the `backend` directory:
```env
# Server Port (optional, defaults to 8000)
PORT=8000

# Google Gemini API key
GEMINI_API_KEY=your_gemini_api_key_here

# Allowed CORS origins (comma-separated, leave blank to default to localhost)
CORS_ORIGINS=https://your-frontend-app.vercel.app
```

### Frontend Configuration (`frontend/.env`)
Create a `.env` file inside the `frontend` directory:
```env
# Backend server endpoint URL
VITE_API_BASE_URL=http://127.0.0.1:8000

# Firebase SDK Authentication Configuration
VITE_FIREBASE_API_KEY=your_firebase_api_key
VITE_FIREBASE_AUTH_DOMAIN=your_firebase_project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your_firebase_project
VITE_FIREBASE_STORAGE_BUCKET=your_firebase_project.firebasestorage.app
VITE_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
VITE_FIREBASE_APP_ID=your_app_id
VITE_FIREBASE_MEASUREMENT_ID=your_measurement_id
```

---

## 3. Local Development Setup

### Running Backend Locally
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Install the python packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the uvicorn development server:
   ```bash
   uvicorn app.main:app --reload
   ```
The backend API Swagger docs will be active at `http://127.0.0.1:8000/docs`.

### Running Frontend Locally
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install the node packages:
   ```bash
   npm install
   ```
3. Start the dev server:
   ```bash
   npm run dev
   ```
The web dashboard will be open at `http://localhost:5173`.

---

## 4. Docker Configurations

You can run the backend service in a isolated Docker container.

### Build the Docker Image
Navigate to the `backend/` directory containing the `Dockerfile` and run:
```bash
docker build -t quick-commerce-backend .
```

### Run the Docker Container
Run the container mapping host port 8000:
```bash
docker run -p 8000:8000 --env-file .env quick-commerce-backend
```

---

## 5. Production Deployments

### Backend Deployment (Render)
This repository includes a `render.yaml` file to automate Render deployment.
1. Connect your GitHub repository to Render.
2. Click **New** -> **Blueprint**.
3. Render will auto-discover the backend service based on `render.yaml`.
4. Configure the required environment variables in Render's dashboard:
   - `GEMINI_API_KEY`: Your Gemini API access credentials.
   - `CORS_ORIGINS`: Your Vercel frontend URL (e.g. `https://your-app.vercel.app`).

### Frontend Deployment (Vercel)
The React frontend can be deployed directly to Vercel.
1. Connect your GitHub repository to Vercel.
2. Choose the `frontend` folder as the root directory of the Vercel project.
3. Configure the build parameters:
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
4. Add all required frontend environment variables (starting with `VITE_`) in Vercel's project settings.
5. The included `vercel.json` rewrite rules will route all page requests back to `index.html` to support `react-router-dom` path refreshes.
