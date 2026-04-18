# car-frontend

React 19 + TypeScript SPA. Communicates with `car-backend-ms` via Axios; authentication via Firebase (Google Sign-In).

**Port:** 5173 (dev) | **Bundler:** Vite 8

## Commands and environment variables

See [README.md](../../README.md) for commands.

Frontend unit tests use Vitest and currently cover prompt construction and tuning reducer behavior. PR checks run `npm run lint`, `npm test`, and `npm run build`.

**Env:** `VITE_API_BASE_URL` is read from the root `.env` via `vite.config.ts` (`envDir: '..'`). No separate `car-frontend/.env` needed.

## Structure

```
car-frontend/src/
├── main.tsx                        # React 19 entry, mounts to #root
├── App.tsx                         # BrowserRouter + route definitions
├── index.css                       # Global styles (TailwindCSS)
├── api/
│   ├── client.ts                   # Axios instance; Firebase ID token interceptor; 401 → /login redirect
│   ├── auth.ts                     # syncFirebaseUser(idToken) — POST /auth/firebase
│   ├── photos.ts                   # getPhotos(), getPhotoBlob()
│   └── segmentation.ts             # editPhoto()
├── context/
│   ├── AuthContext.tsx             # AuthProvider; Firebase onAuthStateChanged, Google Sign-In
│   ├── authContextCore.ts
│   └── useAuth.ts
├── hooks/
│   ├── useEditPhoto.ts             # Submit + 500 ms polling loop (max 10 retries = 5 s)
│   └── usePhotoHistory.ts
├── lib/
│   ├── promptBuilder.ts            # buildPrompt(TuningFormState) → string
│   └── promptBuilder.test.ts
├── types/
│   ├── auth.ts
│   ├── photo.ts
│   └── tuning.ts                   # EditTarget, PaintFinish, CarEditState, BackgroundEditState, TuningFormState
├── pages/
│   ├── LoginPage.tsx
│   ├── SignUpPage.tsx
│   └── TuningPage.tsx              # Owns all form state via useReducer
└── components/
    ├── layout/
    │   ├── AppShell.tsx
    │   └── ProtectedRoute.tsx
    ├── auth/
    │   ├── LoginForm.tsx
    │   └── SignUpForm.tsx          # stale — /signup route removed from App.tsx
    ├── tuning/
    │   ├── TuningForm.tsx
    │   ├── TuningForm.test.ts
    │   ├── tuningReducer.ts        # 9 action types; all clear customPromptOverride except SET_CUSTOM_PROMPT
    │   ├── ImageSelector.tsx
    │   ├── TargetSelector.tsx
    │   ├── car/
    │   │   ├── ColorPicker.tsx
    │   │   ├── BodyModPanel.tsx
    │   │   └── CosmeticPanel.tsx
    │   └── background/
    │       ├── EnvironmentPicker.tsx
    │       ├── TimePicker.tsx
    │       ├── WeatherPicker.tsx
    │       └── StylePicker.tsx
    ├── prompt/
    │   └── PromptPreview.tsx
    └── results/
        ├── ResultDisplay.tsx
        └── PhotoHistoryPanel.tsx
```

## Routes

| Path | Component | Protected | Notes |
|------|-----------|-----------|-------|
| `/login` | `LoginPage` | No | |
| `/` | `TuningPage` (inside `AppShell`) | Yes — via `ProtectedRoute` | Main editing interface |
| `*` | Redirect → `/` | — | Catch-all |

## Key Modules

### State — `TuningPage`

`TuningPage` owns the entire form state via `useReducer` + `tuningReducer`. `TuningFormState` holds: image selection, target (car vs background), color/mods/cosmetics, environment/time/weather/style pickers, and `customPromptOverride`.

`tuningReducer.ts` handles 9 action types: `SET_TARGET`, `SET_CAR_COLOR`, `SET_CAR_FINISH`, `SET_CAR_FIELD`, `SET_BG_FIELD`, `TOGGLE_BODY_KIT`, `TOGGLE_LIGHTING`, `SET_CUSTOM_PROMPT`, `RESET_PROMPT_OVERRIDE`, `RESET_FORM`. All dispatches except `SET_CUSTOM_PROMPT` reset `customPromptOverride` to `undefined` so the prompt rebuilds from form state automatically.

### Prompt Builder — `src/lib/promptBuilder.ts`

Pure function `buildPrompt(form: TuningFormState): string`. Returns `customPromptOverride` directly if set, otherwise assembles a natural-language OpenAI prompt from form state.

### API Layer — `src/api/`

Axios instance with a Firebase ID token interceptor: calls `auth.currentUser?.getIdToken()` on every request and sets `Authorization: Bearer <token>`. On 401 response, redirects to `/login`. Modules: `auth.ts`, `photos.ts`, `segmentation.ts`.

### edit-photo Polling Flow

1. Snapshot `GET /photos` total count
2. `POST /edit-photo` (up to 180 s — OpenAI processing)
3. Poll `GET /photos?limit=1` every 500 ms (max 10 retries = 5 s window) until `total` increases
4. Fetch new photo via `GET /photos/{id}` → display

### Auth — `src/context/AuthContext.tsx`

Firebase-based auth. `AuthContext` wraps `onAuthStateChanged` and exposes `user` (`{uid, email, displayName}`), `login()` (Google Sign-In popup + syncs user to backend via `POST /auth/firebase`), and `logout()`. `ProtectedRoute` wraps the `/` route.