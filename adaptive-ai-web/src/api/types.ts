export type Complexity = 'low' | 'medium' | 'high';

export type PersonaType =
  | 'balanced'
  | 'educational'
  | 'technical'
  | 'concise'
  | 'creative'
  | 'professional'
  | 'researcher'
  | 'planner'
  | 'analyst';

export type ResponseLength = 'short' | 'medium' | 'detailed';
export type ExplanationStyle = 'simple' | 'balanced' | 'technical';

export interface BackendAnalysis {
  task_type: string;
  confidence?: number;
  complexity: Complexity;
  complexity_score?: number;
  selected_persona: string;
  persona_reason?: string;
  default_strategy?: string;
  selected_strategy: string;
  strategy_reason?: string;
  candidate_strategies?: string[];
  adaptation?: {
    method?: string;
    chosen?: string;
    reason?: string;
  };
  needs_clarification?: boolean;
  clarification_question?: string | null;
  risk_flags?: string[];
}

export interface BackendEvaluation {
  has_answer?: boolean;
  length_valid?: boolean;
  not_truncated?: boolean;
  no_secret_leak?: boolean;
  word_count?: number;
  strategy?: string;
  evaluation_status: 'passed' | 'passed_with_warnings' | 'review_required' | 'failed';
  quality_score: number;
  warnings?: string[];
  scope?: string;
}

export interface GenerationMeta {
  model?: string | null;
  latency_ms?: number | null;
  prompt_tokens?: number | null;
  completion_tokens?: number | null;
  finish_reason?: string | null;
  used_fallback_model?: boolean;
}

export interface AssistantRequest {
  message: string;
  session_id?: string | null;
  user_id?: string | null;
  preferred_persona?: PersonaType | null;
  response_length?: ResponseLength | null;
}

export interface AssistantResponse {
  status: 'completed' | 'needs_clarification';
  interaction_id?: string | null;
  session_id?: string | null;
  analysis: BackendAnalysis;
  answer?: string | null;
  evaluation?: BackendEvaluation | null;
  meta?: GenerationMeta | null;
}

export interface FeedbackRequest {
  interaction_id: string;
  session_id?: string | null;
  rating: number; // 1 to 5
  feedback_text?: string | null;
}

export interface UserPreferences {
  preferred_persona?: PersonaType | null;
  response_length?: ResponseLength | null;
  explanation_style?: ExplanationStyle | null;
}

export interface AScoreBreakdown {
  I: number;
  C: number;
  P: number;
  H: number;
  total: number;
}

export interface MessageItem {
  message_id: string;
  interaction_id?: string | null;
  session_id: string;
  role: 'user' | 'assistant';
  content: string;
  analysis?: BackendAnalysis;
  evaluation?: BackendEvaluation | null;
  meta?: GenerationMeta | null;
  a_score?: AScoreBreakdown;
  feedback_rating?: number | null;
  created_at: string;
}

export interface SessionSummary {
  session_id: string;
  title?: string;
  message_count?: number;
  last_message_at?: string;
  updated_at?: string;
  created_at?: string;
}
