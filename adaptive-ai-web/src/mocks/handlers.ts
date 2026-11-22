import { http, HttpResponse } from 'msw';

export const handlers = [
  http.get('http://localhost:8000/health', () =>
    HttpResponse.json({ success: true, status: 'healthy', uptime_seconds: 120, database: 'sqlite_connected' })
  ),
  http.get('http://localhost:8000/health/model', () =>
    HttpResponse.json({
      success: true,
      provider: 'Google Gemini',
      model: 'gemini-2.0-flash',
      status: 'connected',
      credentials_exposed: false,
      note: 'Mocked Gemini connection active.',
    })
  ),
  http.post('http://localhost:8000/respond', async ({ request }) => {
    const body = (await request.json()) as { session_id: string; message: string };
    return HttpResponse.json({
      success: true,
      message_id: 'msg_mock_001',
      session_id: body.session_id,
      intent: 'education',
      complexity: 'medium',
      persona: 'teacher',
      strategy: 'step_by_step_explanation',
      response: `Mocked Adaptive AI response for: ${body.message}`,
      evaluation: {
        status: 'passed',
        format_compliant: true,
        overall_score: 0.92,
        dimensions: { relevance: 0.94, completeness: 0.91, clarity: 0.93, consistency: 0.90, format: 0.92 },
      },
      applied_preferences: { detail: 'balanced', style: 'step_by_step' },
      a_score: { I: 0.88, C: 0.78, P: 0.88, H: 0.65, total: 0.81 },
      latency_ms: 42,
      model: 'gemini-2.0-flash',
      created_at: new Date().toISOString(),
    });
  }),
];
