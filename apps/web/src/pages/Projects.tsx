import { useState } from 'react';
import { useProjects, useCreateProject } from '../lib/queries';

export function Projects() {
    const { data: projectsData, isLoading, error } = useProjects();
    const createProject = useCreateProject();
    const [showForm, setShowForm] = useState(false);
    const [formData, setFormData] = useState({
        name: '',
        slug: '',
        github_owner: '',
        github_repo: '',
        staging_url: '',
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        createProject.mutate(
            {
                name: formData.name,
                slug: formData.slug,
                github_owner: formData.github_owner,
                github_repo: formData.github_repo,
                staging_url: formData.staging_url || undefined,
            },
            {
                onSuccess: () => {
                    setFormData({ name: '', slug: '', github_owner: '', github_repo: '', staging_url: '' });
                    setShowForm(false);
                },
            }
        );
    };

    const projects = projectsData?.items || [];

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800">
            <div className="max-w-6xl mx-auto px-4 py-8">
                <div className="flex justify-between items-center mb-8">
                    <h1 className="text-4xl font-bold text-white">Projets</h1>
                    <button
                        onClick={() => setShowForm(!showForm)}
                        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
                    >
                        {showForm ? 'Annuler' : 'Créer un projet'}
                    </button>
                </div>

                {showForm && (
                    <div className="mb-8 bg-slate-800 rounded-lg p-6 border border-slate-700">
                        <h2 className="text-2xl font-semibold text-white mb-4">Nouveau projet</h2>
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-1">
                                    Nom
                                </label>
                                <input
                                    type="text"
                                    value={formData.name}
                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
                                    placeholder="Mon Projet"
                                    required
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-1">
                                    Slug
                                </label>
                                <input
                                    type="text"
                                    value={formData.slug}
                                    onChange={(e) => setFormData({ ...formData, slug: e.target.value })}
                                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
                                    placeholder="mon-projet"
                                    pattern="^[a-z0-9-]+$"
                                    required
                                />
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-1">
                                        GitHub Owner
                                    </label>
                                    <input
                                        type="text"
                                        value={formData.github_owner}
                                        onChange={(e) => setFormData({ ...formData, github_owner: e.target.value })}
                                        className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
                                        placeholder="Beugre"
                                        required
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-1">
                                        GitHub Repo
                                    </label>
                                    <input
                                        type="text"
                                        value={formData.github_repo}
                                        onChange={(e) => setFormData({ ...formData, github_repo: e.target.value })}
                                        className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
                                        placeholder="mon-app"
                                        required
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-1">
                                    URL Staging (optionnel)
                                </label>
                                <input
                                    type="url"
                                    value={formData.staging_url}
                                    onChange={(e) => setFormData({ ...formData, staging_url: e.target.value })}
                                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
                                    placeholder="https://staging.example.com"
                                />
                            </div>

                            <button
                                type="submit"
                                disabled={createProject.isPending}
                                className="w-full px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg disabled:opacity-50 transition"
                            >
                                {createProject.isPending ? 'Création...' : 'Créer'}
                            </button>

                            {createProject.isError && (
                                <div className="p-3 bg-red-900 text-red-200 rounded">
                                    Erreur : {(createProject.error as any)?.message || 'Une erreur est survenue'}
                                </div>
                            )}
                        </form>
                    </div>
                )}

                {isLoading && <p className="text-gray-300">Chargement des projets...</p>}
                {error && <p className="text-red-400">Erreur : {(error as any)?.message}</p>}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {projects.map((project) => (
                        <div
                            key={project.id}
                            className="bg-slate-800 rounded-lg p-6 border border-slate-700 hover:border-slate-500 transition"
                        >
                            <h3 className="text-xl font-semibold text-white mb-2">{project.name}</h3>
                            <dl className="space-y-2 text-sm">
                                <div>
                                    <dt className="text-gray-400">Slug</dt>
                                    <dd className="text-gray-200 font-mono">{project.slug}</dd>
                                </div>
                                <div>
                                    <dt className="text-gray-400">Repository</dt>
                                    <dd className="text-gray-200 font-mono">
                                        {project.github_owner}/{project.github_repo}
                                    </dd>
                                </div>
                                <div>
                                    <dt className="text-gray-400">Branche par défaut</dt>
                                    <dd className="text-gray-200">{project.default_branch}</dd>
                                </div>
                                {project.staging_url && (
                                    <div>
                                        <dt className="text-gray-400">URL Staging</dt>
                                        <dd>
                                            <a
                                                href={project.staging_url}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="text-blue-400 hover:text-blue-300"
                                            >
                                                {project.staging_url}
                                            </a>
                                        </dd>
                                    </div>
                                )}
                                <div>
                                    <dt className="text-gray-400">Statut</dt>
                                    <dd>
                                        <span
                                            className={
                                                project.status === 'active'
                                                    ? 'px-2 py-1 bg-green-900 text-green-200 rounded text-xs'
                                                    : 'px-2 py-1 bg-gray-900 text-gray-200 rounded text-xs'
                                            }
                                        >
                                            {project.status}
                                        </span>
                                    </dd>
                                </div>
                            </dl>
                        </div>
                    ))}
                </div>

                {projects.length === 0 && !isLoading && (
                    <div className="text-center py-12">
                        <p className="text-gray-400 mb-4">Aucun projet créé</p>
                        <button
                            onClick={() => setShowForm(true)}
                            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
                        >
                            Créer le premier projet
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}
