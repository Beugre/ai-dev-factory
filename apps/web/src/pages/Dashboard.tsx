import { Link } from 'react-router-dom';
import { StatusBadge } from '@/components/StatusBadge';
import { EmptyState, ErrorCard, Loading, Section } from '@/components/ui';
import {
    useAgentRuns,
    useApprovals,
    useFeatures,
    usePullRequests,
} from '@/lib/queries';

function Stat({ label, value }: { label: string; value: number | string }) {
    return (
        <div className="card flex-1">
            <p className="text-3xl font-bold">{value}</p>
            <p className="text-xs text-white/50">{label}</p>
        </div>
    );
}

export function Dashboard() {
    const features = useFeatures();
    const approvals = useApprovals();
    const prs = usePullRequests();
    const runs = useAgentRuns();

    if (features.isLoading) return <Loading />;
    if (features.isError) return <ErrorCard message="Impossible de charger les demandes." />;

    const items = features.data?.items ?? [];
    const pending = items.filter((f) =>
        ['NEEDS_CLARIFICATION', 'READY_FOR_SCOPE_APPROVAL'].includes(f.state),
    );
    const inDev = items.filter((f) => f.state === 'IN_DEVELOPMENT');
    const pendingApprovals = (approvals.data?.items ?? []).filter(
        (a) => a.decision === 'pending',
    );
    const prsInReview = (prs.data?.items ?? []).filter((p) => p.review_state === 'pending');
    const errors = (runs.data?.items ?? []).filter((r) => r.state === 'failed');

    return (
        <div className="space-y-5">
            <div className="flex gap-3">
                <Stat label="En attente" value={pending.length} />
                <Stat label="À valider" value={pendingApprovals.length} />
                <Stat label="En dev" value={inDev.length} />
            </div>

            <Section title="Actions requises">
                {pendingApprovals.length === 0 && pending.length === 0 ? (
                    <EmptyState message="Rien à valider pour le moment." />
                ) : (
                    <div className="space-y-2">
                        {pending.map((f) => (
                            <Link key={f.id} to={`/features/${f.id}`} className="card flex items-center justify-between">
                                <span className="font-medium">{f.title}</span>
                                <StatusBadge state={f.state} />
                            </Link>
                        ))}
                    </div>
                )}
            </Section>

            <Section title="Pull requests en revue">
                {prsInReview.length === 0 ? (
                    <EmptyState message="Aucune PR en attente de revue." />
                ) : (
                    <div className="space-y-2">
                        {prsInReview.map((p) => (
                            <div key={p.id} className="card flex items-center justify-between">
                                <span className="font-medium">#{p.number} {p.title}</span>
                                <span className="badge bg-accent-soft text-accent">{p.ci_state}</span>
                            </div>
                        ))}
                    </div>
                )}
            </Section>

            <Section title="Erreurs récentes">
                {errors.length === 0 ? (
                    <EmptyState message="Aucune erreur récente." />
                ) : (
                    <div className="space-y-2">
                        {errors.map((r) => (
                            <div key={r.id} className="card border-danger/30">
                                <p className="font-medium">{r.agent_type}</p>
                                <p className="text-xs text-danger">{r.error}</p>
                            </div>
                        ))}
                    </div>
                )}
            </Section>
        </div>
    );
}
