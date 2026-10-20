import { useCallback, useMemo, useState } from 'react';
import { api } from '../lib/api';
import { useI18n } from '../lib/i18n';
import ResultList from '../components/ResultList';
import DocumentViewer from '../components/DocumentViewer';

export default function SearchPage() {
  const { t } = useI18n();
  const [q, setQ] = useState('');
  const [status, setStatus] = useState('idle'); // idle | loading | done | error
  const [data, setData] = useState(null);
  const [activeId, setActiveId] = useState(null);
  const [viewerOpen, setViewerOpen] = useState(false);

  const results = data?.results ?? [];
  const idx = useMemo(() => results.findIndex((r) => r.chunk_id === activeId), [results, activeId]);
  const active = idx >= 0 ? results[idx] : null;

  const submit = useCallback(
    async (e) => {
      e?.preventDefault();
      const query = q.trim();
      if (!query) return;
      setStatus('loading');
      try {
        const res = await api.search(query, 10);
        setData(res);
        setActiveId(res.results[0]?.chunk_id ?? null);
        setViewerOpen(false);
        setStatus('done');
      } catch {
        setStatus('error');
      }
    },
    [q]
  );

  const select = (r) => { setActiveId(r.chunk_id); setViewerOpen(true); };
  const step = (d) => { const n = results[idx + d]; if (n) setActiveId(n.chunk_id); };

  return (
    <div className="grid min-h-0 flex-1 lg:grid-cols-[minmax(340px,440px)_1fr]">
      <div className="flex min-h-0 flex-col border-r border-rule bg-panel">
        <form onSubmit={submit} className="border-b border-rule p-4" role="search">
          <label htmlFor="q" className="sr-only">{t('placeholder')}</label>
          <div className="flex gap-2">
            <input id="q" lang="am" value={q} onChange={(e) => setQ(e.target.value)} placeholder={t('placeholder')} className="input" autoComplete="off" />
            <button className="btn-primary" disabled={status === 'loading' || !q.trim()}>
              {status === 'loading' ? t('searching') : t('searchBtn')}
            </button>
          </div>
          {status === 'done' && (
            <p className="mt-2 text-sm text-mute" aria-live="polite">
              {results.length} {t('results')} · {t('took')} {data.took_ms} ms
            </p>
          )}
        </form>

        <div className="min-h-0 flex-1 overflow-y-auto">
          {status === 'idle' && (
            <div className="p-6">
              <h1 className="mb-2 font-serif text-2xl font-bold leading-snug">{t('heroTitle')}</h1>
              <p className="mb-4 max-w-prose text-mute">{t('heroBody')}</p>
              <button className="btn-ghost" onClick={() => setQ('የስራ ግብር መመሪያ')}>{t('emptyHint')}</button>
            </div>
          )}
          {status === 'error' && <p className="p-6 text-danger" role="alert">{t('errSearch')}</p>}
          {status === 'done' && results.length === 0 && <p className="p-6 text-mute">{t('noResults')}</p>}
          {results.length > 0 && <ResultList results={results} activeId={activeId} onSelect={select} />}
        </div>
      </div>

      <div className={`${viewerOpen ? 'fixed inset-0 z-30 bg-panel' : 'hidden'} min-h-0 lg:static lg:block`}>
        {active ? (
          <DocumentViewer
            result={active}
            results={results}
            hasPrev={idx > 0}
            hasNext={idx < results.length - 1}
            onPrevResult={() => step(-1)}
            onNextResult={() => step(1)}
            onClose={() => setViewerOpen(false)}
          />
        ) : (
          <div className="hidden h-full items-center justify-center text-mute lg:flex">{t('selectResult')}</div>
        )}
      </div>
    </div>
  );
}
