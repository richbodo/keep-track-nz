# Bug: Source Dropdown Filtering Returns No Results for Parliament and Beehive

## Bug Description
The source dropdown on the main web page does not work properly. When users select 'Parliament' or 'Beehive' from the source dropdown and select all tags (or any tags), no actions are displayed. Additionally, the filtering system needs to ensure that source filtering works correctly with tag selection - when both a specific source and specific tags are selected, only actions from that source containing at least one of the selected tags should be displayed.

Expected behavior:
- Source filtering should display actions from the selected source
- Combined source + tag filtering should display actions from the selected source that have at least one of the selected tags
- All available sources in the dropdown should have corresponding data to filter

Actual behavior:
- Selecting 'Parliament' + any tags = 0 results (should show Parliament actions with those tags)
- Selecting 'Beehive' + any tags = 0 results (should show Beehive actions with those tags)
- Selecting 'Legislation' + tags = works correctly (139 available actions)
- Selecting 'Gazette' + tags = works correctly (100 available actions)

## Problem Statement
The UI offers source filtering options (Parliament, Beehive) that have no corresponding data in the current dataset, causing the filtering system to return empty results when users select these unavailable sources. This creates a poor user experience where the interface suggests functionality that doesn't work.

## Solution Statement
Implement dynamic source dropdown population based on available data in the dataset, and enhance the filtering system with comprehensive tests to ensure source and tag filtering work correctly in all combinations. The solution will prevent users from selecting unavailable sources while maintaining the existing filtering logic.

## Steps to Reproduce
1. Open the main web page (Index.tsx)
2. Click on the source dropdown
3. Select 'Parliament' from the dropdown
4. Click on any tag badges (e.g., "Health", "Housing") or leave all tags unselected
5. Observe that no actions are displayed
6. Repeat steps 2-5 with 'Beehive' source
7. Verify the issue: Expected to see actions from Parliament/Beehive source, but see "No actions match your filters" message

## Root Cause Analysis
The root cause is a **data availability mismatch** between the UI and the dataset:

1. **Frontend UI provides these source options** (`src/components/ActionFilters.tsx:58-63`):
   - "All sources" (ALL) ✅
   - "Parliament" (PARLIAMENT) ❌ **No data available**
   - "Legislation" (LEGISLATION) ✅ **139 actions available**
   - "Gazette" (GAZETTE) ✅ **100 actions available**
   - "Beehive" (BEEHIVE) ❌ **No data available**

2. **Dataset analysis** (`src/data/actions.ts`):
   - Total actions: 239
   - LEGISLATION source: 139 actions
   - GAZETTE source: 100 actions
   - PARLIAMENT source: 0 actions
   - BEEHIVE source: 0 actions

3. **Filtering logic** (`src/lib/actionFilters.ts:149-155`):
   - `filterBySource()` correctly filters by `action.source_system === selectedSource`
   - When selectedSource is 'PARLIAMENT', no actions match because none have `source_system: 'PARLIAMENT'`
   - The filtering logic itself is correct - the issue is missing data for certain source types

## Relevant Files
Use these files to fix the bug:

- **`src/components/ActionFilters.tsx`** (lines 57-63) - Contains hardcoded source dropdown options that include unavailable sources
- **`src/lib/actionFilters.ts`** (lines 149-155, 199-229) - Source filtering logic and main filter orchestration function
- **`src/data/actions.ts`** (line 17, lines 67+) - Source type definitions and actual data
- **`src/pages/Index.tsx`** - Main page that uses the filtering system, good place to add data validation

### New Files
- **`src/lib/sourceUtils.ts`** - Utility functions to extract available sources from data
- **`src/lib/__tests__/sourceUtils.test.ts`** - Tests for source utility functions
- **`src/components/__tests__/ActionFilters.integration.test.tsx`** - Integration tests for source filtering with real data scenarios

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Create Source Utility Functions
- Create `src/lib/sourceUtils.ts` with functions to extract available sources from action data
- Add `getAvailableSources()` function that analyzes the dataset and returns only sources that have data
- Add `getSourceCounts()` function that returns the count of actions per source
- Add type safety and validation for source operations

