// In-browser mock of the backend so the frontend works stand-alone.
// Page images are drawn on a <canvas>, with each passage placed exactly inside
// its bounding box, so the highlight overlay can be verified visually.

const DOCS = [
  { id: 'd1', title: 'የገቢ ግብር አዋጅ', pages: 3, status: 'indexed', uploaded_at: '2026-09-02' },
  { id: 'd2', title: 'የሠራተኞች አስተዳደር መመሪያ', pages: 2, status: 'indexed', uploaded_at: '2026-09-05' },
  { id: 'd3', title: 'የዩኒቨርሲቲ ምርምር ማሳተሚያ መመሪያ', pages: 2, status: 'indexed', uploaded_at: '2026-09-09' },
];

// A chunk has either one `bbox` (legacy single box) or `bboxes` (one box per line,
// with `lines` holding the text drawn in each box).
const C = (id, doc_id, page, bbox, text, extra = {}) => ({ chunk_id: id, doc_id, page, bbox, text, ...extra });
const CHUNKS = [
  C('c1', 'd1', 1, { x: 0.1, y: 0.18, w: 0.8, h: 0.13 }, 'ማንኛውም ሰው ከስራ የሚያገኘው ገቢ በዚህ አዋጅ መሠረት የሥራ ግብር ይከፈልበታል።'),
  C('c2', 'd1', 1, { x: 0.1, y: 0.5, w: 0.8, h: 0.13 }, 'ግብር ከፋይ ዓመታዊ የገቢ መግለጫውን ከዓመቱ መጨረሻ በኋላ በአራት ወር ውስጥ ማቅረብ አለበት።'),
  C('c3', 'd1', 2, null, 'የገቢ ግብር ሕግ ከሚፈቅደው በላይ የዘገየ ክፍያ ተጨማሪ ቅጣት ያስከትላል።', {
    bboxes: [
      { x: 0.1, y: 0.28, w: 0.8, h: 0.045 },
      { x: 0.1, y: 0.325, w: 0.45, h: 0.045 },
    ],
    lines: ['የገቢ ግብር ሕግ ከሚፈቅደው በላይ የዘገየ ክፍያ', 'ተጨማሪ ቅጣት ያስከትላል።'],
  }),
  C('c4', 'd2', 1, { x: 0.1, y: 0.22, w: 0.8, h: 0.13 }, 'ሠራተኛው ዓመታዊ የዕረፍት ፈቃድ የማግኘት መብት አለው።'),
  C('c5', 'd2', 2, { x: 0.1, y: 0.4, w: 0.8, h: 0.13 }, 'የሥራ ስንብት ክፍያ ከአሠሪው በሕግ በተወሰነው መጠን ይከፈላል።'),
  C('c6', 'd3', 1, { x: 0.1, y: 0.3, w: 0.8, h: 0.13 }, 'ተማሪዎች የምረቃ ጽሑፋቸውን ለቤተ መጻሕፍት በዲጂታል ቅጂ ማስረከብ አለባቸው።'),
  C('c7', 'd3', 2, { x: 0.1, y: 0.2, w: 0.8, h: 0.13 }, 'የምርምር ሥራዎች ሥነ ምግባራዊ መርሆችን ማክበር አለባቸው።'),
];

// Tiny synonym groups imitating what dense embeddings add over keyword search.
const GROUPS = [
  ['ግብር', 'ታክስ', 'ገቢ', 'ቀረጥ'],
  ['ዕረፍት', 'ፈቃድ', 'ዕረፍት'],
  ['ክፍያ', 'ስንብት', 'ደመወዝ'],
  ['ምርምር', 'ጥናት', 'ምረቃ', 'ጽሑፍ'],
  ['መመሪያ', 'አዋጅ', 'ሕግ', 'ደንብ'],
];

const tokens = (s) => s.split(/[\s።፣፤፦፧,.?!]+/).filter(Boolean);
const group = (w) => GROUPS.findIndex((g) => g.includes(w));

export function mockSearch(query, k = 10) {
  const q = tokens(query);
  if (!q.length) return [];
  return CHUNKS.map((c) => {
    const words = tokens(c.text);
    let score = 0;
    for (const w of q) {
      if (words.some((x) => x.includes(w) || w.includes(x))) score += 1; // lexical
      else if (group(w) >= 0 && words.some((x) => group(x) === group(w))) score += 0.6; // semantic
    }
    return { c, score: score / q.length };
  })
    .filter((r) => r.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, k)
    .map(({ c, score }) => {
      const doc = DOCS.find((d) => d.id === c.doc_id);
      return {
        chunk_id: c.chunk_id,
        doc_id: c.doc_id,
        title: doc.title,
        page: c.page,
        pages_total: doc.pages,
        score: Math.min(0.99, 0.35 + score * 0.6),
        snippet: c.text,
        ...(c.bboxes ? { bboxes: c.bboxes } : { bbox: c.bbox }),
      };
    });
}

