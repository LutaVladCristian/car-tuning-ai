import { useReducer, useMemo, useState, type FormEvent } from 'react';
import { tuningReducer } from '../components/tuning/tuningReducer';
import { DEFAULT_FORM_STATE } from '../types/tuning';
import type { ImageSourceType } from '../types/tuning';
import { buildPrompt } from '../lib/promptBuilder';
import { useEditPhoto } from '../hooks/useEditPhoto';
import { usePhotoHistory } from '../hooks/usePhotoHistory';
import { getPhotoBlob } from '../api/photos';

import TuningForm from '../components/tuning/TuningForm';
import ImageSelector from '../components/tuning/ImageSelector';
import PromptPreview from '../components/prompt/PromptPreview';
import ResultDisplay from '../components/results/ResultDisplay';
import PhotoHistoryPanel from '../components/results/PhotoHistoryPanel';

export default function TuningPage() {
  const [formState, dispatch] = useReducer(tuningReducer, DEFAULT_FORM_STATE);
  const [imageSource, setImageSource] = useState<ImageSourceType>('upload');
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [selectedHistoryPhotoId, setSelectedHistoryPhotoId] = useState<number | null>(null);

  const { photos, total, isLoading: historyLoading, hasMore, refetch, fetchMore } = usePhotoHistory();
  const { status, resultPhotoId, error, submit, reset } = useEditPhoto(refetch);

  const prompt = useMemo(() => buildPrompt(formState), [formState]);
  const isSubmitting = status === 'submitting' || status === 'polling';
  const canSubmit = !isSubmitting && (
    (imageSource === 'upload' && uploadedFile !== null) ||
    (imageSource === 'history' && selectedHistoryPhotoId !== null)
  );

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;

    let fileToSend: File | Blob;
    if (imageSource === 'upload' && uploadedFile) {
      fileToSend = uploadedFile;
    } else if (imageSource === 'history' && selectedHistoryPhotoId !== null) {
      fileToSend = await getPhotoBlob(selectedHistoryPhotoId);
    } else {
      return;
    }

    await submit(fileToSend, prompt, formState.target === 'car');
  };

  const handleHistorySelect = (id: number) => {
    setSelectedHistoryPhotoId(id);
  };

  return (
    <div className="min-h-screen bg-surface-900">
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="mb-6">
          <h2 className="text-xl font-bold text-zinc-100">Car Tuning Studio</h2>
          <p className="text-zinc-500 text-sm mt-1">
            Upload a car photo, configure modifications, and let AI generate the result.
          </p>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="grid grid-cols-1 lg:grid-cols-[1fr_420px] gap-6">
            {/* Left column: controls */}
            <div className="space-y-6">
              {/* Image selection */}
              <div className="bg-surface-800 border border-surface-600 rounded-xl p-5 space-y-4">
                <h3 className="text-sm font-semibold text-zinc-300">Select Image</h3>
                <ImageSelector
                  imageSource={imageSource}
                  uploadedFile={uploadedFile}
                  selectedHistoryPhotoId={selectedHistoryPhotoId}
                  historyPhotos={photos}
                  onSourceChange={setImageSource}
                  onFileUpload={setUploadedFile}
                  onHistorySelect={(id) => {
                    setSelectedHistoryPhotoId(id);
                    setImageSource('history');
                  }}
                />
              </div>

              {/* Tuning form */}
              <div className="bg-surface-800 border border-surface-600 rounded-xl p-5">
                <TuningForm formState={formState} dispatch={dispatch} />
              </div>

              {/* Prompt preview */}
              <div className="bg-surface-800 border border-surface-600 rounded-xl p-5">
                <PromptPreview
                  prompt={prompt}
                  isOverridden={formState.customPromptOverride !== null}
                  onChange={(v) => dispatch({ type: 'SET_CUSTOM_PROMPT', value: v })}
                  onReset={() => dispatch({ type: 'RESET_PROMPT_OVERRIDE' })}
                />
              </div>

              {/* Submit */}
              <button
                type="submit"
                disabled={!canSubmit}
                className={`w-full py-3 rounded-xl font-semibold text-sm transition-all ${
                  formState.target === 'car'
                    ? 'bg-accent-blue hover:bg-blue-400 shadow-glow-blue'
                    : 'bg-accent-orange hover:bg-orange-400 shadow-glow-orange'
                } text-white disabled:opacity-40 disabled:cursor-not-allowed disabled:shadow-none`}
              >
                {isSubmitting
                  ? status === 'submitting'
                    ? 'Processing with AI...'
                    : 'Saving...'
                  : `Generate ${formState.target === 'car' ? 'Car Edit' : 'Background'}`}
              </button>

              {!uploadedFile && imageSource === 'upload' && (
                <p className="text-center text-zinc-600 text-xs -mt-3">
                  Upload an image to enable generation
                </p>
              )}
            </div>

            {/* Right column: result + history */}
            <div className="space-y-6">
              <div className="bg-surface-800 border border-surface-600 rounded-xl p-5">
                <ResultDisplay
                  status={status}
                  resultPhotoId={resultPhotoId}
                  error={error}
                  onReset={reset}
                />
              </div>

              <div className="bg-surface-800 border border-surface-600 rounded-xl p-5">
                <PhotoHistoryPanel
                  photos={photos}
                  total={total}
                  isLoading={historyLoading}
                  hasMore={hasMore}
                  onLoadMore={fetchMore}
                  onSelectPhoto={handleHistorySelect}
                />
              </div>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
