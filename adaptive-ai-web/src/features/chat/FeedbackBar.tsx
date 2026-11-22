import React, { useState } from 'react';
import { AlertTriangle, CheckCircle2, RefreshCw, Star } from 'lucide-react';
import type { MessageItem } from '../../api/types';
import { useFeedback } from '../../hooks/useAdaptiveApi';
import { GlassButton } from '../../components/glass/GlassButton';

interface Props {
  message: MessageItem;
  onRegenerate: () => void;
}

export const FeedbackBar: React.FC<Props> = ({ message, onRegenerate }) => {
  const [rating, setRating] = useState<number>(message.feedback_rating || 0);
  const [showText, setShowText] = useState(false);
  const [feedbackText, setFeedbackText] = useState('');
  const [adaptationNote, setAdaptationNote] = useState<string | null>(null);
  const feedbackMut = useFeedback();

  const submitRating = (stars: number) => {
    if (!message.interaction_id) return;
    setRating(stars);
    if (stars <= 3) setShowText(true);
    feedbackMut.mutate(
      {
        interaction_id: message.interaction_id,
        session_id: message.session_id,
        rating: stars,
        feedback_text: feedbackText.trim() || undefined,
      },
      {
        onSuccess: (res) => setAdaptationNote(res.adaptation || 'Feedback recorded for Thompson adaptation.'),
      }
    );
  };

  const evStatus = message.evaluation?.evaluation_status;
  const passed = evStatus === 'passed' || evStatus === 'passed_with_warnings' || !evStatus;

  return (
    <div className="mt-3 border-t border-white/10 pt-2.5">
      <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
        <div className="flex items-center gap-2">
          {passed ? (
            <span className="inline-flex items-center gap-1 rounded-full bg-[#2EC4B6]/15 px-2.5 py-0.5 font-medium text-[#2EC4B6]">
              <CheckCircle2 className="h-3.5 w-3.5" />
              {evStatus === 'passed_with_warnings' ? 'Passed (Warnings)' : 'Evaluation Passed'}
              {message.evaluation?.quality_score !== undefined &&
                ` (${Math.round(message.evaluation.quality_score * 100)}%)`}
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 rounded-full border border-amber-400/60 px-2.5 py-0.5 font-medium text-amber-300">
              <AlertTriangle className="h-3.5 w-3.5" /> Needs Review
            </span>
          )}
          <button
            onClick={onRegenerate}
            className="inline-flex items-center gap-1 rounded-lg px-2 py-1 text-xs opacity-80 hover:bg-white/10 hover:opacity-100"
          >
            <RefreshCw className="h-3 w-3" /> Regenerate
          </button>
        </div>

        {message.interaction_id && (
          <div className="flex items-center gap-1" title="Rate 1–5 to train Thompson-sampling adaptation">
            {[1, 2, 3, 4, 5].map((star) => (
              <button
                key={star}
                onClick={() => submitRating(star)}
                disabled={feedbackMut.isPending || Boolean(adaptationNote)}
                aria-label={`Rate ${star} out of 5`}
                className="rounded p-1 transition hover:bg-white/10 disabled:opacity-60"
              >
                <Star
                  className={`h-3.5 w-3.5 ${
                    star <= rating ? 'fill-[#2EC4B6] text-[#2EC4B6]' : 'opacity-50'
                  }`}
                />
              </button>
            ))}
          </div>
        )}
      </div>

      {adaptationNote && (
        <div className="mt-1.5 text-[11px] text-[#2EC4B6]">{adaptationNote}</div>
      )}

      {showText && !adaptationNote && (
        <div className="mt-2 flex gap-2">
          <input
            value={feedbackText}
            onChange={(e) => setFeedbackText(e.target.value)}
            placeholder="Optional note on how to improve..."
            className="glass flex-1 rounded-xl px-3 py-1.5 text-xs outline-none focus:border-[#6C63FF]"
          />
          <GlassButton onClick={() => submitRating(rating || 3)} className="px-3 py-1.5 text-xs">
            Send
          </GlassButton>
        </div>
      )}
    </div>
  );
};
