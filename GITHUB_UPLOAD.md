# GitHub Upload Guide

This folder is a cleaned public version of the project.
It does not include `.env`, local database dumps, `node_modules`, frontend `dist`,
`.git`, `.vsix`, diagnostics or backup archives.

## 1. Create A New GitHub Repository

Create an empty repository on GitHub, for example:

```text
evolution-tutor-bot
```

Do not initialize it with a README if you want to push this folder as-is.

## 2. Initialize Git Locally

Run these commands inside this cleaned folder:

```bash
git init
git add .
git commit -m "Initial public GitHub version"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/evolution-tutor-bot.git
git push -u origin main
```

## 3. Configure Runtime Locally Or On Server

Create a real environment file only outside git history:

```bash
cp .env.example .env
```

Fill in your own tokens and passwords:

```env
TG_BOT_TOKEN=
OPENROUTER_API_KEY=
POSTGRES_PASSWORD=
DATABASE_URL=
VK_APP_SECRET=
```

## 4. Sanity Checks Before Push

```bash
git status --short
git check-ignore .env
git check-ignore backend/database/example.db
```

Expected: `.env` and database dumps are ignored.

## 5. Run Checks

```bash
python -m compileall -q backend/src
cd frontend/vk-mini-app
npm install
npm run build
```
