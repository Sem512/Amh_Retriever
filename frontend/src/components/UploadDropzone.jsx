import { useRef, useState } from 'react';
import { api } from '../lib/api';
import { useI18n } from '../lib/i18n';

const OK = ['application/pdf', 'image/png', 'image/jpeg'];
const MAX = 50 * 1024 * 1024;

export default function UploadDropzone({ onUploaded }) {
  const { t } = useI18n();
  const inputRef = useRef(null);
  const [over, setOver] = useState(false);
  const [jobs, setJobs] = useState([]); // {name, progress, error}

  const patch = (name, p) => setJobs((j) => j.map((x) => (x.name === name ? { ...x, ...p } : x)));

  async function handle(files) {
    for (const f of files) {
      if (!OK.includes(f.type)) {
        setJobs((j) => [...j, { name: f.name, progress: 0, error: t('uploadBadType') }]);
        continue;
      }
      if (f.size > MAX) {
        setJobs((j) => [...j, { name: f.name, progress: 0, error: t('uploadTooBig') }]);
        continue;
      }
      setJobs((j) => [...j, { name: f.name, progress: 0 }]);
      try {
        await api.uploadDocument(f, (p) => patch(f.name, { progress: p }));
        patch(f.name, { progress: 1, done: true });
        onUploaded?.();
      } catch (e) {
        patch(f.name, { error: e.message });
      }
    }
  }

  return (
    <div>
      <div
        onDragOver={(e) => { e.preventDefault(); setOver(true); }}
        onDragLeave={() => setOver(false)}
        onDrop={(e) => { e.preventDefault(); setOver(false); handle([...e.dataTransfer.files]); }}
        className={`rounded-lg border-2 border-dashed px-6 py-10 text-center transition-colors ${over ? 'border-archive bg-archive-soft' : 'border-rule bg-panel'}`}
      >
        <p className="mb-1 font-medium">{t('uploadDrop')}</p>
        <p className="mb-4 text-sm text-mute">{t('uploadTypes')}</p>
        <button className="btn-primary" onClick={() => inputRef.current?.click()}>{t('uploadChoose')}</button>
        <input ref={inputRef} type="file" multiple accept=".pdf,.png,.jpg,.jpeg" className="sr-only" aria-label={t('uploadChoose')}
          onChange={(e) => { handle([...e.target.files]); e.target.value = ''; }} />
      </div>
      {jobs.length > 0 && (
        <ul className="mt-3 space-y-2" aria-live="polite">
          {jobs.map((j, i) => (
            <li key={`${j.name}-${i}`} className="rounded-md border border-rule bg-panel px-3 py-2 text-sm">
              <div className="flex justify-between gap-3">
                <span className="truncate">{j.name}</span>
                <span className={j.error ? 'text-danger' : 'text-mute'}>{j.error ?? `${Math.round(j.progress * 100)}%`}</span>
              </div>
              {!j.error && (
                <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-rule">
                  <div className="h-full bg-archive transition-all" style={{ width: `${j.progress * 100}%` }} />
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
