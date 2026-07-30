import { Link, useLocation } from 'react-router-dom';
import { ThemeMode } from '../../hooks/useTheme';

const links = [
  { to: '/', label: 'Dashboard' },
  { to: '/simulator', label: 'Simulator' },
];

interface NavbarProps {
  theme: ThemeMode;
  onToggleTheme: () => void;
}

export function Navbar({ theme, onToggleTheme }: NavbarProps) {
  const location = useLocation();

  return (
    <nav style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem 1.5rem', borderBottom: '1px solid var(--border)' }}>
      <div style={{ fontWeight: 700, fontSize: '1.1rem' }}>Smart Classroom Edge AI</div>
      <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
        {links.map((link) => {
          const isActive = location.pathname === link.to;
          return (
            <Link
              key={link.to}
              to={link.to}
              className={isActive ? 'link-active' : ''}
              style={{ textDecoration: 'none', fontWeight: 600 }}
            >
              {link.label}
            </Link>
          );
        })}
        <button className="theme-toggle" onClick={onToggleTheme} type="button">
          {theme === 'dark' ? '☀️ Light' : '🌙 Dark'}
        </button>
      </div>
    </nav>
  );
}
