# VK Mini App

Frontend for the EVO:LUTION VK Mini App.

## Local Setup

```bash
npm install
cp .env.example .env
npm run dev
```

Set `VITE_API_BASE_URL` to the public HTTPS URL of the backend API.
For VK hosting it must be a real HTTPS domain, for example:

```env
VITE_API_BASE_URL=https://your-domain.example
```

## Build

```bash
npm run build
```

The production build is created in `dist/`.

## Deploy To VK Hosting

```bash
npm run deploy
```

The deploy script uses `vk-miniapps-deploy`.
