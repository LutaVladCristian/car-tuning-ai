export type EditTarget = 'car' | 'background';
export type PaintFinish = 'solid' | 'metallic' | 'matte' | 'special';
export type Environment = 'urban' | 'mountain' | 'track' | 'beach' | 'industrial';
export type TimeOfDay = 'day' | 'sunset' | 'night' | 'dawn';
export type Weather = 'clear' | 'rain' | 'snow' | 'fog';
export type PhotoStyle = 'action' | 'static' | 'three-quarter' | 'dramatic';
export type ImageSourceType = 'upload' | 'history';

export interface CarEditState {
  color: string;
  finish: PaintFinish;
  spoiler: string | null;
  rimSize: string | null;
  rimStyle: string | null;
  rimFinish: string | null;
  bodyKit: string[];
  windowTint: string | null;
  lighting: string[];
  stance: string | null;
  vinylWrap: string | null;
}

export interface BackgroundEditState {
  environment: Environment;
  timeOfDay: TimeOfDay;
  weather: Weather;
  style: PhotoStyle;
}

export interface TuningFormState {
  target: EditTarget;
  car: CarEditState;
  background: BackgroundEditState;
  customPromptOverride: string | null;
}

export const DEFAULT_CAR_STATE: CarEditState = {
  color: '',
  finish: 'solid',
  spoiler: null,
  rimSize: null,
  rimStyle: null,
  rimFinish: null,
  bodyKit: [],
  windowTint: null,
  lighting: [],
  stance: null,
  vinylWrap: null,
};

export const DEFAULT_BACKGROUND_STATE: BackgroundEditState = {
  environment: 'urban',
  timeOfDay: 'sunset',
  weather: 'clear',
  style: 'static',
};

export const DEFAULT_FORM_STATE: TuningFormState = {
  target: 'background',
  car: DEFAULT_CAR_STATE,
  background: DEFAULT_BACKGROUND_STATE,
  customPromptOverride: null,
};
