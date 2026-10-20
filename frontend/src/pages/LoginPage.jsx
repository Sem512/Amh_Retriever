import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../lib/auth';
import { useI18n } from '../lib/i18n';
import { USE_MOCK } from '../lib/api';

export default function LoginPage() {
  const { t } = useI18n();
  const { login } = useAuth();
  const nav = useNavigate();
  const loc = useLocation();
  const [u, setU] = useState('');
  const [p, setP] = useState('');
  const [err, setErr] = useState('');
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setErr('');
    try {
      const user = await login(u.trim(), p);
      nav(user.role === 'admin' ? loc.state?.from || '/admin' : '/', { replace: true });
    } catch {
      setErr(t('loginFail'));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto w-full max-w-sm p-6 pt-16">
      <h1 className="mb-6 font-serif text-2xl font-bold">{t('loginTitle')}</h1>
      <form onSubmit={submit} className="space-y-4">
        <div>
          <label htmlFor="u" className="mb-1 block text-sm font-medium">{t('username')}</label>
          <input id="u" className="input" value={u} onChange={(e) => setU(e.target.value)} autoComplete="username" required />
        </div>
        <div>
          <label htmlFor="p" className="mb-1 block text-sm font-medium">{t('password')}</label>
          <input id="p" type="password" className="input" value={p} onChange={(e) => setP(e.target.value)} autoComplete="current-password" required />
        </div>
        {err && <p className="text-sm text-danger" role="alert">{err}</p>}
        <button className="btn-primary w-full" disabled={busy}>{t('login')}</button>
        {USE_MOCK && <p className="text-sm text-mute">{t('loginHint')}</p>}
      </form>
    </main>
  );
}
