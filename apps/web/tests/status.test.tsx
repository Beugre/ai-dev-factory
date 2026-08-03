import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { StatusBadge } from '@/components/StatusBadge';
import { stateLabel } from '@/lib/status';

describe('status helpers', () => {
    it('maps known feature states to French labels', () => {
        expect(stateLabel('NEEDS_CLARIFICATION')).toBe('Clarification');
        expect(stateLabel('DONE')).toBe('Terminé');
    });

    it('falls back to the raw state when unknown', () => {
        expect(stateLabel('WEIRD')).toBe('WEIRD');
    });

    it('renders a badge with the localized label', () => {
        render(<StatusBadge state="IN_DEVELOPMENT" />);
        expect(screen.getByText('En développement')).toBeInTheDocument();
    });
});
