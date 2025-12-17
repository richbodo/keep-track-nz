import { GovernmentAction, SourceSystem } from '@/data/actions';

/**
 * Filter state interface for managing all filter parameters
 */
export interface ActionFilterState {
  searchQuery: string;
  selectedSource: SourceSystem | 'ALL';
  selectedLabels: string[];
  sortOrder: 'newest' | 'oldest';
}

/**
 * Search configuration interface
 */
export interface SearchConfig {
  caseSensitive?: boolean;
  exactMatch?: boolean;
  searchMetadata?: boolean;
  searchStageHistory?: boolean;
}

/**
 * Filter result interface
 */
export interface FilterResult {
  actions: GovernmentAction[];
  totalMatched: number;
  searchTime?: number;
}

/**
 * Default search configuration
 */
const DEFAULT_SEARCH_CONFIG: Required<SearchConfig> = {
  caseSensitive: false,
  exactMatch: false,
  searchMetadata: true,
  searchStageHistory: true,
};

/**
 * Normalize string for searching - handles case sensitivity and whitespace
 */
function normalizeSearchString(str: string, caseSensitive = false): string {
  let normalized = str.trim();
  if (!caseSensitive) {
    normalized = normalized.toLowerCase();
  }
  return normalized;
}

/**
 * Check if a value exists and contains the search query
 */
function matchesSearchQuery(
  value: string | number | null | undefined,
  query: string,
  config: Required<SearchConfig>
): boolean {
  if (!value || !query) return false;

  const stringValue = String(value);
  const normalizedValue = normalizeSearchString(stringValue, config.caseSensitive);
  const normalizedQuery = normalizeSearchString(query, config.caseSensitive);

  if (config.exactMatch) {
    return normalizedValue === normalizedQuery;
  }

  return normalizedValue.includes(normalizedQuery);
}

/**
 * Search through stage history for matching terms
 */
function searchStageHistory(
  stageHistory: Array<{ stage: string; date: string }> | null | undefined,
  query: string,
  config: Required<SearchConfig>
): boolean {
  if (!config.searchStageHistory || !stageHistory || !query) return false;

  return stageHistory.some(stage =>
    matchesSearchQuery(stage.stage, query, config) ||
    matchesSearchQuery(stage.date, query, config)
  );
}

/**
 * Comprehensive search function that searches all action fields and metadata
 */
export function searchActions(
  actions: GovernmentAction[],
  searchQuery: string,
  config: SearchConfig = {}
): GovernmentAction[] {
  if (!searchQuery.trim()) return actions;

  const searchConfig = { ...DEFAULT_SEARCH_CONFIG, ...config };
  const query = searchQuery.trim();

  return actions.filter(action => {
    // Search basic fields
    if (
      matchesSearchQuery(action.title, query, searchConfig) ||
      matchesSearchQuery(action.summary, query, searchConfig) ||
      matchesSearchQuery(action.primary_entity, query, searchConfig) ||
      matchesSearchQuery(action.url, query, searchConfig) ||
      matchesSearchQuery(action.id, query, searchConfig)
    ) {
      return true;
    }

    // Search labels array
    if (action.labels.some(label => matchesSearchQuery(label, query, searchConfig))) {
      return true;
    }

    // Search metadata if enabled
    if (searchConfig.searchMetadata && action.metadata) {
      const metadata = action.metadata;
      if (
        matchesSearchQuery(metadata.bill_number, query, searchConfig) ||
        matchesSearchQuery(metadata.act_number, query, searchConfig) ||
        matchesSearchQuery(metadata.notice_number, query, searchConfig) ||
        matchesSearchQuery(metadata.notice_type, query, searchConfig) ||
        matchesSearchQuery(metadata.document_type, query, searchConfig) ||
        matchesSearchQuery(metadata.portfolio, query, searchConfig) ||
        matchesSearchQuery(metadata.parliament_number, query, searchConfig) ||
        matchesSearchQuery(metadata.commencement_date, query, searchConfig)
      ) {
        return true;
      }

      // Search stage history
      if (searchStageHistory(metadata.stage_history, query, searchConfig)) {
        return true;
      }
    }

    return false;
  });
}

