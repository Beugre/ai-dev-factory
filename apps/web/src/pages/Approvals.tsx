import { EmptyState, ErrorCard, Loading } from '@/components/ui';
import { useApprovals } from '@/lib/queries';

export function Approvals() {
    const approvals = useApprovals();
    if (approvals.isLoading) return <Loading />;
    if (approvals.isError) return <ErrorCard message="Chargement impossible." />;

    const pending = (approvals.data?.items ?? []).filter((a) => a.decision === 'pending');

    return (
        <div className="space-y-4">
            <h2 className="title-xl">Validations</h2>
            {pending.length === 0 ? (
                <EmptyState message="Aucune validation en attente." />
            ) : (
                pending.map((a) => (
                    <div key={a.id} className="card space-y-2">
                        <div className="flex items-center justify-between">
                            <span className="font-medium capitalize">{a.approval_type}</span>
                            <span className="badge bg-warn/20 text-warn">En attente</span>
                        </div>
                        <p className="text-xs text-white/50">
                            {a.entity_type} · {a.entity_id.slice(0, 8)}
                        </p>
                    </div>
                ))
            )}
        </div>
    );
}
