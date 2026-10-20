import { Link, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../lib/auth';
import { useI18n } from '../lib/i18n';
import { USE_MOCK } from '../lib/api';

export default function Header() {
  const { t, toggle } = useI18n();
  const { user, isAdmin, logout } = useAuth();
  const nav = useNavigate();
  const link = ({ isActive }) =>
    `rounded-md px-3 py-2 text-sm font-medium ${isActive ? 'bg-archive text-white' : 'text-ink hover:bg-archive-soft'}`;
  return (
    <header className="flex flex-wrap items-center gap-2 border-b border-rule bg-panel px-4 py-2">
      <Link to="/" className="mr-3 font-serif text-xl font-bold text-archive">
        {t('appName')}
      </Link>
      <nav className="flex flex-1 items-center gap-1" aria-label="Main">
        <NavLink to="/" end className={link}>{t('search')}</NavLink>
        {isAdmin && <NavLink to="/admin" className={link}>{t('admin')}</NavLink>}
      </nav>
      {USE_MOCK && <span className="rounded bg-marker/30 px-2 py-1 text-xs">Demo</span>}
      <button className="btn-ghost py-1.5" onClick={toggle}>{t('language')}</button>
      {user ? (
        <button className="btn-ghost py-1.5" onClick={() => { logout(); nav('/'); }}>{t('logout')} ({user.username})</button>
      ) : (
        <Link className="btn-primary py-1.5" to="/login">{t('login')}</Link>
      )}
    </header>
  );
}
