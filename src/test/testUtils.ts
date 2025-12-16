import { GovernmentAction, SourceSystem, ActionMetadata } from '@/data/actions';

/**
 * Create a mock government action for testing
 */
export function createMockAction(overrides: Partial<GovernmentAction> = {}): GovernmentAction {
  const defaultAction: GovernmentAction = {
    id: 'test-action-1',
    title: 'Test Bill 2024',
    date: '2024-12-01',
    source_system: 'PARLIAMENT' as SourceSystem,
    url: 'https://example.com/test-bill',
    primary_entity: 'Test Ministry',
    summary: 'A test bill for unit testing purposes',
    labels: ['Health', 'Education'],
    metadata: {
      bill_number: 'TB-2024-001',
      parliament_number: 54,
      stage_history: [
        { stage: 'First Reading', date: '2024-11-01' },
        { stage: 'Select Committee', date: '2024-11-15' }
      ],
      act_number: null,
      commencement_date: null,
      notice_number: null,
      notice_type: null,
      document_type: 'Bill',
      portfolio: 'Health'
    }
  };

  return { ...defaultAction, ...overrides };
}

/**
 * Create multiple mock actions for testing
 */
export function createMockActions(count: number): GovernmentAction[] {
  return Array.from({ length: count }, (_, index) => createMockAction({
    id: `test-action-${index + 1}`,
    title: `Test Bill ${index + 1}`,
    date: `2024-${String(index % 12 + 1).padStart(2, '0')}-01`,
    source_system: ['PARLIAMENT', 'LEGISLATION', 'GAZETTE', 'BEEHIVE'][index % 4] as SourceSystem,
    labels: [['Health'], ['Education'], ['Environment'], ['Economy']][index % 4]
  }));
}

/**
 * Create mock action with specific metadata for testing search
 */
export function createActionWithMetadata(metadata: Partial<ActionMetadata>): GovernmentAction {
  return createMockAction({
    metadata: {
      bill_number: null,
      parliament_number: null,
      stage_history: null,
      act_number: null,
      commencement_date: null,
      notice_number: null,
      notice_type: null,
      document_type: null,
      portfolio: null,
      ...metadata
    }
  });
}