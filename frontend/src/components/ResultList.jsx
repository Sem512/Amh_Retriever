import { formatScore } from '../lib/bbox';
import { useI18n } from '../lib/i18n';

export default function ResultList({ results, activeId, onSelect }) {
  const { t } = useI18n();
  return (
    <ol className="divide-y divide-rule" aria-label={t('results')}>
      {results.map((r) => {
        const active = r.chunk_id === activeId;
        return (
          <li key={r.chunk_id}>
            <button
              onClick={() => onSelect(r)}
              aria-current={active ? 'true' : undefined}
              className={`block w-full px-4 py-3 text-left transition-colors hover:bg-archive-soft/60 ${active ? 'bg-archive-soft' : ''}`}
            >
              <div className="mb-1 flex items-baseline justify-between gap-3">
                <span className="truncate font-serif font-bold">{r.title}</span>
                <span className="shrink-0 text-xs tabular-nums text-mute">
                  {t('page')} {r.page}
                </span>
              </div>
              <p className="line-clamp-3 text-[15px] leading-relaxed text-ink/90">{r.snippet}</p>
              <div className="mt-2 flex items-center gap-2" aria-label={`${formatScore(r.score)} ${t('match')}`}>
                <div className="h-1.5 w-24 overflow-hidden rounded-full bg-rule">
                  <div className="h-full bg-archive" style={{ width: formatScore(r.score) }} />
                </div>
                <span className="text-xs tabular-nums text-mute">{formatScore(r.score)}</span>
              </div>
            </button>
          </li>
        );
      })}
    </ol>
  );
}
