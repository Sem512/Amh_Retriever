// Turn a backend error body into one readable line.
// FastAPI sends { detail: "text" } for HTTPException and
// { detail: [{ loc, msg, type }, ...] } for validation errors.
export function extractDetail(body, fallback = '') {
  let data = body;
  if (typeof body === 'string') {
    try {
      data = JSON.parse(body);
    } catch {
      return body.trim().slice(0, 200) || fallback;
    }
  }
  const d = data?.detail ?? data?.message;
  if (typeof d === 'string' && d.trim()) return d.trim();
  if (Array.isArray(d)) {
    const msgs = d.map((x) => (typeof x === 'string' ? x : x?.msg)).filter(Boolean);
    if (msgs.length) return msgs.join('; ');
  }
  return fallback;
}

export const isAuthError = (e) => e?.status === 401 || e?.status === 403;
