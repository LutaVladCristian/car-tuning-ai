# FRONTEND.md — Car Tuning AI

## Overview

React + TypeScript frontend for the Car Tuning AI platform. Provides login, registration, and a car tuning studio where users upload a car photo, configure modifications via a structured form, and generate AI-edited images via the backend's `/edit-photo` endpoint.

**Location:** `car-tuning-ai/car-frontend/`
**Dev server:** `http://localhost:5173`

---

## Tech Stack

| Concern | Choice |
|---|---|
| Bundler | Vite 5 |
| UI | React 18 + TypeScript 5 |
| Routing | React Router v6 |
| HTTP | Axios (with JWT interceptor) |
| Styling | Tailwind CSS v3 |
| State | React Context + useReducer |

No component libraries — pure Tailwind + custom components.

---

## Running the Frontend

```bash
# Prerequisites: both backend services must be running
# Terminal 1
conda activate car-backend-ms && cd car-backend-ms && uvicorn main:app --reload --port 8001

# Terminal 2
conda activate sam-microservice && cd car-segmentation-ms && uvicorn server:app --reload --port 8000

# Terminal 3 — frontend
cd car-frontend
npm install     # first time only
npm run dev     # http://localhost:5173
```

---

## Folder Structure

```
car-frontend/
├── .env                          # VITE_API_BASE_URL=http://localhost:8001
├── tailwind.config.js            # Custom colors + shadows
├── src/
│   ├── main.tsx                  # React entry point
│   ├── App.tsx                   # Router + AuthProvider
│   ├── index.css                 # Tailwind base directives
│   ├── types/
│   │   ├── auth.ts               # RegisterRequest, LoginRequest, TokenResponse, AuthUser
│   │   ├── photo.ts              # PhotoResponse, PhotoListResponse, EditPhotoResponse
│   │   └── tuning.ts             # TuningFormState, CarEditState, BackgroundEditState, defaults
│   ├── api/
│   │   ├── client.ts             # Axios instance + auth header + 401 logout interceptors
│   │   ├── auth.ts               # registerUser(), loginUser()
│   │   ├── photos.ts             # listPhotos(), getPhotoUrl(), getPhotoBlob()
│   │   └── segmentation.ts       # editPhoto(), carSegmentation(), carPartSegmentation()
│   ├── context/
│   │   └── AuthContext.tsx       # AuthProvider, useAuth hook, localStorage persistence
│   ├── hooks/
│   │   ├── usePhotoHistory.ts    # Paginated GET /photos with refetch()
│   │   └── useEditPhoto.ts       # submit(), polling, status state machine
│   ├── lib/
│   │   └── promptBuilder.ts      # Pure fn: TuningFormState → natural language prompt
│   ├── pages/
│   │   ├── LoginPage.tsx
│   │   ├── SignUpPage.tsx
│   │   └── TuningPage.tsx        # Main orchestrating page
│   └── components/
│       ├── layout/
│       │   ├── AppShell.tsx      # Navbar + Outlet
│       │   └── ProtectedRoute.tsx
│       ├── auth/
│       │   ├── LoginForm.tsx
│       │   └── SignUpForm.tsx
│       ├── tuning/
│       │   ├── TuningForm.tsx    # Defines TuningAction + tuningReducer; orchestrates panels
│       │   ├── TargetSelector.tsx
│       │   ├── ImageSelector.tsx # Upload (drag-drop) or pick from history
│       │   ├── car/
│       │   │   ├── ColorPicker.tsx     # Preset swatches + text input + finish selector
│       │   │   ├── BodyModPanel.tsx    # Spoiler, rims, body kit, stance
│       │   │   └── CosmeticPanel.tsx   # Window tint, lighting, vinyl wrap
│       │   └── background/
│       │       ├── EnvironmentPicker.tsx
│       │       ├── TimePicker.tsx
│       │       ├── WeatherPicker.tsx
│       │       └── StylePicker.tsx
│       ├── prompt/
│       │   └── PromptPreview.tsx # Editable textarea; shows "Custom" badge when overridden
│       └── results/
│           ├── ResultDisplay.tsx       # Status machine: idle/submitting/polling/success/error
│           └── PhotoHistoryPanel.tsx   # Paginated list, clickable to reuse as input
```

---

## Routes

| Path | Component | Auth |
|---|---|---|
| `/login` | LoginPage | Public |
| `/signup` | SignUpPage | Public |
| `/` | TuningPage (inside AppShell) | Protected (JWT required) |
| `/*` | Redirect to `/` | — |

---

## Auth Flow

