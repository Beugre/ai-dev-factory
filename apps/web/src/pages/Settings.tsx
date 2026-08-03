import { BASE_URL } from '@/lib/api';
import { ErrorCard, Loading, Section } from '@/components/ui';
import { useProjects } from '@/lib/queries';

export function Settings() {
    const projects = useProjects();
    return (
        <div className="space-y-5">
            <h2 className="title-xl">Réglages</h2>

            <Section title="API">
                <div className="card text-sm">
                    <p className="text-white/50">Backend</p>
                    <p className="font-mono text-accent">{BASE_URL}</p>
                </div>
            </Section>

            <Section title="Projets">
                {projects.isLoading && <Loading />}
                {projects.isError && <ErrorCard message="Chargement impossible." />}
                {(projects.data?.items ?? []).map((p) => (
                    <div key={p.id} className="card space-y-1">
                        <p className="font-medium">{p.name}</p>
                        <p className="text-xs text-white/50">
                            {p.github_owner}/{p.github_repo} · {p.default_branch}
                        </p>
                    </div>
                ))}
            </Section>

            <p className="px-1 text-xs text-white/40">
                Les secrets ne sont jamais gérés ici : ils restent dans les variables
                d'environnement du serveur.
            </p>
        </div>
    );
}