/**
 * Filter actions by source system
 */
export function filterBySource(
  actions: GovernmentAction[],
  selectedSource: SourceSystem | 'ALL'
): GovernmentAction[] {
  if (selectedSource === 'ALL') return actions;
  return actions.filter(action => action.source_system === selectedSource);
}

/**
 * Filter actions by selected labels (OR logic - action must have at least one selected label)
 */
export function filterByLabels(
  actions: GovernmentAction[],
  selectedLabels: string[]
): GovernmentAction[] {
  if (selectedLabels.length === 0) return actions;

  return actions.filter(action =>
    selectedLabels.some(label => action.labels.includes(label))
  );
}

/**
 * Sort actions by date
 */
export function sortActionsByDate(
  actions: GovernmentAction[],
  sortOrder: 'newest' | 'oldest'
): GovernmentAction[] {
  const sorted = [...actions];

  sorted.sort((a, b) => {
    const dateA = new Date(a.date).getTime();
    const dateB = new Date(b.date).getTime();

    // Handle invalid dates
    if (isNaN(dateA) && isNaN(dateB)) return 0;
    if (isNaN(dateA)) return 1; // Invalid dates go to end
    if (isNaN(dateB)) return -1;

    return sortOrder === 'newest' ? dateB - dateA : dateA - dateB;
  });

  return sorted;
}

/**
 * Apply all filters and sorting to actions
 * This is the main function that combines all filtering logic
 */
export function filterAndSortActions(
  actions: GovernmentAction[],
  filterState: ActionFilterState,
  searchConfig?: SearchConfig
): FilterResult {
  const startTime = performance.now();

  let filtered = [...actions];

  // Apply search filter
  if (filterState.searchQuery.trim()) {
    filtered = searchActions(filtered, filterState.searchQuery, searchConfig);
  }

  // Apply source filter
  filtered = filterBySource(filtered, filterState.selectedSource);

  // Apply label filter
  filtered = filterByLabels(filtered, filterState.selectedLabels);

  // Apply sorting
  filtered = sortActionsByDate(filtered, filterState.sortOrder);

  const endTime = performance.now();

  return {
    actions: filtered,
    totalMatched: filtered.length,
    searchTime: endTime - startTime,
  };
}

/**
 * Create a default filter state
 */
export function createDefaultFilterState(): ActionFilterState {
  return {
    searchQuery: '',
    selectedSource: 'ALL',
    selectedLabels: [],
    sortOrder: 'newest',
  };
}

/**
 * Check if any filters are active (non-default state)
 */
export function hasActiveFilters(filterState: ActionFilterState): boolean {
  const defaultState = createDefaultFilterState();
  return (
    filterState.searchQuery !== defaultState.searchQuery ||
    filterState.selectedSource !== defaultState.selectedSource ||
    filterState.selectedLabels.length !== defaultState.selectedLabels.length ||
    filterState.sortOrder !== defaultState.sortOrder
  );
}

/**
 * Reset all filters to default state
 */
export function resetFilters(): ActionFilterState {
  return createDefaultFilterState();
}

/**
 * Validate filter state to ensure data integrity
 */
export function validateFilterState(filterState: Partial<ActionFilterState>): ActionFilterState {
  const defaults = createDefaultFilterState();

  return {
    searchQuery: typeof filterState.searchQuery === 'string' ? filterState.searchQuery : defaults.searchQuery,
    selectedSource: filterState.selectedSource &&
      ['ALL', 'PARLIAMENT', 'LEGISLATION', 'GAZETTE', 'BEEHIVE'].includes(filterState.selectedSource)
      ? filterState.selectedSource : defaults.selectedSource,
    selectedLabels: Array.isArray(filterState.selectedLabels) ? filterState.selectedLabels : defaults.selectedLabels,
    sortOrder: filterState.sortOrder && ['newest', 'oldest'].includes(filterState.sortOrder)
      ? filterState.sortOrder : defaults.sortOrder,
  };
}