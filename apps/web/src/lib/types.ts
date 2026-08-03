export interface Page<T> {
    items: T[];
    total: number;
    limit: number;
    offset: number;
}

export type FeatureState =
    | 'DRAFT'
    | 'ANALYZING'
    | 'NEEDS_CLARIFICATION'
    | 'READY_FOR_SCOPE_APPROVAL'
    | 'SCOPE_APPROVED'
    | 'CREATING_ISSUES'
    | 'READY_FOR_DEVELOPMENT'
    | 'IN_DEVELOPMENT'
    | 'IN_REVIEW'
    | 'READY_FOR_STAGING'
    | 'STAGING_DEPLOYED'
    | 'READY_FOR_ACCEPTANCE'
    | 'CHANGES_REQUESTED'
    | 'ACCEPTED'
    | 'READY_FOR_PRODUCTION'
    | 'DONE'
    | 'BLOCKED'
    | 'CANCELLED';

export interface Project {
    id: string;
    name: string;
    slug: string;
    github_owner: string;
    github_repo: string;
    default_branch: string;
    staging_url: string | null;
    status: string;
}

export interface FeatureRequest {
    id: string;
    project_id: string;
    title: string;
    raw_request: string;
    normalized_request: string | null;
    source: string;
    requester_id: string | null;
    state: FeatureState;
    priority: string;
    created_at: string;
    updated_at: string;
}

export interface ClarificationQuestion {
    id: string;
    feature_request_id: string;
    question: string;
    answer_type: string;
    options: string[];
    answer: string | null;
    blocking: boolean;
    state: string;
}

export interface Story {
    id: string;
    epic_id: string;
    title: string;
    description: string;
    acceptance_criteria: string[];
    gherkin: string;
    priority: string;
    estimated_complexity: number;
    dependencies: string[];
    status: string;
    assigned_agent: string | null;
    github_issue_number: number | null;
    github_issue_url: string | null;
    pull_request_number: number | null;
    pull_request_url: string | null;
}

export interface Approval {
    id: string;
    project_id: string;
    entity_type: string;
    entity_id: string;
    approval_type: string;
    decision: string;
    comment: string | null;
}

export interface PullRequest {
    id: string;
    story_id: string | null;
    repository: string;
    number: number;
    title: string;
    branch: string;
    state: string;
    ci_state: string;
    review_state: string;
    preview_url: string | null;
    mergeable: boolean | null;
}

export interface Deployment {
    id: string;
    project_id: string;
    pull_request_id: string | null;
    environment: string;
    version: string;
    status: string;
    url: string | null;
}

export interface AgentRun {
    id: string;
    project_id: string;
    feature_request_id: string | null;
    story_id: string | null;
    agent_type: string;
    provider: string;
    model: string | null;
    input_summary: string;
    output_summary: string;
    state: string;
    error: string | null;
}

export interface AuditLog {
    id: string;
    actor_type: string;
    actor_id: string;
    action: string;
    entity_type: string;
    entity_id: string;
    created_at: string;
}
