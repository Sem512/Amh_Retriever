// Single integration point with the FastAPI backend (Task 9, co-owned with Semir).
// If VITE_API_URL is empty the app runs against an in-browser mock so the UI can
// be demonstrated and tested without the backend.
import { mockApi } from './mockApi';

const BASE = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');
export const USE_MOCK = !BASE;

let token = sessionStorage.getItem('token');
export function setToken(t) {
  token = t;
  if (t) sessionStorage.setItem('token', t);
  else sessionStorage.removeItem('token');
}

async function request(path, opts = {}) {
  const headers = { ...(opts.headers || {}) };
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(`${BASE}${path}`, { ...opts, headers });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail || detail;
    } catch {
      /* non-JSON error body */
    }
    const err = new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
    err.status = res.status;
    throw err;
  }
  return res;
}

const json = (body) => ({
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body),
});

const real = {
  // POST /auth/login -> { access_token, token_type, role, username }
  async login(username, password) {
    return (await request('/auth/login', json({ username, password }))).json();
  },

  // GET /search?q=&k= -> { query, took_ms, results: [Result] }
  // Result = { chunk_id, doc_id, title, page, pages_total, score, snippet, bbox:{x,y,w,h} }
  async search(q, k = 10) {
    return (await request(`/search?q=${encodeURIComponent(q)}&k=${k}`)).json();
  },

  // GET /documents -> [{ id, title, pages, status, uploaded_at }]
  async listDocuments() {
    return (await request('/documents')).json();
  },

  // POST /documents (multipart: file) -> { id, status }
  uploadDocument(file, onProgress) {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open('POST', `${BASE}/documents`);
      if (token) xhr.setRequestHeader('Authorization', `Bearer ${token}`);
      xhr.upload.onprogress = (e) => e.lengthComputable && onProgress?.(e.loaded / e.total);
      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) resolve(JSON.parse(xhr.responseText));
        else reject(new Error(xhr.statusText || 'Upload failed'));
      };
      xhr.onerror = () => reject(new Error('Network error'));
      const form = new FormData();
      form.append('file', file);
      xhr.send(form);
    });
  },

  // DELETE /documents/{id}
  async deleteDocument(id) {
    await request(`/documents/${id}`, { method: 'DELETE' });
  },

  // GET /documents/{id}/pages/{n}/image -> image/png (rendered by pdf2image)
  // Fetched as a blob so the Authorization header can be sent.
  async getPageImage(docId, page) {
    const res = await request(`/documents/${docId}/pages/${page}/image`);
    return URL.createObjectURL(await res.blob());
  },
};

export const api = USE_MOCK ? mockApi : real;
