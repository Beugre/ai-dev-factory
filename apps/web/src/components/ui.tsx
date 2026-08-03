export function Section({ title, children }: { title: string; children: React.ReactNode }) {
    return (
        <section className="space-y-2">
            <h2 className="px-1 text-sm font-semibold uppercase tracking-wide text-white/50">
                {title}
            </h2>
            {children}
        </section>
    );
}

export function EmptyState({ message }: { message: string }) {
    return <div className="card text-center text-sm text-white/50">{message}</div>;
}

export function Loading() {
    return <div className="card animate-pulse text-sm text-white/40">Chargement…</div>;
}

export function ErrorCard({ message }: { message: string }) {
    return <div className="card border-danger/30 text-sm text-danger">{message}</div>;
}
