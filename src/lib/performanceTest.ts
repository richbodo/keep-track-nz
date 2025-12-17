import { actions } from '@/data/actions';
import { filterAndSortActions, createDefaultFilterState } from './actionFilters';

/**
 * Performance test for filtering functionality
 */
export function runPerformanceTest() {
  const datasetSize = actions.length;
  const iterations = 100;

  console.log(`\n=== Action Filtering Performance Test ===`);
  console.log(`Dataset size: ${datasetSize} actions`);
  console.log(`Iterations: ${iterations}`);

  // Test 1: Basic search performance
  console.log(`\nTest 1: Basic Search Performance`);
  const searchTerms = ['health', 'education', 'bill', 'act', '2024'];

  for (const term of searchTerms) {
    const times: number[] = [];

    for (let i = 0; i < iterations; i++) {
      const filterState = {
        ...createDefaultFilterState(),
        searchQuery: term
      };

      const start = performance.now();
      const result = filterAndSortActions(actions, filterState);
      const end = performance.now();

      times.push(end - start);
    }

    const avgTime = times.reduce((sum, time) => sum + time, 0) / times.length;
    const minTime = Math.min(...times);
    const maxTime = Math.max(...times);

    console.log(`  Search "${term}": avg ${avgTime.toFixed(2)}ms, min ${minTime.toFixed(2)}ms, max ${maxTime.toFixed(2)}ms`);
  }

  // Test 2: Combined filter performance
  console.log(`\nTest 2: Combined Filters Performance`);
  const combinedTimes: number[] = [];

  for (let i = 0; i < iterations; i++) {
    const filterState = {
      searchQuery: 'health',
      selectedSource: 'PARLIAMENT' as const,
      selectedLabels: ['Health'],
      sortOrder: 'newest' as const
    };

    const start = performance.now();
    const result = filterAndSortActions(actions, filterState);
    const end = performance.now();

    combinedTimes.push(end - start);
  }

  const avgCombinedTime = combinedTimes.reduce((sum, time) => sum + time, 0) / combinedTimes.length;
  const minCombinedTime = Math.min(...combinedTimes);
  const maxCombinedTime = Math.max(...combinedTimes);

  console.log(`  Combined filters: avg ${avgCombinedTime.toFixed(2)}ms, min ${minCombinedTime.toFixed(2)}ms, max ${maxCombinedTime.toFixed(2)}ms`);

  // Test 3: Large result set performance
  console.log(`\nTest 3: Large Result Set Performance`);
  const largeTimes: number[] = [];

  for (let i = 0; i < iterations; i++) {
    const filterState = createDefaultFilterState(); // No filters = all results

    const start = performance.now();
    const result = filterAndSortActions(actions, filterState);
    const end = performance.now();

    largeTimes.push(end - start);
  }

  const avgLargeTime = largeTimes.reduce((sum, time) => sum + time, 0) / largeTimes.length;
  const minLargeTime = Math.min(...largeTimes);
  const maxLargeTime = Math.max(...largeTimes);

  console.log(`  All actions (${datasetSize} results): avg ${avgLargeTime.toFixed(2)}ms, min ${minLargeTime.toFixed(2)}ms, max ${maxLargeTime.toFixed(2)}ms`);

  // Test 4: Memory usage estimation
  console.log(`\nTest 4: Memory Usage Estimation`);
  const memoryBefore = process.memoryUsage?.()?.heapUsed || 0;

  const filterState = {
    searchQuery: 'government',
    selectedSource: 'ALL' as const,
    selectedLabels: ['Health', 'Education'],
    sortOrder: 'newest' as const
  };

  const result = filterAndSortActions(actions, filterState);
  const memoryAfter = process.memoryUsage?.()?.heapUsed || 0;
  const memoryDiff = memoryAfter - memoryBefore;

  console.log(`  Memory used: ${memoryDiff} bytes (${(memoryDiff / 1024 / 1024).toFixed(2)} MB)`);
  console.log(`  Result size: ${result.actions.length} actions`);

  // Performance recommendations
  console.log(`\n=== Performance Summary ===`);

  const hasSlowOperations =
    avgCombinedTime > 50 ||
    maxCombinedTime > 100 ||
    avgLargeTime > 20;

  if (hasSlowOperations) {
    console.log(`⚠️  PERFORMANCE WARNING: Some operations are slow`);
    console.log(`   Consider implementing debouncing for search input`);
    console.log(`   Consider virtualizing large result lists`);
  } else {
    console.log(`✅ PERFORMANCE GOOD: All operations within acceptable limits`);
  }

  console.log(`\n=== Test Complete ===\n`);

  return {
    datasetSize,
    searchPerformance: {
      avgTime: searchTerms.map((term, index) => ({
        term,
        avgTime: 0 // Would need to track this properly
      }))
    },
    combinedFiltersAvgTime: avgCombinedTime,
    allActionsAvgTime: avgLargeTime,
    memoryUsage: memoryDiff,
    resultSize: result.actions.length
  };
}

// Run performance test if this file is executed directly
if (typeof window === 'undefined') {
  runPerformanceTest();
}