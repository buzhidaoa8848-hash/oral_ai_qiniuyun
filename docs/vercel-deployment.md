# Vercel Deployment Checklist

This project should be deployed as two services:

| Service | Recommended host | Domain example |
| --- | --- | --- |
| Frontend | Vercel | `talk.your-domain.com` |
| Backend | Render, Railway, Fly.io, or a VPS | `api.your-domain.com` |

The FastAPI backend is not a good fit for Vercel serverless in its current
shape because it uses a normal ASGI app lifecycle, SQLite by default, audio
uploads, and potentially long-running AI/STT calls.

## 1. Deploy Backend First

Start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Set these backend environment variables:

```env
FRONTEND_ORIGINS=https://talk.your-domain.com
MOCK_MODE=true
LLM_PROVIDER=mock
STT_PROVIDER=mock
TTS_PROVIDER=mock
PRONUNCIATION_PROVIDER=fallback
```

For a real AI deployment:

```env
MOCK_MODE=false
LLM_PROVIDER=deepseek
STT_PROVIDER=qwen
DEEPSEEK_API_KEY=your-key
DASHSCOPE_API_KEY=your-key
```

Verify the backend:

```text
https://api.your-domain.com/api/health
```

## 2. Deploy Frontend To Vercel

When importing the GitHub repository in Vercel:

| Setting | Value |
| --- | --- |
| Framework Preset | Next.js |
| Root Directory | `frontend` |
| Install Command | `npm ci` |
| Build Command | `npm run build` |
| Output Directory | leave empty |

Set this Vercel environment variable:

```env
NEXT_PUBLIC_API_URL=https://api.your-domain.com
```

Then add the frontend custom domain:

```text
talk.your-domain.com
```

## 3. DNS

For the frontend subdomain, add the DNS record shown by Vercel. For most
subdomains this is a `CNAME` record.

For the backend subdomain, add the DNS record shown by your backend host.

## 4. Common Failure Points

- Browser CORS error: ensure backend `FRONTEND_ORIGINS` exactly includes the
  frontend origin, including `https://`.
- Frontend cannot connect to API: ensure Vercel has
  `NEXT_PUBLIC_API_URL=https://api.your-domain.com`, then redeploy.
- Local tests unexpectedly call real AI providers: run tests with
  `MOCK_MODE=true`, `LLM_PROVIDER=mock`, and `STT_PROVIDER=mock`.
