import type { TuningFormState, CarEditState, BackgroundEditState } from '../types/tuning';

// ── Car edit prompt ───────────────────────────────────────────────────────

function buildColorFragment(car: CarEditState): string {
  if (!car.color) return '';
  const finishMap: Record<string, string> = {
    solid: 'solid',
    metallic: 'metallic',
    matte: 'matte flat',
    special: 'special-effect',
  };
  const finish = finishMap[car.finish] ?? 'solid';
  return `Repaint the entire car body in ${finish} ${car.color} paint.`;
}

function buildBodyModFragment(car: CarEditState): string {
  const parts: string[] = [];
  if (car.spoiler) parts.push(`Add a ${car.spoiler} spoiler`);
  if (car.rimSize && car.rimStyle) {
    const rimFinish = car.rimFinish ? ` with ${car.rimFinish} finish` : '';
    parts.push(`Fit ${car.rimSize} ${car.rimStyle} wheels${rimFinish}`);
  }
  if (car.bodyKit.length > 0) parts.push(`Apply body kit: ${car.bodyKit.join(', ')}`);
  if (car.stance) parts.push(`Apply ${car.stance} stance`);
  return parts.join('. ');
}

function buildCosmeticFragment(car: CarEditState): string {
  const parts: string[] = [];
  if (car.windowTint) parts.push(`Apply ${car.windowTint} window tint to all windows`);
  if (car.lighting.length > 0) parts.push(`Upgrade lighting with: ${car.lighting.join(', ')}`);
  if (car.vinylWrap) parts.push(`Add ${car.vinylWrap} vinyl wrap graphics`);
  return parts.join('. ');
}

function buildCarPrompt(car: CarEditState): string {
  const fragments = [
    buildColorFragment(car),
    buildBodyModFragment(car),
    buildCosmeticFragment(car),
  ].filter(Boolean);

  if (fragments.length === 0) {
    return (
      'Enhance the car in this photograph with photorealistic quality. ' +
      'Maintain the exact geometry, model, and proportions of the original car. ' +
      'Keep all other parts of the car exactly as they are. ' +
      'Use the provided mask to restrict changes to the car body only.'
    );
  }

  return (
    `You are editing a real car photograph. ${fragments.join(' ')} ` +
    `Maintain photorealism, correct lighting, and consistent shadows. ` +
    `Keep the geometry and model of the car exactly as in the original photo. ` +
    `Use the provided mask to restrict changes to the car body only.`
  );
}

// ── Background edit prompt ─────────────────────────────────────────────

const environmentLabels: Record<string, string> = {
  urban: 'a photorealistic urban city street',
  mountain: 'a scenic mountain road with dramatic peaks',
  track: 'a professional motorsport race track',
  beach: 'a coastal beach road at the shoreline',
  industrial: 'a gritty industrial zone with concrete warehouses',
};

const timeLabels: Record<string, string> = {
  day: 'midday bright daylight',
  sunset: 'golden hour sunset',
  night: 'nighttime with city lights and neon reflections',
  dawn: 'early dawn blue hour',
};

const weatherLabels: Record<string, string> = {
  clear: 'clear sky',
  rain: 'rainy conditions with a wet reflective ground',
  snow: 'light snowfall with snow on the ground',
  fog: 'dense atmospheric fog',
};

const styleLabels: Record<string, string> = {
  action: 'a motion blur action shot as if the car is moving at speed',
  static: 'a clean static display shot',
  'three-quarter': 'a classic three-quarter angle perspective',
  dramatic: 'a dramatic low-angle cinematic composition',
};

function buildBackgroundPrompt(bg: BackgroundEditState): string {
  const env = environmentLabels[bg.environment] ?? bg.environment;
  const time = timeLabels[bg.timeOfDay] ?? bg.timeOfDay;
  const weather = weatherLabels[bg.weather] ?? bg.weather;
  const style = styleLabels[bg.style] ?? bg.style;

  return (
    `Replace only the background of this image with ${env} ` +
    `during ${time} with ${weather}. ` +
    `Frame the scene as ${style}. ` +
    `Keep the car exactly as it is — do not modify the car body, color, wheels, or any part of it. ` +
    `Use the provided mask to isolate only the background for replacement. ` +
    `Ensure cinematic quality, photorealistic lighting, correct ground reflections, ` +
    `and seamless blending where the car meets the road surface.`
  );
}

// ── Main export ──────────────────────────────────────────────────────────

export function buildPrompt(form: TuningFormState): string {
  if (form.customPromptOverride !== null) return form.customPromptOverride;
  return form.target === 'car'
    ? buildCarPrompt(form.car)
    : buildBackgroundPrompt(form.background);
}
