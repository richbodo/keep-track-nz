# Feature: Fix Action Filtering and Sorting Implementation

## Feature Description
Re-implement the filtering and sorting functionality for the four main UI elements on the main page: search bar, sources dropdown, sort order dropdown, and category tags. The current implementation has incorrect and incomplete filtering logic that needs to be completely redesigned to work correctly together. The search function is particularly incomplete, only searching a few fields instead of performing full-text search across all action data and metadata.

## User Story
As a user tracking NZ government actions
I want to filter and sort actions using multiple criteria (search, source, category tags, date order)
So that I can quickly find specific actions or browse actions in my preferred view

## Problem Statement
The current filtering implementation in `src/pages/Index.tsx` has several critical issues:
1. **Incomplete Search**: Search only covers title, summary, and primary_entity fields, missing URL, labels, and all metadata fields (bill_number, act_number, notice_number, notice_type, document_type, portfolio, stage_history)
2. **Missing Full-Text Search**: Requirements specify full-text search across all action data and metadata, but current implementation is limited
3. **Untested Logic**: No comprehensive tests exist to verify filter combinations work correctly
4. **Poor User Experience**: Users cannot find actions that contain search terms in metadata or other important fields

## Solution Statement
Completely re-implement the filtering logic to perform true full-text search across all action fields and metadata, ensure all filter combinations work correctly, and add comprehensive testing to prevent regressions. Create utility functions for search logic and implement proper TypeScript typing for filter state management.

## Relevant Files
Use these files to implement the feature:

- `src/pages/Index.tsx` - Main page component containing current filtering logic that needs to be re-implemented
- `src/components/ActionFilters.tsx` - UI components for the four filtering controls (search, source, sort, category tags)
- `src/data/actions.ts` - Contains the GovernmentAction interface and ActionMetadata interface defining searchable fields
- `src/components/ActionCard.tsx` - Displays individual actions, may need updates for highlighting search results

### New Files
- `src/lib/actionFilters.ts` - New utility functions for filtering and searching actions
- `src/lib/actionFilters.test.ts` - Comprehensive tests for filtering logic
- `src/components/__tests__/ActionFilters.test.tsx` - Component tests for filter UI
- `src/pages/__tests__/Index.test.tsx` - Integration tests for the main page filtering

## Implementation Plan

### Phase 1: Foundation
Set up testing infrastructure and create utility functions for the new filtering logic. This provides a solid foundation for implementing and testing the complex filtering requirements.

### Phase 2: Core Implementation
Re-implement the filtering logic with comprehensive full-text search across all action fields and metadata. Ensure all filter combinations work correctly together.

### Phase 3: Integration
Update the main page component to use the new filtering logic and add comprehensive tests to ensure no regressions in existing functionality.

## Step by Step Tasks

### Setup Testing Infrastructure
- Install and configure testing dependencies (Vitest, React Testing Library)
- Create test utilities for mocking action data and filter states
- Set up test coverage reporting for filtering functions

### Create Filter Utility Functions
- Design TypeScript interfaces for filter state and search parameters
- Implement full-text search function that searches all action fields and metadata
- Create individual filter functions for source, labels, and date sorting
- Implement combined filter function that applies all filters in the correct order

### Implement Comprehensive Search Logic
- Create search function that searches title, summary, primary_entity, url, and labels
- Add metadata search across bill_number, act_number, notice_number, notice_type, document_type, portfolio
- Implement stage_history search that looks through stage names and dates
- Add case-insensitive matching and proper string normalization

### Write Comprehensive Tests
- Create unit tests for each filter function with edge cases
- Test search function with various metadata combinations
- Test filter combinations (search + source + labels + sorting)
- Add integration tests for the complete filtering workflow

### Update Main Page Component
- Replace current filtering logic with new utility functions
- Ensure proper TypeScript typing for all filter state
- Maintain existing UI behavior while improving underlying logic
- Add proper error handling for invalid filter states

### Performance Testing and Optimization
- Add performance tests for large datasets
- Profile search performance with the full action dataset
- Implement any necessary optimizations for search speed
- Ensure filtering remains responsive with the complete data set

### Final Integration and Validation
- Run all existing tests to ensure no regressions
- Test complete user workflows through the UI
- Validate that all four filtering controls work correctly together
- Run the complete validation suite to confirm zero regressions

## Testing Strategy

### Unit Tests
- Test each individual filter function (search, source filter, label filter, date sorting)
- Test search function with each type of metadata field
- Test edge cases: empty search, no results, invalid dates, missing metadata
- Test filter combinations: multiple filters applied together

### Integration Tests
- Test the complete filtering workflow from UI interaction to filtered results
- Test filter state management and URL parameter synchronization
- Test performance with large datasets (current ~2000+ actions)
- Test real user scenarios: complex searches, multiple filter combinations

### Edge Cases
- Empty search queries and filter states
- Actions with missing or null metadata fields
- Invalid date formats in stage_history
- Special characters and unicode in search queries
- Very large search result sets and very small result sets

## Acceptance Criteria
- [ ] Search bar performs full-text search across all action fields: title, summary, primary_entity, url, labels
- [ ] Search includes all metadata fields: bill_number, act_number, notice_number, notice_type, document_type, portfolio
- [ ] Search includes stage_history data (stage names and dates)
- [ ] Sources dropdown correctly filters to ALL SOURCES or ONE SOURCE
- [ ] Sort Order dropdown correctly sorts filtered results by newest or oldest date
- [ ] Category tags multi-select correctly filters to actions with one or more selected labels
- [ ] All four filter controls work correctly in combination
- [ ] Filter state is properly managed and doesn't cause unnecessary re-renders
- [ ] Search is case-insensitive and handles special characters correctly
- [ ] No regressions in existing functionality
- [ ] Comprehensive test coverage (>90%) for all filtering logic
- [ ] Performance remains responsive with the full dataset

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `npm run dev` - Start development server to manually test filtering functionality
- `npm run build` - Build production version to ensure no TypeScript errors
- `npm run lint` - Run linting to ensure code quality standards
- `npm test` - Run all frontend tests including new filtering tests
- `cd backend && uv run pytest` - Run server tests to validate the feature works with zero regressions

## Notes
- Current dataset contains 2000+ government actions with rich metadata
- Search performance should be optimized for this scale but remain responsive
- Consider implementing search result highlighting in future iterations
- The filtering logic should be easily extensible for future filter types
- Maintain backward compatibility with any existing URL parameters or bookmarks
- Consider adding search analytics or usage tracking in future versions