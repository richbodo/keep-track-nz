import { Search, X } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import type { SourceSystem } from '@/data/actions';
import { labels } from '@/data/actions';

interface ActionFiltersProps {
  searchQuery: string;
  onSearchChange: (query: string) => void;
  selectedSource: SourceSystem | 'ALL';
  onSourceChange: (source: SourceSystem | 'ALL') => void;
  selectedLabels: string[];
  onLabelToggle: (label: string) => void;
  onClearFilters: () => void;
  sortOrder: 'newest' | 'oldest';
  onSortChange: (order: 'newest' | 'oldest') => void;
}

export function ActionFilters({
  searchQuery,
  onSearchChange,
  selectedSource,
  onSourceChange,
  selectedLabels,
  onLabelToggle,
  onClearFilters,
  sortOrder,
  onSortChange,
}: ActionFiltersProps) {
  const hasActiveFilters = searchQuery || selectedSource !== 'ALL' || selectedLabels.length > 0;

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            type="search"
            placeholder="Search actions, bills, or entities..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select value={selectedSource} onValueChange={(v) => onSourceChange(v as SourceSystem | 'ALL')}>
          <SelectTrigger className="w-full sm:w-[180px]">
            <SelectValue placeholder="All sources" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ALL">All sources</SelectItem>
            <SelectItem value="PARLIAMENT">Parliament</SelectItem>
            <SelectItem value="LEGISLATION">Legislation</SelectItem>
            <SelectItem value="GAZETTE">Gazette</SelectItem>
            <SelectItem value="BEEHIVE">Beehive</SelectItem>
          </SelectContent>
        </Select>
        <Select value={sortOrder} onValueChange={(v) => onSortChange(v as 'newest' | 'oldest')}>
          <SelectTrigger className="w-full sm:w-[140px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="newest">Newest first</SelectItem>
            <SelectItem value="oldest">Oldest first</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="flex flex-wrap gap-2">
        {labels.map((label) => (
          <Badge
            key={label}
            variant={selectedLabels.includes(label) ? 'default' : 'outline'}
            className="cursor-pointer transition-colors"
            onClick={() => onLabelToggle(label)}
          >
            {label}
          </Badge>
        ))}
      </div>

      {hasActiveFilters && (
        <Button
          variant="ghost"
          size="sm"
          onClick={onClearFilters}
          className="text-muted-foreground"
        >
          <X className="mr-1 h-3 w-3" />
          Clear filters
        </Button>
      )}
    </div>
  );
}
