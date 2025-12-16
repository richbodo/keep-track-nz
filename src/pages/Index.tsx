import { useState, useMemo } from 'react';
import { Header } from '@/components/Header';
import { Footer } from '@/components/Footer';
import { ActionCard } from '@/components/ActionCard';
import { ActionFilters } from '@/components/ActionFilters';
import { actions, type SourceSystem } from '@/data/actions';

const Index = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSource, setSelectedSource] = useState<SourceSystem | 'ALL'>('ALL');
  const [selectedLabels, setSelectedLabels] = useState<string[]>([]);
  const [sortOrder, setSortOrder] = useState<'newest' | 'oldest'>('newest');

  const filteredActions = useMemo(() => {
    let filtered = [...actions];

    // Filter by search
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (action) =>
          action.title.toLowerCase().includes(query) ||
          action.summary.toLowerCase().includes(query) ||
          action.primary_entity.toLowerCase().includes(query)
      );
    }

    // Filter by source
    if (selectedSource !== 'ALL') {
      filtered = filtered.filter((action) => action.source_system === selectedSource);
    }

    // Filter by labels
    if (selectedLabels.length > 0) {
      filtered = filtered.filter((action) =>
        selectedLabels.some((label) => action.labels.includes(label))
      );
    }

    // Sort
    filtered.sort((a, b) => {
      const dateA = new Date(a.date).getTime();
      const dateB = new Date(b.date).getTime();
      return sortOrder === 'newest' ? dateB - dateA : dateA - dateB;
    });

    return filtered;
  }, [searchQuery, selectedSource, selectedLabels, sortOrder]);

  const handleLabelToggle = (label: string) => {
    setSelectedLabels((prev) =>
      prev.includes(label) ? prev.filter((l) => l !== label) : [...prev, label]
    );
  };

  const handleClearFilters = () => {
    setSearchQuery('');
    setSelectedSource('ALL');
    setSelectedLabels([]);
  };

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
              searchQuery={searchQuery}
              onSearchChange={setSearchQuery}
              selectedSource={selectedSource}
              onSourceChange={setSelectedSource}
              selectedLabels={selectedLabels}
              onLabelToggle={handleLabelToggle}
              onClearFilters={handleClearFilters}
              sortOrder={sortOrder}
              onSortChange={setSortOrder}
            />
          </div>

          <div className="mb-4 text-sm text-muted-foreground">
            Showing {filteredActions.length} of {actions.length} actions
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
