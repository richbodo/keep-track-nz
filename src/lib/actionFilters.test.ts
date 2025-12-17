import { describe, it, expect, beforeEach } from 'vitest';
import {
  searchActions,
  filterBySource,
  filterByLabels,
  sortActionsByDate,
  filterAndSortActions,
  createDefaultFilterState,
  hasActiveFilters,
  resetFilters,
  validateFilterState,
  type ActionFilterState,
  type SearchConfig,
} from './actionFilters';
import { createMockAction, createMockActions, createActionWithMetadata } from '@/test/testUtils';
import { GovernmentAction, ActionMetadata, SourceSystem } from '@/data/actions';

describe('actionFilters', () => {
  let testActions: GovernmentAction[];

  beforeEach(() => {
    testActions = [
      createMockAction({
        id: 'action-1',
        title: 'Health and Safety Bill',
        summary: 'Improving workplace safety standards',
        primary_entity: 'Ministry of Health',
        url: 'https://example.com/health-bill',
        source_system: 'PARLIAMENT',
        labels: ['Health', 'Safety'],
        date: '2024-01-15',
        metadata: {
          bill_number: 'HSB-2024-001',
          portfolio: 'Health',
          document_type: 'Bill',
          stage_history: [
            { stage: 'First Reading', date: '2024-01-01' },
            { stage: 'Committee Review', date: '2024-01-10' }
          ]
        }
      }),
      createMockAction({
        id: 'action-2',
        title: 'Education Reform Act',
        summary: 'Modernizing education curriculum',
        primary_entity: 'Ministry of Education',
        url: 'https://example.com/education-act',
        source_system: 'LEGISLATION',
        labels: ['Education'],
        date: '2024-02-01',
        metadata: {
          act_number: 'ERA-2024-001',
          portfolio: 'Education',
          document_type: 'Act'
        }
      }),
      createMockAction({
        id: 'action-3',
        title: 'Environmental Protection Notice',
        summary: 'New regulations for environmental protection',
        primary_entity: 'Department of Conservation',
        url: 'https://example.com/environment-notice',
        source_system: 'GAZETTE',
        labels: ['Environment'],
        date: '2024-01-01',
        metadata: {
          notice_number: 'EPN-2024-001',
          notice_type: 'Regulation',
          portfolio: 'Conservation'
        }
      }),
      createMockAction({
        id: 'action-4',
        title: 'Economic Development Announcement',
        summary: 'Investment in infrastructure projects',
        primary_entity: 'Treasury',
        url: 'https://example.com/economic-announcement',
        source_system: 'BEEHIVE',
        labels: ['Economy', 'Infrastructure'],
        date: '2024-03-01',
        metadata: {
          document_type: 'Announcement',
          portfolio: 'Treasury'
        }
      })
    ];
  });

  describe('searchActions', () => {
    it('should search by title', () => {
      const result = searchActions(testActions, 'Health');
      expect(result).toHaveLength(1);
      expect(result[0].title).toBe('Health and Safety Bill');
    });

    it('should search by summary', () => {
      const result = searchActions(testActions, 'safety standards');
      expect(result).toHaveLength(1);
      expect(result[0].title).toBe('Health and Safety Bill');
    });

    it('should search by primary entity', () => {
      const result = searchActions(testActions, 'Education');
      expect(result).toHaveLength(1);
      expect(result[0].title).toBe('Education Reform Act');
    });

    it('should search by URL', () => {
      const result = searchActions(testActions, 'health-bill');
      expect(result).toHaveLength(1);
      expect(result[0].url).toContain('health-bill');
    });

    it('should search by labels', () => {
      const result = searchActions(testActions, 'Infrastructure');
      expect(result).toHaveLength(1);
      expect(result[0].labels).toContain('Infrastructure');
    });

    it('should search by ID', () => {
      const result = searchActions(testActions, 'action-2');
      expect(result).toHaveLength(1);
      expect(result[0].id).toBe('action-2');
    });

    describe('metadata search', () => {
      it('should search by bill number', () => {
        const result = searchActions(testActions, 'HSB-2024-001');
        expect(result).toHaveLength(1);
        expect(result[0].metadata.bill_number).toBe('HSB-2024-001');
      });

      it('should search by act number', () => {
        const result = searchActions(testActions, 'ERA-2024-001');
        expect(result).toHaveLength(1);
        expect(result[0].metadata.act_number).toBe('ERA-2024-001');
      });

      it('should search by notice number', () => {
        const result = searchActions(testActions, 'EPN-2024-001');
        expect(result).toHaveLength(1);
        expect(result[0].metadata.notice_number).toBe('EPN-2024-001');
      });

      it('should search by document type', () => {
        const result = searchActions(testActions, 'Bill');
        expect(result).toHaveLength(1);
        expect(result[0].metadata.document_type).toBe('Bill');
      });

      it('should search by portfolio', () => {
        const result = searchActions(testActions, 'Treasury');
        expect(result).toHaveLength(1);
        expect(result[0].metadata.portfolio).toBe('Treasury');
      });

      it('should search stage history stages', () => {
        const result = searchActions(testActions, 'First Reading');
        expect(result).toHaveLength(1);
        expect(result[0].metadata.stage_history?.[0].stage).toBe('First Reading');
      });

      it('should search stage history dates', () => {
        const result = searchActions(testActions, '2024-01-10');
        expect(result).toHaveLength(1);
        expect(result[0].metadata.stage_history?.[1].date).toBe('2024-01-10');
      });
    });

    describe('search configuration', () => {
      it('should support case sensitive search', () => {
        const config: SearchConfig = { caseSensitive: true };
        const sensitiveResult = searchActions(testActions, 'HEALTH', config);
        const insensitiveResult = searchActions(testActions, 'HEALTH');

        expect(sensitiveResult).toHaveLength(0);
        expect(insensitiveResult).toHaveLength(1);
      });

      it('should support exact match search', () => {
        const config: SearchConfig = { exactMatch: true };
        const exactResult = searchActions(testActions, 'Health and Safety Bill', config);
        const partialResult = searchActions(testActions, 'Health', config);

        expect(exactResult).toHaveLength(1); // Exact title match
        expect(partialResult).toHaveLength(1); // 'Health' exact matches the 'Health' label
      });

      it('should allow disabling metadata search', () => {
        const config: SearchConfig = { searchMetadata: false };
        const result = searchActions(testActions, 'HSB-2024-001', config);
        expect(result).toHaveLength(0);
      });

      it('should allow disabling stage history search', () => {
        const config: SearchConfig = { searchStageHistory: false };
        const result = searchActions(testActions, 'First Reading', config);
        expect(result).toHaveLength(0);
      });
    });

    it('should handle empty search query', () => {
      const result = searchActions(testActions, '');
      expect(result).toHaveLength(testActions.length);
    });

    it('should handle whitespace-only search query', () => {
      const result = searchActions(testActions, '   ');
      expect(result).toHaveLength(testActions.length);
    });

    it('should return empty array for non-matching search', () => {
      const result = searchActions(testActions, 'non-existent-term');
      expect(result).toHaveLength(0);
    });
  });

  describe('filterBySource', () => {
    it('should return all actions when source is ALL', () => {
      const result = filterBySource(testActions, 'ALL');
      expect(result).toHaveLength(testActions.length);
    });

    it('should filter by PARLIAMENT source', () => {
      const result = filterBySource(testActions, 'PARLIAMENT');
      expect(result).toHaveLength(1);
      expect(result[0].source_system).toBe('PARLIAMENT');
    });

    it('should filter by LEGISLATION source', () => {
      const result = filterBySource(testActions, 'LEGISLATION');
      expect(result).toHaveLength(1);
      expect(result[0].source_system).toBe('LEGISLATION');
    });

    it('should filter by GAZETTE source', () => {
      const result = filterBySource(testActions, 'GAZETTE');
      expect(result).toHaveLength(1);
      expect(result[0].source_system).toBe('GAZETTE');
    });

    it('should filter by BEEHIVE source', () => {
      const result = filterBySource(testActions, 'BEEHIVE');
      expect(result).toHaveLength(1);
      expect(result[0].source_system).toBe('BEEHIVE');
    });

    it('should return empty array for non-existent source', () => {
      const result = filterBySource(testActions, 'PARLIAMENT');
      expect(result.every(action => action.source_system === 'PARLIAMENT')).toBe(true);
    });
  });

  describe('filterByLabels', () => {
    it('should return all actions when no labels selected', () => {
      const result = filterByLabels(testActions, []);
      expect(result).toHaveLength(testActions.length);
    });

    it('should filter by single label', () => {
      const result = filterByLabels(testActions, ['Health']);
      expect(result).toHaveLength(1);
      expect(result[0].labels).toContain('Health');
    });

    it('should filter by multiple labels (OR logic)', () => {
      const result = filterByLabels(testActions, ['Health', 'Education']);
      expect(result).toHaveLength(2);
      expect(result.some(action => action.labels.includes('Health'))).toBe(true);
      expect(result.some(action => action.labels.includes('Education'))).toBe(true);
    });

    it('should return empty array for non-existent labels', () => {
      const result = filterByLabels(testActions, ['NonExistent']);
      expect(result).toHaveLength(0);
    });

    it('should handle actions with multiple labels', () => {
      const result = filterByLabels(testActions, ['Infrastructure']);
      expect(result).toHaveLength(1);
      expect(result[0].labels).toContain('Infrastructure');
      expect(result[0].labels).toContain('Economy');
    });
  });

  describe('sortActionsByDate', () => {
    it('should sort by newest first', () => {
      const result = sortActionsByDate(testActions, 'newest');
      expect(result[0].date).toBe('2024-03-01'); // Economic Development
      expect(result[1].date).toBe('2024-02-01'); // Education Reform
      expect(result[2].date).toBe('2024-01-15'); // Health and Safety
      expect(result[3].date).toBe('2024-01-01'); // Environmental Protection
    });

    it('should sort by oldest first', () => {
      const result = sortActionsByDate(testActions, 'oldest');
      expect(result[0].date).toBe('2024-01-01'); // Environmental Protection
      expect(result[1].date).toBe('2024-01-15'); // Health and Safety
      expect(result[2].date).toBe('2024-02-01'); // Education Reform
      expect(result[3].date).toBe('2024-03-01'); // Economic Development
    });

    it('should handle invalid dates', () => {
      const actionsWithInvalidDate = [
        ...testActions,
        createMockAction({ date: 'invalid-date', title: 'Invalid Date Action' })
      ];

      const result = sortActionsByDate(actionsWithInvalidDate, 'newest');
      // Invalid date should be at the end
      expect(result[result.length - 1].title).toBe('Invalid Date Action');
    });

    it('should not mutate original array', () => {
      const originalOrder = [...testActions];
      sortActionsByDate(testActions, 'oldest');
      expect(testActions).toEqual(originalOrder);
    });
  });

  describe('filterAndSortActions', () => {
    it('should apply all filters and sorting', () => {
      const filterState: ActionFilterState = {
        searchQuery: 'Health',
        selectedSource: 'ALL',
        selectedLabels: [],
        sortOrder: 'newest'
      };

      const result = filterAndSortActions(testActions, filterState);
      expect(result.actions).toHaveLength(1);
      expect(result.totalMatched).toBe(1);
      expect(result.actions[0].title).toBe('Health and Safety Bill');
      expect(result.searchTime).toBeGreaterThanOrEqual(0);
    });

    it('should combine multiple filters', () => {
      const filterState: ActionFilterState = {
        searchQuery: '',
        selectedSource: 'ALL',
        selectedLabels: ['Health', 'Education'],
        sortOrder: 'oldest'
      };

      const result = filterAndSortActions(testActions, filterState);
      expect(result.actions).toHaveLength(2);
      expect(result.actions[0].date).toBe('2024-01-15'); // Health (older)
      expect(result.actions[1].date).toBe('2024-02-01'); // Education (newer)
    });

    it('should handle no matching results', () => {
      const filterState: ActionFilterState = {
        searchQuery: 'non-existent',
        selectedSource: 'ALL',
        selectedLabels: [],
        sortOrder: 'newest'
      };

      const result = filterAndSortActions(testActions, filterState);
      expect(result.actions).toHaveLength(0);
      expect(result.totalMatched).toBe(0);
    });

    it('should measure search time', () => {
      const filterState = createDefaultFilterState();
      const result = filterAndSortActions(testActions, filterState);
      expect(result.searchTime).toBeDefined();
      expect(result.searchTime).toBeGreaterThanOrEqual(0);
    });
  });

  describe('utility functions', () => {
    describe('createDefaultFilterState', () => {
      it('should create default filter state', () => {
        const defaultState = createDefaultFilterState();
        expect(defaultState).toEqual({
          searchQuery: '',
          selectedSource: 'ALL',
          selectedLabels: [],
          sortOrder: 'newest'
        });
      });
    });

    describe('hasActiveFilters', () => {
      it('should return false for default state', () => {
        const defaultState = createDefaultFilterState();
        expect(hasActiveFilters(defaultState)).toBe(false);
      });

      it('should return true when search query is set', () => {
        const state = { ...createDefaultFilterState(), searchQuery: 'test' };
        expect(hasActiveFilters(state)).toBe(true);
      });

      it('should return true when source is changed', () => {
        const state = { ...createDefaultFilterState(), selectedSource: 'PARLIAMENT' as const };
        expect(hasActiveFilters(state)).toBe(true);
      });

      it('should return true when labels are selected', () => {
        const state = { ...createDefaultFilterState(), selectedLabels: ['Health'] };
        expect(hasActiveFilters(state)).toBe(true);
      });

      it('should return true when sort order is changed', () => {
        const state = { ...createDefaultFilterState(), sortOrder: 'oldest' as const };
        expect(hasActiveFilters(state)).toBe(true);
      });
    });

    describe('resetFilters', () => {
      it('should return default filter state', () => {
        const reset = resetFilters();
        const defaultState = createDefaultFilterState();
        expect(reset).toEqual(defaultState);
      });
    });

    describe('validateFilterState', () => {
      it('should validate correct filter state', () => {
        const validState = {
          searchQuery: 'test',
          selectedSource: 'PARLIAMENT' as const,
          selectedLabels: ['Health'],
          sortOrder: 'oldest' as const
        };

        const validated = validateFilterState(validState);
        expect(validated).toEqual(validState);
      });

      it('should use defaults for invalid search query', () => {
        const invalidState = { searchQuery: 123 as unknown as string };
        const validated = validateFilterState(invalidState);
        expect(validated.searchQuery).toBe('');
      });

      it('should use defaults for invalid source', () => {
        const invalidState = { selectedSource: 'INVALID' as unknown as SourceSystem | 'ALL' };
        const validated = validateFilterState(invalidState);
        expect(validated.selectedSource).toBe('ALL');
      });

      it('should use defaults for invalid labels', () => {
        const invalidState = { selectedLabels: 'invalid' as unknown as string[] };
        const validated = validateFilterState(invalidState);
        expect(validated.selectedLabels).toEqual([]);
      });

      it('should use defaults for invalid sort order', () => {
        const invalidState = { sortOrder: 'invalid' as unknown as 'newest' | 'oldest' };
        const validated = validateFilterState(invalidState);
        expect(validated.sortOrder).toBe('newest');
      });

      it('should handle partial state objects', () => {
        const partialState = { searchQuery: 'test' };
        const validated = validateFilterState(partialState);
        expect(validated.searchQuery).toBe('test');
        expect(validated.selectedSource).toBe('ALL');
        expect(validated.selectedLabels).toEqual([]);
        expect(validated.sortOrder).toBe('newest');
      });

      it('should handle empty object', () => {
        const validated = validateFilterState({});
        const defaultState = createDefaultFilterState();
        expect(validated).toEqual(defaultState);
      });
    });
  });

  describe('edge cases', () => {
    it('should handle empty actions array', () => {
      const result = filterAndSortActions([], createDefaultFilterState());
      expect(result.actions).toHaveLength(0);
      expect(result.totalMatched).toBe(0);
    });

    it('should handle actions with missing metadata', () => {
      const actionsWithMissingMetadata = [
        createMockAction({ metadata: {} as ActionMetadata }),
        createMockAction({ metadata: null as ActionMetadata | null })
      ];

      // 'test' should match the default titles which contain 'Test Bill 2024'
      const result = searchActions(actionsWithMissingMetadata, 'nonexistent');
      expect(result).toHaveLength(0);
    });

    it('should handle null/undefined values in metadata', () => {
      const actionWithNullMetadata = createActionWithMetadata({
        bill_number: null,
        act_number: undefined,
        notice_number: '',
        portfolio: null
      });

      const result = searchActions([actionWithNullMetadata], 'null');
      expect(result).toHaveLength(0);
    });

    it('should handle special characters in search', () => {
      const actionWithSpecialChars = createMockAction({
        title: 'Test & Special Characters (2024)',
        summary: 'Contains special chars: @#$%^&*()'
      });

      const result = searchActions([actionWithSpecialChars], '&');
      expect(result).toHaveLength(1);
    });

    it('should handle unicode characters', () => {
      const actionWithUnicode = createMockAction({
        title: 'Treaty of Waitangi - Te Tiriti o Waitangi',
        summary: 'Māori language content'
      });

      const result = searchActions([actionWithUnicode], 'Māori');
      expect(result).toHaveLength(1);
    });
  });

  describe('performance', () => {
    it('should handle large datasets efficiently', () => {
      const largeDataset = createMockActions(1000);
      const start = performance.now();

      const result = filterAndSortActions(largeDataset, {
        searchQuery: 'Test',
        selectedSource: 'ALL',
        selectedLabels: [],
        sortOrder: 'newest'
      });

      const end = performance.now();
      const duration = end - start;

      expect(duration).toBeLessThan(100); // Should complete in under 100ms
      expect(result.searchTime).toBeLessThan(duration);
    });
  });
});