### Step 2: Update ActionFilters Component to Use Dynamic Sources
- Modify `src/components/ActionFilters.tsx` to accept available sources as a prop instead of hardcoding them
- Update the source dropdown to only show sources that have corresponding data
- Add optional display of action counts per source in the dropdown
- Maintain backward compatibility with the existing prop interface

### Step 3: Integrate Dynamic Sources in Index Page
- Update `src/pages/Index.tsx` to calculate available sources from the actions data
- Pass the dynamic source list to the ActionFilters component
- Add validation to ensure selected source is always available
- Handle edge case where selected source becomes unavailable after data updates

### Step 4: Enhance Filtering Logic Validation
- Update `src/lib/actionFilters.ts` to add validation functions for filter state
- Add `validateSourceAvailability()` function to check if selected source exists in data
- Enhance `validateFilterState()` function to reset to 'ALL' if selected source is unavailable
- Add logging/warnings when invalid source selections are detected

### Step 5: Create Comprehensive Tests for Source Filtering
- Create `src/lib/__tests__/sourceUtils.test.ts` to test source utility functions
- Test `getAvailableSources()` with various datasets (empty, single source, multiple sources)
- Test `getSourceCounts()` accuracy with duplicate handling
- Create `src/components/__tests__/ActionFilters.integration.test.tsx` for integration tests
- Test all source + tag filter combinations with realistic data scenarios
- Test edge cases: empty dataset, dataset with only one source type
- Test UI behavior when no sources are available vs when some sources are available

### Step 6: Add End-to-End Source and Tag Filtering Tests
- Extend existing test suites in `src/lib/actionFilters.test.ts`
- Add comprehensive test cases for source filtering scenarios:
  - Parliament + Housing tags = 0 results (expected behavior with current data)
  - Legislation + Housing tags = X results (should work)
  - All sources + Housing tags = Y results (should work)
  - Invalid source + any tags = defaults to 'ALL'
- Test the complete filter chain: source → tags → sort
- Verify filtering performance with large datasets

### Step 7: Update Component Tests for Dynamic Sources
- Update `src/components/__tests__/ActionFilters.test.tsx` to test with dynamic source props
- Test that component correctly displays only available sources
- Test that component handles empty available sources list
- Test that source selection callbacks work correctly with dynamic sources
- Add accessibility tests for dynamic source dropdown

### Step 8: Documentation and Error Handling
- Update component props documentation to reflect new dynamic source behavior
- Add JSDoc comments to new utility functions
- Add user-friendly error handling for edge cases
- Add development warnings when sources become unavailable

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `npm run test` - Run all tests to ensure no regressions in existing functionality
- `npm run test src/lib/__tests__/sourceUtils.test.ts` - Test new source utility functions
- `npm run test src/components/__tests__/ActionFilters.integration.test.tsx` - Test integration scenarios
- `npm run test src/lib/actionFilters.test.ts` - Test enhanced filtering logic
- `npm run test src/components/__tests__/ActionFilters.test.tsx` - Test component with dynamic sources
- `npm run lint` - Ensure code style compliance
- `npm run build` - Verify the application builds successfully
- Manual testing: Open application and verify source dropdown only shows 'All sources', 'Legislation', and 'Gazette' options
- Manual testing: Verify that selecting 'Legislation' + 'Housing' tag shows appropriate results
- Manual testing: Verify that selecting 'Gazette' + 'Health' tag shows appropriate results
- Manual testing: Verify that all source + tag combinations work as expected without returning empty results inappropriately

## Notes
- The filtering logic itself is working correctly - this is primarily a data availability and UI issue
- Current dataset contains 139 LEGISLATION actions and 100 GAZETTE actions, but 0 PARLIAMENT and 0 BEEHIVE actions
- The solution maintains existing filter behavior while preventing user confusion about unavailable sources
- Backend improvements (populating Parliament and Beehive data) would be a separate future enhancement
- Performance impact is minimal - source analysis runs once when component mounts and results can be memoized
- Solution is backward compatible - if backend adds Parliament/Beehive data in the future, the UI will automatically include those sources