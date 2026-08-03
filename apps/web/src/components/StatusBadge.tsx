import { stateLabel, stateTone } from '@/lib/status';

export function StatusBadge({ state }: { state: string }) {
    return <span className={`badge ${stateTone(state)}`}>{stateLabel(state)}</span>;
}

export function Badge({ tone, children }: { tone: string; children: React.ReactNode }) {
    return <span className={`badge ${tone}`}>{children}</span>;
}
