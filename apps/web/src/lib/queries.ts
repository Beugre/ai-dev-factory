import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from './api';
import type {
    AgentRun,
    Approval,
    AuditLog,
    ClarificationQuestion,
    Deployment,
    FeatureRequest,
    Page,
    Project,
    PullRequest,
    Story,
} from './types';

export function useProjects() {
    return useQuery({
        queryKey: ['projects'],
        queryFn: () => api.get<Page<Project>>('/projects'),
    });
}

export function useFeatures() {
    return useQuery({
        queryKey: ['features'],
        queryFn: () => api.get<Page<FeatureRequest>>('/feature-requests'),
    });
}

export function useFeature(id: string) {
    return useQuery({
        queryKey: ['feature', id],
        queryFn: () => api.get<FeatureRequest>(`/feature-requests/${id}`),
        enabled: Boolean(id),
    });
}

export function useQuestions(featureId: string) {
    return useQuery({
        queryKey: ['questions', featureId],
        queryFn: () =>
            api.get<ClarificationQuestion[]>(`/feature-requests/${featureId}/questions`),
        enabled: Boolean(featureId),
    });
}

export function useStories() {
    return useQuery({
        queryKey: ['stories'],
        queryFn: () => api.get<Page<Story>>('/stories'),
    });
}

export function useApprovals() {
    return useQuery({
        queryKey: ['approvals'],
        queryFn: () => api.get<Page<Approval>>('/approvals'),
    });
}

export function usePullRequests() {
    return useQuery({
        queryKey: ['pull-requests'],
        queryFn: () => api.get<Page<PullRequest>>('/pull-requests'),
    });
}

export function useDeployments() {
    return useQuery({
        queryKey: ['deployments'],
        queryFn: () => api.get<Page<Deployment>>('/deployments'),
    });
}

export function useAgentRuns() {
    return useQuery({
        queryKey: ['agent-runs'],
        queryFn: () => api.get<Page<AgentRun>>('/agent-runs'),
    });
}

export function useAuditLogs() {
    return useQuery({
        queryKey: ['audit-logs'],
        queryFn: () => api.get<Page<AuditLog>>('/audit-logs'),
    });
}

export function useCreateFeature() {
    const qc = useQueryClient();
    return useMutation({
        mutationFn: (payload: {
            project_id: string;
            title: string;
            raw_request: string;
            priority: string;
        }) => api.post<FeatureRequest>('/feature-requests', { ...payload, source: 'web' }),
        onSuccess: (feature) => {
            void qc.invalidateQueries({ queryKey: ['features'] });
            void api.post(`/feature-requests/${feature.id}/analyze`).then(() => {
                void qc.invalidateQueries({ queryKey: ['feature', feature.id] });
            });
        },
    });
}

export function useCreateProject() {
    const qc = useQueryClient();
    return useMutation({
        mutationFn: (payload: {
            name: string;
            slug: string;
            github_owner: string;
            github_repo: string;
            staging_url?: string;
        }) => api.post<Project>('/projects', payload),
        onSuccess: () => {
            void qc.invalidateQueries({ queryKey: ['projects'] });
        },
    });
}

export function useAnswerQuestion(featureId: string) {
    const qc = useQueryClient();
    return useMutation({
        mutationFn: (vars: { questionId: string; answer: string }) =>
            api.post(`/questions/${vars.questionId}/answer`, { answer: vars.answer }),
        onSuccess: () => {
            void qc.invalidateQueries({ queryKey: ['questions', featureId] });
            void qc.invalidateQueries({ queryKey: ['feature', featureId] });
        },
    });
}

export function useFeatureAction(featureId: string) {
    const qc = useQueryClient();
    const invalidate = () => {
        void qc.invalidateQueries({ queryKey: ['feature', featureId] });
        void qc.invalidateQueries({ queryKey: ['features'] });
        void qc.invalidateQueries({ queryKey: ['stories'] });
    };
    return {
        approveScope: useMutation({
            mutationFn: () => api.post(`/feature-requests/${featureId}/approve-scope`, {}),
            onSuccess: invalidate,
        }),
        requestChanges: useMutation({
            mutationFn: (comment: string) =>
                api.post(`/feature-requests/${featureId}/request-changes`, { comment }),
            onSuccess: invalidate,
        }),
        cancel: useMutation({
            mutationFn: () => api.post(`/feature-requests/${featureId}/cancel`, {}),
            onSuccess: invalidate,
        }),
    };
}