1. User submits login form → `POST /auth/login` → JWT stored in `localStorage`
2. `AuthContext` restores state from `localStorage` on page refresh (lazy init)
3. Axios request interceptor attaches `Authorization: Bearer <token>` to every request
4. Axios response interceptor: on `401` → clear storage + redirect to `/login`
5. Logout clears `localStorage` and resets context state

---

## Tuning Page Architecture

```
TuningPage (useReducer → TuningFormState)
├── ImageSelector        — upload file OR pick from GET /photos history
├── TuningForm           — dispatches TuningAction to reducer
│   ├── TargetSelector   — "Edit Car" (blue) / "Edit Background" (orange)
│   ├── [Car mode]
│   │   ├── ColorPicker  — swatches + text + finish (solid/metallic/matte/special)
│   │   ├── BodyModPanel — spoiler, rims, body kit, stance
│   │   └── CosmeticPanel— tint, lighting, vinyl
│   └── [Background mode]
│       ├── EnvironmentPicker — urban/mountain/track/beach/industrial
│       ├── TimePicker        — day/sunset/night/dawn
│       ├── WeatherPicker     — clear/rain/snow/fog
│       └── StylePicker       — static/action/three-quarter/dramatic
├── PromptPreview        — live preview of assembled prompt; manually editable
├── Submit button        → useEditPhoto.submit()
├── ResultDisplay        — shows status + fetched image from GET /photos/{id}
└── PhotoHistoryPanel    — paginated history; click to reuse photo as input
```

### State reducer actions (`TuningAction`)

| Action | Effect |
|---|---|
| `SET_TARGET` | Switch car/background mode; clears prompt override |
| `SET_CAR_COLOR` | Update car color string |
| `SET_CAR_FINISH` | Update paint finish enum |
| `SET_CAR_FIELD` | Update any scalar field in CarEditState |
| `SET_BG_FIELD` | Update any scalar field in BackgroundEditState |
| `TOGGLE_BODY_KIT` | Toggle item in bodyKit array |
| `TOGGLE_LIGHTING` | Toggle item in lighting array |
| `SET_CUSTOM_PROMPT` | User manually edited textarea |
| `RESET_PROMPT_OVERRIDE` | Clear override; auto-prompt resumes |
| `RESET_FORM` | Full reset to defaults |

---

## Prompt Builder (`src/lib/promptBuilder.ts`)

Pure function `buildPrompt(form: TuningFormState): string`. Two modes:

**Car mode** — assembles fragments:
- Color: `"Repaint the entire car body in metallic midnight blue paint."`
- Body mods: `"Add a GT racing wing spoiler. Fit 19-inch multi-spoke wheels with chrome finish."`
- Cosmetics: `"Apply 35% dark window tint to all windows. Upgrade lighting with: LED headlights, Halo angel eyes."`
- Footer: `"Maintain photorealism... keep geometry of the original car..."`

**Background mode:**
- `"Replace only the background of this image with a photorealistic urban city street during golden hour sunset with rainy conditions... Keep the car exactly as it is..."`

If `customPromptOverride !== null`, that string is returned directly. A "Reset to auto" button clears it.

---

## edit-photo Flow

1. User selects image + configures form → prompt auto-assembles
2. Submit button calls `useEditPhoto.submit(file, prompt, editCar)`
3. Hook snapshots `GET /photos` total count
4. `POST /edit-photo` is called (30–90s, 180s timeout) — OpenAI processes
5. On response, hook polls `GET /photos?limit=1` until `total` increases
6. New `photo.id` retrieved → `ResultDisplay` fetches it via `GET /photos/{id}`
7. History panel refreshes automatically

**Known backend limitation:** `result_image` is `NULL` for `edit_photo` operations — `GET /photos/{id}` returns the original image. `ResultDisplay` shows the original with an explanatory note.

---

## Design System

Dark automotive aesthetic, no light mode:

| Token | Value | Use |
|---|---|---|
| `surface-900` | `#0A0A0A` | Page background |
| `surface-800` | `#111111` | Card/panel |
| `surface-700` | `#1C1C1E` | Inputs, selectors |
| `surface-600` | `#2C2C2E` | Borders, dividers |
| `accent-blue` | `#3B82F6` | "Edit Car" mode, links, focus |
| `accent-orange` | `#F97316` | "Edit Background" mode, CTAs |
| `shadow-glow-blue` | `0 0 20px rgba(59,130,246,0.3)` | Active buttons |
| `shadow-glow-orange` | `0 0 20px rgba(249,115,22,0.3)` | Active buttons |

---

## Environment Variables

```bash
# car-frontend/.env
VITE_API_BASE_URL=http://localhost:8001
```

Change this to point at a production backend URL when deploying.
