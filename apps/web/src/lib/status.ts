const FEATURE_LABELS: Record<string, string> = {
    DRAFT: 'Brouillon',
    ANALYZING: 'Analyse',
    NEEDS_CLARIFICATION: 'Clarification',
    READY_FOR_SCOPE_APPROVAL: 'À valider',
    SCOPE_APPROVED: 'Périmètre validé',
    CREATING_ISSUES: 'Création issues',
    READY_FOR_DEVELOPMENT: 'Prêt à développer',
    IN_DEVELOPMENT: 'En développement',
    IN_REVIEW: 'En revue',
    READY_FOR_STAGING: 'Prêt staging',
    STAGING_DEPLOYED: 'Staging déployé',
    READY_FOR_ACCEPTANCE: 'À accepter',
    CHANGES_REQUESTED: 'Modifs demandées',
    ACCEPTED: 'Accepté',
    READY_FOR_PRODUCTION: 'Prêt production',
    DONE: 'Terminé',
    BLOCKED: 'Bloqué',
    CANCELLED: 'Annulé',
};

const TONE: Record<string, string> = {
    DRAFT: 'bg-white/10 text-white/70',
    ANALYZING: 'bg-accent-soft text-accent',
    NEEDS_CLARIFICATION: 'bg-warn/20 text-warn',
    READY_FOR_SCOPE_APPROVAL: 'bg-warn/20 text-warn',
    CHANGES_REQUESTED: 'bg-warn/20 text-warn',
    BLOCKED: 'bg-danger/20 text-danger',
    CANCELLED: 'bg-danger/10 text-danger',
    DONE: 'bg-ok/20 text-ok',
    ACCEPTED: 'bg-ok/20 text-ok',
    STAGING_DEPLOYED: 'bg-ok/20 text-ok',
};

export function stateLabel(state: string): string {
    return FEATURE_LABELS[state] ?? state;
}

export function stateTone(state: string): string {
    return TONE[state] ?? 'bg-accent-soft text-accent';
}

export function ciTone(ci: string): string {
    if (ci === 'success') return 'bg-ok/20 text-ok';
    if (ci === 'failure') return 'bg-danger/20 text-danger';
    return 'bg-white/10 text-white/70';
}
