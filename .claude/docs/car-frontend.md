# car-frontend

React 19 + TypeScript SPA. Communicates with `car-backend-ms` via Axios; JWT stored in localStorage.

**Port:** 5173 (dev) | **Bundler:** Vite 8

## Commands and environment variables

See [README.md](../../README.md) for commands.

Frontend unit tests use Vitest and currently cover prompt construction and tuning reducer behavior. PR checks run `npm run lint`, `npm test`, and `npm run build`.

**Env:** `VITE_API_BASE_URL` is read from the root `.env` via `vite.config.ts` (`envDir: '..'`). No separate `car-frontend/.env` needed.

## Structure

```

```

## Routes



## Key Modules

### State — `TuningPage`

`TuningPage` owns the entire form state via `useReducer`. `TuningFormState` holds: image selection, target (car vs background), color/mods/cosmetics, environment/time/weather/style pickers, `customPromptOverride`, and result status.



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