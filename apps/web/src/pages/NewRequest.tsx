import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import { z } from 'zod';
import { ErrorCard, Loading } from '@/components/ui';
import { useCreateFeature, useProjects } from '@/lib/queries';

const schema = z.object({
    project_id: z.string().min(1, 'Projet requis'),
    title: z.string().min(3, 'Titre trop court'),
    raw_request: z.string().min(10, 'Décrivez le besoin (10 caractères min.)'),
    priority: z.enum(['critical', 'high', 'medium', 'low']),
});

type FormValues = z.infer<typeof schema>;

export function NewRequest() {
    const navigate = useNavigate();
    const projects = useProjects();
    const create = useCreateFeature();
    const {
        register,
        handleSubmit,
        formState: { errors },
    } = useForm<FormValues>({ defaultValues: { priority: 'medium' } });

    if (projects.isLoading) return <Loading />;
    if (projects.isError) return <ErrorCard message="Impossible de charger les projets." />;

    const onSubmit = handleSubmit(async (values) => {
        const parsed = schema.safeParse(values);
        if (!parsed.success) return;
        const feature = await create.mutateAsync(parsed.data);
        navigate(`/features/${feature.id}`);
    });

    return (
        <form onSubmit={onSubmit} className="space-y-4">
            <h2 className="title-xl">Nouvelle demande</h2>

            <div>
                <label className="label">Projet</label>
                <select className="input" {...register('project_id')}>
                    {(projects.data?.items ?? []).map((p) => (
                        <option key={p.id} value={p.id}>
                            {p.name}
                        </option>
                    ))}
                </select>
                {errors.project_id && <p className="mt-1 text-xs text-danger">{errors.project_id.message}</p>}
            </div>

            <div>
                <label className="label">Titre</label>
                <input className="input" placeholder="Réinitialisation du mot de passe" {...register('title')} />
                {errors.title && <p className="mt-1 text-xs text-danger">{errors.title.message}</p>}
            </div>

            <div>
                <label className="label">Besoin</label>
                <textarea
                    className="input min-h-[140px]"
                    placeholder="En tant qu'utilisateur, je veux…"
                    {...register('raw_request')}
                />
                {errors.raw_request && (
                    <p className="mt-1 text-xs text-danger">{errors.raw_request.message}</p>
                )}
            </div>

            <div>
                <label className="label">Priorité</label>
                <select className="input" {...register('priority')}>
                    <option value="critical">Critique</option>
                    <option value="high">Haute</option>
                    <option value="medium">Moyenne</option>
                    <option value="low">Basse</option>
                </select>
            </div>

            {create.isError && <ErrorCard message="La création a échoué." />}

            <button className="btn-primary w-full" type="submit" disabled={create.isPending}>
                {create.isPending ? 'Envoi…' : 'Envoyer la demande'}
            </button>
        </form>
    );
}
