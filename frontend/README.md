# Frontend

User-facing clients for EVO:LUTION.

## Current Apps

- `vk-mini-app/` - React/Vite VK Mini App.

## VK Mini App

Local run:

```powershell
cd C:\Users\admin\Documents\Codex\bot\frontend\vk-mini-app
npm run dev
```

Production build:

```powershell
cd C:\Users\admin\Documents\Codex\bot\frontend\vk-mini-app
npm run build
```

## Team Rules

- Frontend talks to backend only through public API endpoints.
- No OpenRouter keys, bot tokens, database credentials or private secrets in frontend.
- Shared UI work for VK/Web should stay component-friendly, even while the first app is VK-only.
