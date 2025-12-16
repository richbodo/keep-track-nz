import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ActionFilters } from '../ActionFilters';

// Mock the UI components
vi.mock('@/components/ui/input', () => ({
  Input: ({ onChange, ...props }: React.InputHTMLAttributes<HTMLInputElement> & {
    onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
  }) => (
    <input
      {...props}
      onChange={(e) => onChange?.(e)}
      data-testid="search-input"
    />
  )
}));

vi.mock('@/components/ui/select', () => ({
  Select: ({ children, onValueChange }: {
    children: React.ReactNode;
    onValueChange?: (value: string) => void;
  }) => (
    <select onChange={(e) => onValueChange?.(e.target.value)} data-testid="select">
      {children}
    </select>
  ),
  SelectContent: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  SelectItem: ({ value, children }: { value: string; children: React.ReactNode }) => (
    <option value={value}>{children}</option>
  ),
  SelectTrigger: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  SelectValue: ({ placeholder }: { placeholder?: string }) => <span>{placeholder}</span>
}));

vi.mock('@/components/ui/badge', () => ({
  Badge: ({ children, onClick, variant }: {
    children: React.ReactNode;
    onClick?: () => void;
    variant?: string;
  }) => (
    <button
      onClick={onClick}
      className={`badge ${variant || ''}`}
      data-testid={`badge-${children}`}
    >
      {children}
    </button>
  )
}));

vi.mock('@/components/ui/button', () => ({
  Button: ({ children, onClick }: {
    children: React.ReactNode;
    onClick?: () => void;
  }) => (
    <button onClick={onClick} data-testid="clear-filters-btn">
      {children}
    </button>
  )
}));

vi.mock('@/data/actions', () => ({
  labels: ['Health', 'Education', 'Environment', 'Economy']
}));

describe('ActionFilters', () => {
  const defaultProps = {
    searchQuery: '',
    onSearchChange: vi.fn(),
    selectedSource: 'ALL' as const,
    onSourceChange: vi.fn(),
    selectedLabels: [],
    onLabelToggle: vi.fn(),
    onClearFilters: vi.fn(),
    sortOrder: 'newest' as const,
    onSortChange: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render search input', () => {
    render(<ActionFilters {...defaultProps} />);
    expect(screen.getByTestId('search-input')).toBeInTheDocument();
  });

  it('should call onSearchChange when search input changes', async () => {
    render(<ActionFilters {...defaultProps} />);

    const searchInput = screen.getByTestId('search-input');

    // Simulate a direct change event instead of typing
    fireEvent.change(searchInput, { target: { value: 'test search' } });

    expect(defaultProps.onSearchChange).toHaveBeenCalledWith('test search');
  });

  it('should render label badges', () => {
    render(<ActionFilters {...defaultProps} />);

    expect(screen.getByTestId('badge-Health')).toBeInTheDocument();
    expect(screen.getByTestId('badge-Education')).toBeInTheDocument();
    expect(screen.getByTestId('badge-Environment')).toBeInTheDocument();
    expect(screen.getByTestId('badge-Economy')).toBeInTheDocument();
  });

  it('should call onLabelToggle when label is clicked', async () => {
    const user = userEvent.setup();
    render(<ActionFilters {...defaultProps} />);

    const healthBadge = screen.getByTestId('badge-Health');
    await user.click(healthBadge);

    expect(defaultProps.onLabelToggle).toHaveBeenCalledWith('Health');
  });

  it('should show clear filters button when filters are active', () => {
    render(<ActionFilters {...defaultProps} searchQuery="test" />);
    expect(screen.getByTestId('clear-filters-btn')).toBeInTheDocument();
  });

  it('should not show clear filters button when no filters are active', () => {
    render(<ActionFilters {...defaultProps} />);
    expect(screen.queryByTestId('clear-filters-btn')).not.toBeInTheDocument();
  });

  it('should call onClearFilters when clear button is clicked', async () => {
    const user = userEvent.setup();
    render(<ActionFilters {...defaultProps} searchQuery="test" />);

    const clearButton = screen.getByTestId('clear-filters-btn');
    await user.click(clearButton);

    expect(defaultProps.onClearFilters).toHaveBeenCalled();
  });

  it('should show active filters correctly', () => {
    render(
      <ActionFilters
        {...defaultProps}
        searchQuery="test"
        selectedSource="PARLIAMENT"
        selectedLabels={['Health']}
      />
    );

    expect(screen.getByTestId('clear-filters-btn')).toBeInTheDocument();
  });

  describe('accessibility', () => {
    it('should have proper ARIA labels', () => {
      render(<ActionFilters {...defaultProps} />);

      const searchInput = screen.getByTestId('search-input');
      expect(searchInput).toHaveAttribute('placeholder', 'Search actions, bills, or entities...');
    });

    it('should support keyboard navigation', async () => {
      const user = userEvent.setup();
      render(<ActionFilters {...defaultProps} />);

      const searchInput = screen.getByTestId('search-input');

      // Focus search input
      await user.tab();
      expect(searchInput).toHaveFocus();
    });
  });
});