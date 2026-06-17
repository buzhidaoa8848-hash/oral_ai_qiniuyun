# SceneTalk AI Frontend

Next.js frontend for SceneTalk AI.

## Local Development

```bash
npm install
npm run dev
```

The frontend calls the backend from `NEXT_PUBLIC_API_URL`.

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Vercel Deployment

Use these settings when importing the GitHub repository into Vercel:

| Setting | Value |
| --- | --- |
| Framework Preset | Next.js |
| Root Directory | `frontend` |
| Install Command | `npm ci` |
| Build Command | `npm run build` |
| Output Directory | leave empty |

Required environment variable:

```env
NEXT_PUBLIC_API_URL=https://api.your-domain.com
```

After deployment, add your custom domain in Vercel:

```text
talk.your-domain.com
```

Then configure your DNS provider with the record Vercel shows, usually a
`CNAME` record for the subdomain.
