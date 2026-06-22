const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type DocumentRow = {
  id: number;
  filename: string;
  content_type: string;
  num_chunks: number;
  created_at: string;
};

export type Citation = {
  marker: number;
  chunk_id: number;
  document_id: number;
  filename: string;
  page: number | null;
  score: number;
  snippet: string;
};

export type ChatResponse = {
  answer: string;
  citations: Citation[];
};

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || JSON.stringify(body);
    } catch {
      // ignore
    }
    throw new Error(`${res.status} ${detail}`);
  }
  return (await res.json()) as T;
}

export async function listDocuments(): Promise<DocumentRow[]> {
  const res = await fetch(`${API_URL}/documents`, { cache: "no-store" });
  return handle<DocumentRow[]>(res);
}

export async function uploadDocument(file: File): Promise<DocumentRow> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_URL}/documents`, { method: "POST", body: form });
  return handle<DocumentRow>(res);
}

export async function deleteDocument(id: number): Promise<void> {
  const res = await fetch(`${API_URL}/documents/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
}

export async function chat(question: string): Promise<ChatResponse> {
  const res = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  return handle<ChatResponse>(res);
}
