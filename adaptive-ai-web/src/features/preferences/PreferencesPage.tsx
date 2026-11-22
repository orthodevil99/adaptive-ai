import React, { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { usePreferences, useResetPreferences, useUpdatePreferences } from '../../hooks/useAdaptiveApi';
import { useAppStore } from '../../store/useAppStore';
import type { ExplanationStyle, PersonaType, ResponseLength } from '../../api/types';
import { GlassCard } from '../../components/glass/GlassCard';
import { GlassButton } from '../../components/glass/GlassButton';

interface PrefsForm {
  preferred_persona: PersonaType | '';
  response_length: ResponseLength;
  explanation_style: ExplanationStyle;
  theme: 'dark' | 'light';
}

export const PreferencesPage: React.FC = () => {
  const { userId, theme, setTheme, setQuickPreferences } = useAppStore();
  const { data } = usePreferences(userId);
  const updateMut = useUpdatePreferences(userId);
  const resetMut = useResetPreferences(userId);

  const { register, handleSubmit, reset } = useForm<PrefsForm>({
    defaultValues: {
      preferred_persona: '',
      response_length: 'medium',
      explanation_style: 'balanced',
      theme,
    },
  });

  useEffect(() => {
    if (data?.preferences) {
      reset({
        preferred_persona: data.preferences.preferred_persona || '',
        response_length: data.preferences.response_length || 'medium',
        explanation_style: data.preferences.explanation_style || 'balanced',
        theme,
      });
    }
  }, [data, reset, theme]);

  const onSubmit = (values: PrefsForm) => {
    setTheme(values.theme);
    const payload = {
      preferred_persona: (values.preferred_persona || null) as PersonaType | null,
      response_length: values.response_length,
      explanation_style: values.explanation_style,
    };
    updateMut.mutate(payload, {
      onSuccess: () => {
        setQuickPreferences({
          preferred_persona: payload.preferred_persona,
          response_length: payload.response_length,
        });
      },
    });
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-6 md:p-8">
      <div>
        <h1 className="text-2xl font-bold">Preferences</h1>
        <p className="text-sm opacity-75">Persisted to <code>/api/v1/preferences/{userId}</code>.</p>
      </div>

      <GlassCard level="elevated" className="p-6">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 text-sm">
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-xs opacity-75">Preferred Persona</label>
              <select {...register('preferred_persona')} className="glass w-full rounded-xl px-3 py-2 outline-none">
                <option value="">Auto (Adaptive)</option>
                <option value="educational">Educational</option>
                <option value="technical">Technical</option>
                <option value="researcher">Researcher</option>
                <option value="planner">Planner</option>
                <option value="analyst">Analyst</option>
                <option value="creative">Creative</option>
                <option value="concise">Concise</option>
                <option value="professional">Professional</option>
                <option value="balanced">Balanced</option>
              </select>
            </div>
            <div>
              <label className="mb-1 block text-xs opacity-75">Response Length</label>
              <select {...register('response_length')} className="glass w-full rounded-xl px-3 py-2 outline-none">
                <option value="short">Short</option>
                <option value="medium">Medium</option>
                <option value="detailed">Detailed</option>
              </select>
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-xs opacity-75">Explanation Style</label>
              <select {...register('explanation_style')} className="glass w-full rounded-xl px-3 py-2 outline-none">
                <option value="simple">Simple</option>
                <option value="balanced">Balanced</option>
                <option value="technical">Technical</option>
              </select>
            </div>
            <div>
              <label className="mb-1 block text-xs opacity-75">Glass Theme</label>
              <select {...register('theme')} className="glass w-full rounded-xl px-3 py-2 outline-none">
                <option value="dark">Dark Circuit Glass (Default)</option>
                <option value="light">Light Glass</option>
              </select>
            </div>
          </div>

          <div className="flex items-center gap-3 pt-2">
            <GlassButton type="submit" disabled={updateMut.isPending}>
              {updateMut.isPending ? 'Saving...' : 'Save Preferences'}
            </GlassButton>
            <GlassButton type="button" variant="secondary" onClick={() => resetMut.mutate()}>
              Reset Defaults
            </GlassButton>
            {updateMut.isSuccess && <span className="text-xs text-[#2EC4B6]">Saved!</span>}
          </div>
        </form>
      </GlassCard>
    </div>
  );
};
