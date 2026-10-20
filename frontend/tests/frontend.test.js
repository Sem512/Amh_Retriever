import { describe, it, expect } from 'vitest';
import { bboxToStyle, clampBBox, formatScore, pixelsToBBox } from '../src/lib/bbox';
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
