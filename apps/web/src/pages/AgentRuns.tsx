import { EmptyState, ErrorCard, Loading } from '@/components/ui';
import { useAgentRuns } from '@/lib/queries';

const TONE: Record<string, string> = {
    succeeded: 'bg-ok/20 text-ok',
    failed: 'bg-danger/20 text-danger',
    running: 'bg-accent-soft text-accent',
    pending: 'bg-white/10 text-white/60',
};

export function AgentRuns() {
    const runs = useAgentRuns();
    if (runs.isLoading) return <Loading />;
    if (runs.isError) return <ErrorCard message="Chargement impossible." />;

    const items = runs.data?.items ?? [];
    return (
        <div className="space-y-4">
            <h2 className="title-xl">Agents</h2>
            {items.length === 0 ? (
                <EmptyState message="Aucune exécution d'agent." />
            ) : (
                items.map((r) => (
                    <div key={r.id} className="card space-y-1">
                        <div className="flex items-center justify-between">
                            <span className="font-medium">{r.agent_type}</span>
                            <span className={`badge ${TONE[r.state] ?? 'bg-white/10 text-white/60'}`}>
                                {r.state}
                            </span>
                        </div>
                        <p className="text-xs text-white/50">{r.provider}{r.model ? ` · ${r.model}` : ''}</p>
                        {/* Only summaries are shown — never a private reasoning chain. */}
                        <p className="text-sm text-white/70">{r.output_summary || r.input_summary}</p>
                        {r.error && <p className="text-xs text-danger">{r.error}</p>}
                    </div>
                ))
            )}
        </div>
    );
}
