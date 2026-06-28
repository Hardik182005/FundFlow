# Deployment (AWS)

Persistence is in-memory (no database). Two pieces to deploy: the FastAPI backend (container)
and the Next.js static frontend.

## Backend — AWS App Runner (recommended)

App Runner builds the container from `fundflow-backend/Dockerfile`, gives you HTTPS + autoscaling,
and supports the ~120s request window an audit needs.

1. Push the image to ECR (or point App Runner at the repo/Dockerfile).
2. Create an App Runner service:
   - Port: `8080`
   - Health check path: `/health`
   - Request timeout: 120s
3. Set environment variables (or wire them to **AWS Secrets Manager**):
   `ANAKIN_API_KEY`, `GEMINI_API_KEY`, `GROQ_API_KEY`, `OPENAI_API_KEY`,
   `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID`, `ALLOWED_ORIGINS=<frontend URL>`,
   `FUNDFLOW_DEMO_MODE=false`.

```bash
aws ecr create-repository --repository-name fundflow-api
docker build -t fundflow-api fundflow-backend
docker tag fundflow-api:latest <acct>.dkr.ecr.<region>.amazonaws.com/fundflow-api:latest
aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <acct>.dkr.ecr.<region>.amazonaws.com
docker push <acct>.dkr.ecr.<region>.amazonaws.com/fundflow-api:latest
# then create the App Runner service from this image in the console/CLI
```

Alternatives: **ECS Fargate** (more control) or **Elastic Beanstalk** (Docker platform). Avoid
plain Lambda unless you add Mangum — audits can run up to ~90s.

## Frontend — S3 + CloudFront (or Amplify Hosting)

Static export (`output: 'export'` → `out/`).

```bash
cd fundflow-frontend
rm -rf .next out
NEXT_PUBLIC_API_URL=https://<app-runner-url> NEXT_PUBLIC_ELEVENLABS_AGENT_ID=<id> npm run build
aws s3 sync out/ s3://<your-bucket> --delete
aws cloudfront create-invalidation --distribution-id <id> --paths "/*"
```

CloudFront notes: set the default root object to `index.html`; because of `trailingSlash: true`
each route emits `route/index.html`. The audit detail page is the query-param route
`/audit/view?id=` so any runtime audit ID works under static hosting.

**AWS Amplify Hosting** is the one-click alternative — connect the repo, set build dir
`fundflow-frontend`, output `out`, and the same `NEXT_PUBLIC_*` build env vars.

## Wiring the two together
- Frontend build-time `NEXT_PUBLIC_API_URL` = backend App Runner HTTPS URL.
- Backend `ALLOWED_ORIGINS` = the CloudFront/Amplify domain (CORS).
- Only `NEXT_PUBLIC_*` vars are exposed to the browser; all secrets stay on the backend.

## Health
`GET /health` and `GET /api/health/dependencies` (config-presence only — never spends credits).
