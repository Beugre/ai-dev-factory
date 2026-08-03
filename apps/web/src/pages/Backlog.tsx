import { Link } from 'react-router-dom';
import { StatusBadge } from '@/components/StatusBadge';
import { EmptyState, ErrorCard, Loading, Section } from '@/components/ui';
import { useFeatures, useStories } from '@/lib/queries';

export function Backlog() {
    const features = useFeatures();
    const stories = useStories();

    if (features.isLoading) return <Loading />;
    if (features.isError) return <ErrorCard message="Chargement impossible." />;

    const items = features.data?.items ?? [];
    const grouped = items.reduce<Record<string, typeof items>>((acc, f) => {
        (acc[f.state] ??= []).push(f);
        return acc;
    }, {});

    return (
        <div className="space-y-5">
            <h2 className="title-xl">Backlog</h2>
            {Object.keys(grouped).length === 0 && <EmptyState message="Backlog vide." />}
            {Object.entries(grouped).map(([state, list]) => (
                <Section key={state} title={state}>
                    <div className="space-y-2">
                        {list.map((f) => (
                            <Link key={f.id} to={`/features/${f.id}`} className="card flex items-center justify-between">
                                <span className="font-medium">{f.title}</span>
                                <StatusBadge state={f.state} />
                            </Link>
                        ))}
                    </div>
                </Section>
            ))}

            <Section title="Stories">
                <div className="space-y-2">
                    {(stories.data?.items ?? []).map((s) => (
                        <div key={s.id} className="card flex items-center justify-between">
                            <span className="font-medium">{s.title}</span>
                            <span className="badge bg-accent-soft text-accent">{s.status}</span>
                        </div>
                    ))}
                </div>
            </Section>
        </div>
    );
}
