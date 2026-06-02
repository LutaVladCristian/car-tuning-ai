# car-frontend

React 19 + TypeScript SPA. Communicates with `car-backend-ms` through Axios and authenticates users with Firebase Google Sign-In. The visible app brand and browser tab title are `SlickTunesAI` / `slick-tunes`; the package directory remains `car-frontend`.

**Port:** 5173 in development
**Bundler:** Vite 8

## Commands and Environment Variables

See [README.md](../../README.md) for setup, local run commands, and tests.

Frontend unit tests use Vitest. PR checks run `npm run lint`, `npm test`, and `npm run build`.

`VITE_API_BASE_URL` is read from the repo-root `.env` via `vite.config.ts` (`envDir: '..'`). No separate `car-frontend/.env` is needed for local development.

## Structure

```
car-frontend/src/
|-- main.tsx                        # React 19 entry, mounts to #root
|-- App.tsx                         # BrowserRouter + route definitions
|-- index.css                       # Global styles (Tailwind CSS)
|-- api/
|   |-- client.ts                   # Axios instance; Firebase ID token interceptor; 401 -> /login
|   |-- auth.ts                     # syncFirebaseUser(idToken) -> POST /auth/firebase
|   |-- photos.ts                   # listPhotos(), getPhotoUrl(), getOriginalPhotoUrl(), getPhotoBlob()
|   `-- segmentation.ts             # previewPhoto(), generatePhoto(), deletePreview()
|-- context/
|   |-- AuthContext.tsx             # AuthProvider; Firebase onAuthStateChanged, Google Sign-In
|   |-- authContextCore.ts
|   `-- useAuth.ts
|-- hooks/
|   |-- useEditPhoto.ts             # Submit + 500 ms polling loop (max 10 retries)
|   `-- usePhotoHistory.ts
|-- lib/
|   |-- promptBuilder.ts            # buildPrompt(TuningFormState) -> string
|   `-- promptBuilder.test.ts
|-- types/
|   |-- auth.ts
|   |-- photo.ts
|   `-- tuning.ts                   # EditTarget, car/background state, TuningFormState
|-- pages/
|   |-- LoginPage.tsx
|   |-- SignUpPage.tsx
|   `-- TuningPage.tsx              # Owns form state via useReducer
`-- components/
    |-- layout/
    |   |-- AppShell.tsx
    |   `-- ProtectedRoute.tsx
    |-- auth/
    |   |-- LoginForm.tsx
    |   `-- SignUpForm.tsx
    |-- tuning/
    |   |-- TuningForm.tsx
    |   |-- TuningForm.test.ts
    |   |-- tuningReducer.ts
    |   |-- ImageSelector.tsx
    |   |-- TargetSelector.tsx
    |   |-- car/
    |   |   |-- ColorPicker.tsx
    |   |   |-- BodyModPanel.tsx
    |   |   `-- CosmeticPanel.tsx
    |   `-- background/
    |       |-- EnvironmentPicker.tsx
    |       |-- TimePicker.tsx
    |       |-- WeatherPicker.tsx
    |       `-- StylePicker.tsx
    |-- prompt/
    |   `-- PromptPreview.tsx
    `-- results/
        |-- ImageCompareSlider.tsx  # Original/result overlay slider
        |-- ResultDisplay.tsx       # Compare slider, save/download, New edit action
        `-- PhotoHistoryPanel.tsx
```

## Routes

| Path | Component | Protected | Notes |
|---|---|---|---|
| `/login` | `LoginPage` | No | Google Sign-In entry |
| `/signup` | `SignUpPage` | No | Sign-up route remains registered in `App.tsx` |
| `/` | `TuningPage` inside `AppShell` | Yes, via `ProtectedRoute` | Main editing interface |
| `*` | Redirect to `/` | No | Catch-all |

## Key Modules

### State - `TuningPage`

`TuningPage` owns the form state via `useReducer` + `tuningReducer`. `TuningFormState` holds image selection, edit target (`car` or `background`), car modifications, background style controls, and `customPromptOverride`.

`tuningReducer.ts` handles these action types: `SET_TARGET`, `SET_CAR_COLOR`, `SET_CAR_FINISH`, `SET_CAR_FIELD`, `SET_BG_FIELD`, `TOGGLE_BODY_KIT`, `TOGGLE_LIGHTING`, `SET_CUSTOM_PROMPT`, `RESET_PROMPT_OVERRIDE`, and `RESET_FORM`. All dispatches except `SET_CUSTOM_PROMPT` reset `customPromptOverride` to `null` so the prompt rebuilds from form state.

### Prompt Builder - `src/lib/promptBuilder.ts`

`buildPrompt(form: TuningFormState): string` returns `customPromptOverride` directly if set. Otherwise it assembles an OpenAI prompt from the current car/background selections.

### API Layer - `src/api/`

The Axios client requests `auth.currentUser?.getIdToken()` and sets `Authorization: Bearer <token>` on every request. On HTTP 401, it redirects to `/login`.

### Edit Photo And Comparison Flow

1. `POST /edit-photo/preview` runs YOLO + SAM.
2. Fetch and display the raw binary car mask and effective OpenAI mask.
3. Wait for explicit user approval.
4. `POST /edit-photo/{id}/generate` calls OpenAI.
5. Fetch the original and generated result and display them in `ImageCompareSlider`.
6. Keep completed masks available in a collapsed details section.

History rows call back into `TuningPage`; selecting a row makes that photo ID the active comparison item and highlights the row. The save button downloads the currently active right-side generated/result image, including when the active image came from history.

### Auth - `src/context/AuthContext.tsx`

Firebase auth wraps `onAuthStateChanged` and exposes `user`, `login()` (Google Sign-In popup + backend sync through `POST /auth/firebase`), and `logout()`. `ProtectedRoute` protects the `/` route.
