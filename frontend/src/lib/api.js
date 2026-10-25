// Single integration point with the FastAPI backend (Task 9, co-owned with Semir).
// If VITE_API_URL is empty the app runs against an in-browser mock so the UI can
// be demonstrated and tested without the backend.
import { mockApi } from './mockApi';
import { extractDetail, isAuthError } from './errors';

const BASE = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');
export const USE_MOCK = !BASE;

let token = sessionStorage.getItem('token');
export function setToken(t) {
  token = t;
  if (t) sessionStorage.setItem('token', t);
  else sessionStorage.removeItem('token');
}

// Called when an authenticated request is rejected with 401 or 403
// (expired, invalid or insufficient token). AuthProvider registers it.
let onUnauthorized = null;
export function setUnauthorizedHandler(fn) {
  onUnauthorized = fn;
}

function httpError(status, detail) {
  const err = new Error(detail);
  err.status = status;
  return err;
}

async function request(path, opts = {}) {
  const headers = { ...(opts.headers || {}) };
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(`${BASE}${path}`, { ...opts, headers });
  if (!res.ok) {
    let body = '';
    try {
      body = await res.text();
    } catch {
      /* unreadable body */
    }
    throw httpError(res.status, extractDetail(body, res.statusText || `HTTP ${res.status}`));
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
  // Result = { chunk_id, doc_id, title, page, pages_total, score, snippet,
  //            bboxes: [{x,y,w,h}, ...] }   (normalized 0-1; legacy single `bbox` still accepted)
  async search(q, k = 10) {
    return (await request(`/search?q=${encodeURIComponent(q)}&k=${k}`)).json();
  },

  // GET /documents -> [{ id, title, pages, status, uploaded_at }]
  async listDocuments() {
    return (await request('/documents')).json();
  },

  // POST /documents (multipart: file) -> { id, status }
  // On failure the error message is the backend's `detail`.
  uploadDocument(file, onProgress) {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open('POST', `${BASE}/documents`);
      if (token) xhr.setRequestHeader('Authorization', `Bearer ${token}`);
      xhr.upload.onprogress = (e) => e.lengthComputable && onProgress?.(e.loaded / e.total);
      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            resolve(JSON.parse(xhr.responseText));
          } catch {
            reject(httpError(xhr.status, 'Unexpected response from the server'));
          }
        } else {
          reject(httpError(xhr.status, extractDetail(xhr.responseText, xhr.statusText || `HTTP ${xhr.status}`)));
        }
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

  // GET /documents/{id}/pages/{n}/image -> image/png (the preprocessed page image
  // that the OCR boxes refer to). Fetched as a blob so the Authorization header can be sent.
  async getPageImage(docId, page) {
    const res = await request(`/documents/${docId}/pages/${page}/image`);
    return URL.createObjectURL(await res.blob());
  },
};

// On 401/403 from an authenticated call: clear the session and send the user to
// the login page (via onUnauthorized), then still rethrow so callers can stop.
// Login itself is excluded: a wrong password is a 401 that must stay on the form.
function guard(impl) {
  const out = {};
  for (const [name, fn] of Object.entries(impl)) {
    out[name] = async (...args) => {
      try {
        return await fn(...args);
      } catch (e) {
        if (name !== 'login' && token && isAuthError(e)) onUnauthorized?.(e);
        throw e;
      }
    };
  }
  return out;
}

export const api = guard(USE_MOCK ? mockApi : real);
