export const API_BASE = "http://localhost:8000";

export interface Session {
  id: string;
  topic: string;
  status: string;
  created_at?: string;
  depth?: string;
  language?: string;
}

export interface ResearchPayload {
  topic: string;
  additional_instructions?: string;
  depth: "basic" | "medium" | "deep";
  language: string;
}

async function jsonOrThrow<T>(res: Response): Promise<T> {
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

export const api = {
  startResearch: (body: ResearchPayload) =>
    fetch(`${API_BASE}/api/research`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(jsonOrThrow<{ id: string; session_id?: number }>),

  getSessions: () =>
    fetch(`${API_BASE}/api/sessions`)
      .then(jsonOrThrow<{ sessions: Session[]; total: number } | Session[]>)
      .then((data): Session[] =>
        Array.isArray(data) ? data : (data as { sessions: Session[] }).sessions || []
      ),

  getReport: async (id: string) => {
    const raw = await fetch(`${API_BASE}/api/research/${id}/report`).then(jsonOrThrow<any>);
    return {
      topic: raw.topic as string,
      // final_report fieldini oxu — köhnə report/content field-lərinə də bax
      report: (raw.final_report ?? raw.report ?? raw.content ?? "") as string,
      sources: (raw.sources ?? []) as {
        title?: string;
        url: string;
        type?: string;
        source_type?: string;
        credibility?: number;
        credibility_score?: number;
        snippet?: string;
      }[],
      stats: {
        tokens: raw.tiktoken_count ?? raw.token_count,
        sources: raw.sources_count ?? raw.sources?.length,
        duration_ms: raw.duration_ms,
        cost: raw.estimated_cost,
      },
      timeline: (raw.steps ?? raw.timeline ?? []) as {
        type: string;
        content?: string;
        tool?: string;
        tool_name?: string;
        timestamp?: string | number;
      }[],
    };
  },

  deleteSession: (id: string) =>
    fetch(`${API_BASE}/api/research/${id}`, { method: "DELETE" }),

  streamUrl: (id: string) => `${API_BASE}/api/research/${id}/stream`,
};