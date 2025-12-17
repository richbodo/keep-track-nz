import { useState, useMemo, useCallback } from 'react';
import { Header } from '@/components/Header';
import { Footer } from '@/components/Footer';
import { ActionCard } from '@/components/ActionCard';
import { ActionFilters } from '@/components/ActionFilters';
import { actions, type SourceSystem } from '@/data/actions';
import {
  filterAndSortActions,
  createDefaultFilterState,
  hasActiveFilters,
  validateFilterState,
  type ActionFilterState
} from '@/lib/actionFilters';

const Index = () => {
  // Initialize filter state using the new utility function
  const [filterState, setFilterState] = useState<ActionFilterState>(() =>
    createDefaultFilterState()
  );

  // Memoized filtering with performance tracking
  const filterResult = useMemo(() => {
    // Validate filter state to ensure data integrity
    const validatedState = validateFilterState(filterState);

    // Apply all filters using our comprehensive filtering logic
    return filterAndSortActions(actions, validatedState);
  }, [filterState]);

  // Extract results for easier access
  const { actions: filteredActions, totalMatched, searchTime } = filterResult;

  // Handler functions with proper state management and error handling
  const handleSearchChange = useCallback((searchQuery: string) => {
    setFilterState(prev => ({ ...prev, searchQuery }));
  }, []);

  const handleSourceChange = useCallback((selectedSource: SourceSystem | 'ALL') => {
    setFilterState(prev => ({ ...prev, selectedSource }));
  }, []);

  const handleLabelToggle = useCallback((label: string) => {
    setFilterState(prev => ({
      ...prev,
      selectedLabels: prev.selectedLabels.includes(label)
        ? prev.selectedLabels.filter((l) => l !== label)
        : [...prev.selectedLabels, label]
    }));
  }, []);

  const handleSortChange = useCallback((sortOrder: 'newest' | 'oldest') => {
    setFilterState(prev => ({ ...prev, sortOrder }));
  }, []);

  const handleClearFilters = useCallback(() => {
    setFilterState(createDefaultFilterState());
  }, []);

  // Check if we have active filters for UI purposes
  const hasActiveFiltersState = hasActiveFilters(filterState);

  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex-1">
        <div className="container mx-auto px-4 py-8">
          <div className="mb-8">
            <h2 className="font-serif text-2xl font-bold">Government Actions</h2>
            <p className="mt-1 text-muted-foreground">
              All official actions from the 54th Parliament, National-led Coalition
            </p>
          </div>

          <div className="mb-6">
            <ActionFilters
              searchQuery={filterState.searchQuery}
              onSearchChange={handleSearchChange}
              selectedSource={filterState.selectedSource}
              onSourceChange={handleSourceChange}
              selectedLabels={filterState.selectedLabels}
              onLabelToggle={handleLabelToggle}
              onClearFilters={handleClearFilters}
              sortOrder={filterState.sortOrder}
              onSortChange={handleSortChange}
            />
          </div>

          <div className="mb-4 text-sm text-muted-foreground">
            Showing {totalMatched} of {actions.length} actions
            {searchTime && searchTime > 0 && (
              <span className="ml-2 text-xs text-muted-foreground/70">
                (search completed in {searchTime.toFixed(1)}ms)
              </span>
            )}
          </div>

          <div className="space-y-4">
            {filteredActions.map((action) => (
              <ActionCard key={action.id} action={action} />
            ))}
          </div>

          {filteredActions.length === 0 && (
            <div className="py-12 text-center">
              <p className="text-muted-foreground">No actions match your filters.</p>
            </div>
          )}
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default Index;
