import { useCallback, useEffect, useRef, useState } from 'react';
import { api } from '../lib/api';
import { bboxToStyle, formatScore, getBoxes } from '../lib/bbox';
import { useI18n } from '../lib/i18n';

const ZOOMS = [0.6, 0.8, 1, 1.25, 1.5, 2, 2.5];

export default function DocumentViewer({ result, results, hasPrev, hasNext, onPrevResult, onNextResult, onClose }) {
  const { t } = useI18n();
  const [page, setPage] = useState(result.page);
  const [zoomIdx, setZoomIdx] = useState(2);
  const [img, setImg] = useState(null);
  const [state, setState] = useState('loading'); // loading | ready | error
  const [attempt, setAttempt] = useState(0);
  const activeRef = useRef(null);

  // Jump to the result's page whenever a different result is chosen.
  useEffect(() => setPage(result.page), [result.chunk_id, result.page]);

  // Load the page image.
  useEffect(() => {
    let cancelled = false;
    let url = null;
    setState('loading');
    api
      .getPageImage(result.doc_id, page)
      .then((u) => {
        if (cancelled) return;
        url = u;
        setImg(u);
        setState('ready');
      })
      .catch(() => !cancelled && setState('error'));
    return () => {
      cancelled = true;
      if (url?.startsWith('blob:')) URL.revokeObjectURL(url);
    };
  }, [result.doc_id, page, attempt]);

  // Scroll the highlighted passage into view once the image is shown.
  useEffect(() => {
    if (state === 'ready') activeRef.current?.scrollIntoView({ block: 'center', behavior: 'smooth' });
  }, [state, result.chunk_id, page, zoomIdx]);

  const onPage = results.filter((r) => r.doc_id === result.doc_id && r.page === page);
  const total = result.pages_total;
  const go = useCallback((n) => setPage((p) => Math.min(total, Math.max(1, p + n))), [total]);

  return (
    <section className="flex h-full flex-col bg-panel" aria-label={result.title}>
      <header className="flex flex-wrap items-center gap-2 border-b border-rule px-3 py-2">
        <button className="btn-ghost lg:hidden" onClick={onClose}>
          ← {t('back')}
        </button>
        <h2 className="order-last w-full truncate font-serif text-lg font-bold sm:order-none sm:w-auto sm:min-w-0 sm:flex-1">{result.title}</h2>
        <div className="flex items-center gap-1" role="group" aria-label={t('page')}>
          <button className="btn-ghost px-3" onClick={() => go(-1)} disabled={page <= 1} aria-label={t('prevPage')}>‹</button>
          <span className="min-w-[5.5rem] text-center text-sm tabular-nums">
            {t('page')} {page} {t('of')} {total}
          </span>
          <button className="btn-ghost px-3" onClick={() => go(1)} disabled={page >= total} aria-label={t('nextPage')}>›</button>
        </div>
        <div className="flex items-center gap-1" role="group" aria-label="Zoom">
          <button className="btn-ghost px-3" onClick={() => setZoomIdx((i) => Math.max(0, i - 1))} disabled={zoomIdx === 0} aria-label={t('zoomOut')}>−</button>
          <button className="btn-ghost px-2 text-xs" onClick={() => setZoomIdx(2)}>{Math.round(ZOOMS[zoomIdx] * 100)}%</button>
          <button className="btn-ghost px-3" onClick={() => setZoomIdx((i) => Math.min(ZOOMS.length - 1, i + 1))} disabled={zoomIdx === ZOOMS.length - 1} aria-label={t('zoomIn')}>+</button>
        </div>
      </header>

      <div className="relative min-h-0 flex-1 overflow-auto bg-[#D5DCD6] p-3 sm:p-5">
        {state === 'loading' && <p className="py-20 text-center text-mute" role="status">{t('loadingPage')}</p>}
        {state === 'error' && (
          <div className="py-20 text-center" role="alert">
            <p className="mb-3 text-danger">{t('errPage')}</p>
            <button className="btn-ghost" onClick={() => setAttempt((a) => a + 1)}>{t('retry')}</button>
          </div>
        )}
        {state === 'ready' && (
          <div className="relative mx-auto shadow-lg" style={{ width: `${ZOOMS[zoomIdx] * 100}%` }}>
            <img src={img} alt={`${result.title} — ${t('page')} ${page}`} className="block w-full select-none" draggable={false} />
            {onPage.flatMap((r) => {
              const active = r.chunk_id === result.chunk_id;
              // One rectangle per box; the first box of the active result is
              // the scroll target and carries the accessible label.
              return getBoxes(r).map((box, i) => (
                <div
                  key={`${r.chunk_id}-${i}`}
                  ref={active && i === 0 ? activeRef : null}
                  style={bboxToStyle(box)}
                  title={`${formatScore(r.score)} ${t('match')}`}
                  className={
                    active
                      ? 'absolute rounded-sm border-2 border-[#C58F00] bg-marker/40 mix-blend-multiply'
                      : 'absolute rounded-sm border border-marker bg-marker/15 mix-blend-multiply'
                  }
                  aria-label={active && i === 0 ? r.snippet : undefined}
                  data-chunk={r.chunk_id}
                  data-active={active ? 'true' : undefined}
                />
              ));
            })}
          </div>
        )}
      </div>

      <footer className="flex items-center justify-between gap-2 border-t border-rule px-3 py-2">
        <button className="btn-ghost" onClick={onPrevResult} disabled={!hasPrev}>‹ {t('prevResult')}</button>
        <button className="btn-ghost" onClick={onNextResult} disabled={!hasNext}>{t('nextResult')} ›</button>
      </footer>
    </section>
  );
}
