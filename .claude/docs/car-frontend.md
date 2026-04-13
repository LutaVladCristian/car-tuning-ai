# car-frontend

React 19 + TypeScript SPA. Communicates with `car-backend-ms` via Axios; JWT stored in localStorage.

**Port:** 5173 (dev) | **Bundler:** Vite 8

## Commands

```bash
cd car-frontend

npm run dev       # dev server at port 5173
npm run build     # tsc -b && vite build → dist/
npm run lint      # eslint .
npm run preview   # serve dist/ locally
```

**Env:** `VITE_API_BASE_URL` is read from the root `.env` via `vite.config.ts` (`envDir: '..'`). No separate `car-frontend/.env` needed.

## Routes

| Path | Component | Auth |
|---|---|---|
| `/login` | LoginPage | Public |
| `/signup` | SignUpPage | Public |
| `/` | TuningPage (inside AppShell) | Protected (JWT required) |
| `/*` | Redirect to `/` | — |

## Key Modules

### State — `TuningPage`

`TuningPage` owns the entire form state via `useReducer`. `TuningFormState` holds: image selection, target (car vs background), color/mods/cosmetics, environment/time/weather/style pickers, `customPromptOverride`, and result status.

```
TuningPage (useReducer → TuningFormState)
├── ImageSelector        — upload file OR pick from photo history
├── TuningForm           — dispatches TuningAction
│   ├── TargetSelector   — "Edit Car" / "Edit Background"
│   ├── [Car mode]
│   │   ├── ColorPicker  — swatches + text + finish
│   │   ├── BodyModPanel — spoiler, rims, body kit, stance
│   │   └── CosmeticPanel— tint, lighting, vinyl wrap
│   └── [Background mode]
│       ├── EnvironmentPicker — urban/mountain/track/beach/industrial
│       ├── TimePicker        — day/sunset/night/dawn
│       ├── WeatherPicker     — clear/rain/snow/fog
│       └── StylePicker       — static/action/three-quarter/dramatic
├── PromptPreview        — live assembled prompt; manually editable
├── Submit → useEditPhoto.submit()
├── ResultDisplay        — idle / submitting / polling / success / error
└── PhotoHistoryPanel    — paginated history; click to reuse as input
```

### Prompt Builder — `src/lib/promptBuilder.ts`

Pure function `buildPrompt(form: TuningFormState): string`. Returns `customPromptOverride` directly if set, otherwise assembles a natural-language OpenAI prompt from form state.

### API Layer — `src/api/`

Axios instance with JWT interceptor that reads from `AuthContext`. Modules: `auth.ts`, `photos.ts`, `segmentation.ts`.

### edit-photo Polling Flow

1. Snapshot `GET /photos` total count
2. `POST /edit-photo` (up to 180 s — OpenAI processing)
3. Poll `GET /photos?limit=1` until `total` increases
4. Fetch new photo via `GET /photos/{id}` → display

### Auth — `src/context/AuthContext.tsx`

JWT stored in `localStorage`. `AuthContext` provides `user`, `login()`, `logout()`. `ProtectedRoute` wraps the `/` route.

## Design Tokens (dark automotive theme)

| Token | Value | Usage |
|---|---|---|
| `surface-900` | `#0A0A0A` | Page background |
| `surface-800` | `#111111` | Cards/panels |
| `surface-700` | `#1C1C1E` | Inputs |
| `surface-600` | `#2C2C2E` | Borders |
| `accent-blue` | `#3B82F6` | "Edit Car" mode |
| `accent-orange` | `#F97316` | "Edit Background" mode |

## Docker

```bash
# Build static assets and serve with nginx
docker build -t car-frontend ./car-frontend
docker run -p 80:80 car-frontend
```

Set `VITE_API_BASE_URL` as a build arg or bake it in before `npm run build`.
