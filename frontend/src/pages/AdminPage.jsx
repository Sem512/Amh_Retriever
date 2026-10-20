import { useCallback, useEffect, useState } from 'react';
import { api } from '../lib/api';
import { useI18n } from '../lib/i18n';
import UploadDropzone from '../components/UploadDropzone';

const BADGE = {
  queued: ['statusQueued', 'bg-rule text-ink'],
  processing: ['statusProcessing', 'bg-marker/30 text-ink'],
  indexed: ['statusIndexed', 'bg-archive-soft text-archive-dark'],
  failed: ['statusFailed', 'bg-danger/10 text-danger'],
};

export default function AdminPage() {
  const { t } = useI18n();
  const [docs, setDocs] = useState(null);

  const load = useCallback(() => api.listDocuments().then(setDocs).catch(() => setDocs([])), []);
  useEffect(() => { load(); }, [load]);

  // Poll while any document is still being processed.
  const busy = docs?.some((d) => d.status === 'queued' || d.status === 'processing');
  useEffect(() => {
    if (!busy) return;
    const id = setInterval(load, 2500);
    return () => clearInterval(id);
  }, [busy, load]);

  async function remove(d) {
    if (!window.confirm(`${t('confirmDelete')}\n\n${d.title}`)) return;
    await api.deleteDocument(d.id);
    load();
  }

  return (
    <main className="mx-auto w-full max-w-4xl space-y-8 overflow-y-auto p-4 sm:p-8">
      <section>
        <h1 className="mb-3 font-serif text-2xl font-bold">{t('uploadTitle')}</h1>
        <UploadDropzone onUploaded={load} />
      </section>
      <section>
        <h2 className="mb-3 font-serif text-xl font-bold">{t('documents')}</h2>
        {docs && docs.length === 0 ? (
          <p className="text-mute">{t('noDocs')}</p>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-rule bg-panel">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-rule bg-paper">
                <tr>
                  <th className="px-4 py-2 font-medium">{t('colTitle')}</th>
                  <th className="px-4 py-2 font-medium">{t('colPages')}</th>
                  <th className="px-4 py-2 font-medium">{t('colStatus')}</th>
                  <th className="px-4 py-2 font-medium">{t('colAdded')}</th>
                  <th className="px-4 py-2"><span className="sr-only">{t('delete')}</span></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-rule">
                {(docs ?? []).map((d) => {
                  const [k, cls] = BADGE[d.status] ?? BADGE.queued;
                  return (
                    <tr key={d.id}>
                      <td className="px-4 py-3 font-serif font-bold">{d.title}</td>
                      <td className="px-4 py-3 tabular-nums">{d.pages}</td>
                      <td className="px-4 py-3"><span className={`rounded-full px-2.5 py-1 text-xs font-medium ${cls}`}>{t(k)}</span></td>
                      <td className="px-4 py-3 tabular-nums text-mute">{d.uploaded_at}</td>
                      <td className="px-4 py-3 text-right"><button className="btn-danger py-1.5" onClick={() => remove(d)}>{t('delete')}</button></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </main>
  );
}
