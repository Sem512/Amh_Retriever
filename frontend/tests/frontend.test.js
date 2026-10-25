import { describe, it, expect } from 'vitest';
import { bboxToStyle, clampBBox, formatScore, getBoxes, pixelsToBBox } from '../src/lib/bbox';
import { extractDetail, isAuthError } from '../src/lib/errors';
import { mockSearch } from '../src/lib/mockApi';

describe('bbox utilities', () => {
  it('converts a normalized box to percentage CSS', () => {
    expect(bboxToStyle({ x: 0.1, y: 0.2, w: 0.5, h: 0.25 })).toEqual({
      left: '10%', top: '20%', width: '50%', height: '25%',
    });
  });
  it('clamps boxes that overflow the page', () => {
    const c = clampBBox({ x: 0.8, y: -1, w: 0.9, h: 2 });
    expect(c.x + c.w).toBeLessThanOrEqual(1);
    expect(c.y).toBe(0);
    expect(c.h).toBeLessThanOrEqual(1);
  });
  it('normalizes OCR pixel boxes', () => {
    expect(pixelsToBBox({ left: 100, top: 200, width: 400, height: 100 }, 1000, 2000))
      .toEqual({ x: 0.1, y: 0.1, w: 0.4, h: 0.05 });
  });
  it('formats scores as percentages', () => {
    expect(formatScore(0.874)).toBe('87%');
    expect(formatScore(5)).toBe('100%');
  });
});

describe('mock search (contract check)', () => {
  it('returns results shaped like the API contract', () => {
    const [r] = mockSearch('የስራ ግብር መመሪያ');
    for (const k of ['chunk_id', 'doc_id', 'title', 'page', 'pages_total', 'score', 'snippet', 'bbox'])
      expect(r).toHaveProperty(k);
    expect(r.bbox).toEqual(expect.objectContaining({ x: expect.any(Number), w: expect.any(Number) }));
  });
  it('finds semantically related passages (ግብር ~ ገቢ)', () => {
    expect(mockSearch('የስራ ግብር መመሪያ').some((r) => r.doc_id === 'd1')).toBe(true);
  });
  it('returns nothing for an empty query', () => {
    expect(mockSearch('   ')).toEqual([]);
  });
});

describe('getBoxes (multiple boxes with single-box fallback)', () => {
  const A = { x: 0.1, y: 0.1, w: 0.5, h: 0.05 };
  const B = { x: 0.1, y: 0.2, w: 0.3, h: 0.05 };
  it('returns every box of a bboxes array, in order', () => {
    expect(getBoxes({ bboxes: [A, B] })).toEqual([A, B]);
  });
  it('prefers bboxes over bbox when both are present', () => {
    expect(getBoxes({ bboxes: [A], bbox: B })).toEqual([A]);
  });
  it('falls back to the single bbox', () => {
    expect(getBoxes({ bbox: A })).toEqual([A]);
  });
  it('falls back to bbox when bboxes is empty', () => {
    expect(getBoxes({ bboxes: [], bbox: A })).toEqual([A]);
  });
  it('skips malformed entries and returns [] when nothing is usable', () => {
    expect(getBoxes({ bboxes: [A, { x: 'a' }, null] })).toEqual([A]);
    expect(getBoxes({})).toEqual([]);
    expect(getBoxes(undefined)).toEqual([]);
  });
});

describe('extractDetail (backend error text)', () => {
  it('reads a FastAPI string detail from a JSON body', () => {
    expect(extractDetail('{"detail":"File is not a valid PDF"}', 'x')).toBe('File is not a valid PDF');
  });
  it('joins FastAPI validation messages', () => {
    expect(extractDetail({ detail: [{ msg: 'field required' }, { msg: 'bad type' }] }, 'x')).toBe('field required; bad type');
  });
  it('returns a plain-text body as is', () => {
    expect(extractDetail('Bad gateway', 'x')).toBe('Bad gateway');
  });
  it('uses the fallback when there is nothing to read', () => {
    expect(extractDetail('', 'Server Error')).toBe('Server Error');
    expect(extractDetail('{}', 'Server Error')).toBe('Server Error');
  });
  it('flags 401 and 403 as auth errors only', () => {
    expect(isAuthError({ status: 401 })).toBe(true);
    expect(isAuthError({ status: 403 })).toBe(true);
    expect(isAuthError({ status: 500 })).toBe(false);
    expect(isAuthError(null)).toBe(false);
  });
});

describe('mock search with multiple boxes', () => {
  it('returns bboxes for a multi-line passage and bbox for a single-box one', () => {
    const rs = mockSearch('የስራ ግብር መመሪያ');
    const multi = rs.find((r) => r.chunk_id === 'c3');
    const single = rs.find((r) => r.chunk_id === 'c1');
    expect(multi.bboxes).toHaveLength(2);
    expect(multi).not.toHaveProperty('bbox');
    expect(single).toHaveProperty('bbox');
    expect(getBoxes(multi)).toHaveLength(2);
    expect(getBoxes(single)).toHaveLength(1);
  });
});
