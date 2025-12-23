# Web Dashboard

React + Vite + TypeScript + Tailwind CSS

## Setup (Sprint 3.1)

```bash
cd web
npm create vite@latest . -- --template react-ts
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
npm install
```

## Development

```bash
npm run dev
```

## Structure

```
web/
├── src/
│   ├── components/     # Reusable UI components
│   ├── pages/          # Route pages
│   ├── hooks/          # Custom React hooks
│   ├── lib/            # Utilities, API client
│   ├── App.tsx
│   └── main.tsx
├── package.json
├── vite.config.ts
└── tailwind.config.js
```

## Implementation Status

- [ ] Sprint 3.1: React Foundation
- [ ] Sprint 3.2: Dashboard Core
- [ ] Sprint 3.3: Queue Management
- [ ] Sprint 3.4: Project Workspace
- [ ] Sprint 3.5: Analytics & Polish
