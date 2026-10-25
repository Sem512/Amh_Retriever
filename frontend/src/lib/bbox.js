// Bounding boxes are NORMALIZED (0..1) relative to the page image the viewer
// displays (the preprocessed page image served by the backend), so they stay
// correct at any zoom level. Backend contract: { x, y, w, h } with the origin
// at the top-left corner of that image.
//
// A result carries `bboxes` (array of boxes, one per text line or block the
// passage covers). A single `bbox` is still accepted as a fallback.

export const clamp01 = (n) => Math.min(1, Math.max(0, Number.isFinite(n) ? n : 0));

export function clampBBox(b) {
  const x = clamp01(b.x);
  const y = clamp01(b.y);
  return { x, y, w: Math.min(clamp01(b.w), 1 - x), h: Math.min(clamp01(b.h), 1 - y) };
}

export function bboxToStyle(b) {
  const c = clampBBox(b);
  return {
    left: `${c.x * 100}%`,
    top: `${c.y * 100}%`,
    width: `${c.w * 100}%`,
    height: `${c.h * 100}%`,
  };
}

const isBox = (b) => b && typeof b === 'object' && ['x', 'y', 'w', 'h'].every((k) => Number.isFinite(b[k]));

// All boxes to draw for one search result: `bboxes` when it is a non-empty
// array, otherwise the single `bbox`. Malformed entries are skipped.
export function getBoxes(result) {
  if (Array.isArray(result?.bboxes) && result.bboxes.length > 0) return result.bboxes.filter(isBox);
  return isBox(result?.bbox) ? [result.bbox] : [];
}

// Convert a pixel box (e.g. Tesseract output) into a normalized box.
export function pixelsToBBox(px, pageWidth, pageHeight) {
  return clampBBox({
    x: px.left / pageWidth,
    y: px.top / pageHeight,
    w: px.width / pageWidth,
    h: px.height / pageHeight,
  });
}

export const formatScore = (s) => `${Math.round(clamp01(s) * 100)}%`;
