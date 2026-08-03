import { ciTone } from '@/lib/status';
import { EmptyState, ErrorCard, Loading, Section } from '@/components/ui';
import { useDeployments, usePullRequests } from '@/lib/queries';

export function PullRequests() {
    const prs = usePullRequests();
    const deployments = useDeployments();
    if (prs.isLoading) return <Loading />;
    if (prs.isError) return <ErrorCard message="Chargement impossible." />;

    return (
        <div className="space-y-5">
            <h2 className="title-xl">Livraison</h2>
            <Section title="Pull requests">
                {(prs.data?.items ?? []).length === 0 ? (
                    <EmptyState message="Aucune pull request." />
                ) : (
                    (prs.data?.items ?? []).map((p) => (
                        <div key={p.id} className="card space-y-1">
                            <div className="flex items-center justify-between">
                                <span className="font-medium">#{p.number} {p.title}</span>
                                <span className={`badge ${ciTone(p.ci_state)}`}>CI {p.ci_state}</span>
                            </div>
                            <p className="text-xs text-white/50">Revue: {p.review_state}</p>
                            {p.preview_url && (
                                <a className="text-xs text-accent" href={p.preview_url} target="_blank" rel="noreferrer">
                                    Preview
                                </a>
                            )}
                        </div>
                    ))
                )}
            </Section>

            <Section title="Déploiements">
                {(deployments.data?.items ?? []).length === 0 ? (
                    <EmptyState message="Aucun déploiement." />
                ) : (
                    (deployments.data?.items ?? []).map((d) => (
                        <div key={d.id} className="card flex items-center justify-between">
                            <span className="font-medium capitalize">{d.environment}</span>
                            <span className="badge bg-ok/20 text-ok">{d.status}</span>
                        </div>
                    ))
                )}
            </Section>
        </div>
    );
}
