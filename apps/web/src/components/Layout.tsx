import { NavLink, Outlet, useNavigate } from 'react-router-dom';

const NAV = [
    { to: '/', label: 'Accueil', icon: '🏠' },
    { to: '/backlog', label: 'Backlog', icon: '🗂️' },
    { to: '/new', label: 'Créer', icon: '➕' },
    { to: '/projects', label: 'Projets', icon: '📦' },
    { to: '/approvals', label: 'Validations', icon: '✅' },
    { to: '/settings', label: 'Réglages', icon: '⚙️' },
];

export function Layout() {
    const navigate = useNavigate();
    return (
        <div className="mx-auto flex min-h-full max-w-md flex-col pb-24">
            <header className="sticky top-0 z-10 flex items-center justify-between bg-surface/80 px-5 pb-3 pt-6 backdrop-blur">
                <div>
                    <p className="text-xs uppercase tracking-widest text-white/40">AI Dev Factory</p>
                    <h1 className="title-xl">Pilotage</h1>
                </div>
                <button
                    className="btn-primary !px-4 !py-2"
                    onClick={() => navigate('/new')}
                    aria-label="Nouvelle demande"
                >
                    + Demande
                </button>
            </header>

            <main className="flex-1 space-y-4 px-4">
                <Outlet />
            </main>

            <nav className="fixed inset-x-0 bottom-0 z-20 mx-auto flex max-w-md items-center justify-around border-t border-white/10 bg-surface/95 px-2 py-2 backdrop-blur">
                {NAV.map((item) => (
                    <NavLink
                        key={item.to}
                        to={item.to}
                        end={item.to === '/'}
                        className={({ isActive }) =>
                            `flex flex-col items-center gap-0.5 rounded-xl px-3 py-1 text-[11px] ${isActive ? 'text-accent' : 'text-white/50'
                            }`
                        }
                    >
                        <span className="text-lg">{item.icon}</span>
                        {item.label}
                    </NavLink>
                ))}
            </nav>
        </div>
    );
}
