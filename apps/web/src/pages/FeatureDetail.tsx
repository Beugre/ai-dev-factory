import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { StatusBadge } from '@/components/StatusBadge';
import { EmptyState, ErrorCard, Loading, Section } from '@/components/ui';
import {
    useAnswerQuestion,
    useFeature,
    useFeatureAction,
    useQuestions,
    useStories,
} from '@/lib/queries';
import type { ClarificationQuestion } from '@/lib/types';

function QuestionCard({ question, featureId }: { question: ClarificationQuestion; featureId: string }) {
    const answer = useAnswerQuestion(featureId);
    const [free, setFree] = useState('');
    if (question.state === 'answered') {
        return (
            <div className="card">
                <p className="text-sm text-white/70">{question.question}</p>
                <p className="mt-1 font-medium text-ok">→ {question.answer}</p>
            </div>
        );
    }
    return (
        <div className="card space-y-2">
            <p className="font-medium">{question.question}</p>
            <div className="flex flex-wrap gap-2">
                {question.options.map((opt) => (
                    <button
                        key={opt}
                        className="btn-ghost !py-2 !px-4"
                        onClick={() => answer.mutate({ questionId: question.id, answer: opt })}
                    >
                        {opt}
                    </button>
                ))}
            </div>
            <div className="flex gap-2">
                <input
                    className="input"
                    placeholder="Réponse libre…"
                    value={free}
                    onChange={(e) => setFree(e.target.value)}
                />
                <button
                    className="btn-primary"
                    disabled={!free}
                    onClick={() => answer.mutate({ questionId: question.id, answer: free })}
                >
                    OK
                </button>
            </div>
        </div>
    );
}

export function FeatureDetail() {
    const { id = '' } = useParams();
    const feature = useFeature(id);
    const questions = useQuestions(id);
    const stories = useStories();
    const actions = useFeatureAction(id);
    const [comment, setComment] = useState('');

    if (feature.isLoading) return <Loading />;
    if (feature.isError || !feature.data) return <ErrorCard message="Demande introuvable." />;

    const f = feature.data;
    const relatedStories = (stories.data?.items ?? []).filter(() => true);
    const canApprove = f.state === 'READY_FOR_SCOPE_APPROVAL';

    return (
        <div className="space-y-5">
            <div className="card">
                <div className="flex items-start justify-between gap-2">
                    <h2 className="text-xl font-bold">{f.title}</h2>
                    <StatusBadge state={f.state} />
                </div>
                <p className="mt-2 text-sm text-white/60">{f.normalized_request ?? f.raw_request}</p>
            </div>

            <Section title="Questions de clarification">
                {(questions.data ?? []).length === 0 ? (
                    <EmptyState message="Aucune question." />
                ) : (
                    <div className="space-y-2">
                        {(questions.data ?? []).map((q) => (
                            <QuestionCard key={q.id} question={q} featureId={id} />
                        ))}
                    </div>
                )}
            </Section>

            <Section title="Stories">
                {relatedStories.length === 0 ? (
                    <EmptyState message="Pas encore de stories." />
                ) : (
                    <div className="space-y-2">
                        {relatedStories.map((s) => (
                            <div key={s.id} className="card">
                                <div className="flex items-center justify-between">
                                    <span className="font-medium">{s.title}</span>
                                    <span className="badge bg-accent-soft text-accent">{s.status}</span>
                                </div>
                                {s.github_issue_url && (
                                    <a
                                        className="mt-1 block text-xs text-accent"
                                        href={s.github_issue_url}
                                        target="_blank"
                                        rel="noreferrer"
                                    >
                                        Issue #{s.github_issue_number}
                                    </a>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </Section>

            {canApprove && (
                <Section title="Décision">
                    <div className="card space-y-3">
                        <button
                            className="btn-primary w-full"
                            onClick={() => actions.approveScope.mutate()}
                            disabled={actions.approveScope.isPending}
                        >
                            Approuver le périmètre
                        </button>
                        <textarea
                            className="input"
                            placeholder="Demander une modification…"
                            value={comment}
                            onChange={(e) => setComment(e.target.value)}
                        />
                        <div className="flex gap-2">
                            <button
                                className="btn-ghost flex-1"
                                disabled={!comment}
                                onClick={() => actions.requestChanges.mutate(comment)}
                            >
                                Demander une modif
                            </button>
                            <button className="btn-danger flex-1" onClick={() => actions.cancel.mutate()}>
                                Annuler
                            </button>
                        </div>
                    </div>
                </Section>
            )}
        </div>
    );
}