const wait = (ms) => new Promise((r) => setTimeout(r, ms));

// Behave like the real backend: admin calls need the token issued by login().
const httpError = (status, message) => Object.assign(new Error(message), { status });
const requireAdmin = () => {
  if (sessionStorage.getItem('token') !== 'mock-admin-token') throw httpError(401, 'Token expired or invalid');
};
let docs = [...DOCS];

async function drawPage(docId, page) {
  const W = 794;
  const H = 1123;
  const doc = docs.find((d) => d.id === docId);
  if (document.fonts?.load) {
    try {
      await document.fonts.load('26px "Noto Serif Ethiopic"', 'ሀ');
    } catch {
      /* fall back to default serif */
    }
  }
  const cv = document.createElement('canvas');
  cv.width = W;
  cv.height = H;
  const g = cv.getContext('2d');
  g.fillStyle = '#FFFFFF';
  g.fillRect(0, 0, W, H);
  g.strokeStyle = '#D9D9D9';
  g.strokeRect(24, 24, W - 48, H - 48);
  g.fillStyle = '#222';
  g.font = '700 30px "Noto Serif Ethiopic", serif';
  g.fillText(doc?.title ?? 'ሰነድ', 60, 90);
  g.font = '18px "Noto Serif Ethiopic", serif';
  g.fillStyle = '#777';
  g.fillText(String(page), W / 2 - 4, H - 50);

  // filler "text lines"
  g.fillStyle = '#E6E6E6';
  for (let y = 140; y < H - 100; y += 26) g.fillRect(60, y, W - 120 - ((y * 7) % 160), 8);

  for (const c of CHUNKS.filter((x) => x.doc_id === docId && x.page === page)) {
    if (c.bboxes) {
      c.bboxes.forEach((b, i) => {
        g.fillStyle = '#FFFFFF';
        g.fillRect(b.x * W - 6, b.y * H - 4, b.w * W + 12, b.h * H + 8);
        g.fillStyle = '#111';
        g.font = '26px "Noto Serif Ethiopic", serif';
        g.fillText(c.lines[i], b.x * W, b.y * H + 30);
      });
      continue;
    }
    const bx = c.bbox.x * W;
    const by = c.bbox.y * H;
    const bw = c.bbox.w * W;
    g.fillStyle = '#FFFFFF';
    g.fillRect(bx - 6, by - 6, bw + 12, c.bbox.h * H + 12);
    g.fillStyle = '#111';
    g.font = '26px "Noto Serif Ethiopic", serif';
    let line = '';
    let y = by + 28;
    for (const w of c.text.split(' ')) {
      const t = line ? `${line} ${w}` : w;
      if (g.measureText(t).width > bw && line) {
        g.fillText(line, bx, y);
        line = w;
        y += 38;
      } else line = t;
    }
    g.fillText(line, bx, y);
  }
  return cv.toDataURL('image/png');
}

export const mockApi = {
  async login(username, password) {
    await wait(300);
    if (username === 'admin' && password === 'admin123')
      return { access_token: 'mock-admin-token', role: 'admin', username };
    const e = new Error('Invalid credentials');
    e.status = 401;
    throw e;
  },
  async search(q, k = 10) {
    const t = performance.now();
    await wait(350);
    return { query: q, took_ms: Math.round(performance.now() - t), results: mockSearch(q, k) };
  },
  async listDocuments() {
    await wait(150);
    requireAdmin();
    return docs.map((d) => ({ ...d }));
  },
  async uploadDocument(file, onProgress) {
    requireAdmin();
    for (let i = 1; i <= 5; i++) {
      await wait(120);
      onProgress?.(i / 5);
    }
    // Failures the real backend can report (its `detail` text reaches the user).
    if (file.size === 0) throw httpError(422, 'The uploaded file is empty');
    if (/fail/i.test(file.name)) throw httpError(503, 'OCR service unavailable: could not read page 1');
    const id = `d${Date.now()}`;
    docs = [
      { id, title: file.name.replace(/\.[^.]+$/, ''), pages: 1, status: 'processing', uploaded_at: new Date().toISOString().slice(0, 10) },
      ...docs,
    ];
    setTimeout(() => {
      docs = docs.map((d) => (d.id === id ? { ...d, status: 'indexed' } : d));
    }, 4000);
    return { id, status: 'processing' };
  },
  async deleteDocument(id) {
    await wait(150);
    requireAdmin();
    if (docs.find((d) => d.id === id)?.status === 'processing')
      throw httpError(409, 'Document is still being indexed and cannot be deleted yet');
    docs = docs.filter((d) => d.id !== id);
  },
  async getPageImage(docId, page) {
    await wait(120);
    return drawPage(docId, page);
  },
};
