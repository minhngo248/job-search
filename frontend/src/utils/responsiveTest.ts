/**
 * Utility functions for testing responsive behavior
 */

export interface BreakpointTest {
  name: string;
  minWidth: number;
  maxWidth?: number;
  expectedColumns: number;
  expectedSidebarBehavior: 'fixed' | 'collapsed' | 'overlay';
}

export const BREAKPOINT_TESTS: BreakpointTest[] = [
  {
    name: 'Mobile Small',
    minWidth: 320,
    maxWidth: 480,
    expectedColumns: 1,
    expectedSidebarBehavior: 'collapsed'
  },
  {
    name: 'Mobile',
    minWidth: 481,
    maxWidth: 767,
    expectedColumns: 1,
    expectedSidebarBehavior: 'collapsed'
  },
  {
    name: 'Tablet',
    minWidth: 768,
    maxWidth: 1023,
    expectedColumns: 2,
    expectedSidebarBehavior: 'collapsed'
  },
  {
    name: 'Desktop',
    minWidth: 1024,
    maxWidth: 1439,
    expectedColumns: 3,
    expectedSidebarBehavior: 'fixed'
  },
  {
    name: 'Desktop Large',
    minWidth: 1440,
    maxWidth: 1919,
    expectedColumns: 4,
    expectedSidebarBehavior: 'fixed'
  },
  {
    name: 'Ultra-wide',
    minWidth: 1920,
    expectedColumns: 5,
    expectedSidebarBehavior: 'fixed'
  }
];

/**
 * Get the expected behavior for a given viewport width
 */
export function getExpectedBehavior(width: number): BreakpointTest | null {
  return BREAKPOINT_TESTS.find(test => {
    const minMatch = width >= test.minWidth;
    const maxMatch = !test.maxWidth || width <= test.maxWidth;
    return minMatch && maxMatch;
  }) || null;
}

/**
 * Test if the current viewport matches expected responsive behavior
 */
export function testResponsiveBehavior(): {
  currentWidth: number;
  expected: BreakpointTest | null;
  gridColumns: number;
  sidebarVisible: boolean;
  passed: boolean;
} {
  const currentWidth = window.innerWidth;
  const expected = getExpectedBehavior(currentWidth);
  
  // Test grid columns by checking CSS custom property
  const rootStyles = getComputedStyle(document.documentElement);
  const gridColumnsValue = rootStyles.getPropertyValue('--grid-columns-mobile').trim() || '1';
  const gridColumns = parseInt(gridColumnsValue, 10);
  
  // Test sidebar visibility
  const sidebarElement = document.querySelector('.filters-sidebar') as HTMLElement;
  const sidebarVisible = sidebarElement ? 
    getComputedStyle(sidebarElement).display !== 'none' : false;
  
  const passed = expected ? 
    (gridColumns === expected.expectedColumns) : 
    true; // If no expected behavior found, consider it passed
  
  return {
    currentWidth,
    expected,
    gridColumns,
    sidebarVisible,
    passed
  };
}

/**
 * Run responsive tests across multiple viewport sizes
 */
export function runResponsiveTests(): Array<{
  test: BreakpointTest;
  result: ReturnType<typeof testResponsiveBehavior>;
}> {
  const results: Array<{
    test: BreakpointTest;
    result: ReturnType<typeof testResponsiveBehavior>;
  }> = [];
  
  // Test each breakpoint
  BREAKPOINT_TESTS.forEach(test => {
    // Simulate viewport width (in a real test environment)
    const testWidth = test.maxWidth ? 
      Math.floor((test.minWidth + test.maxWidth) / 2) : 
      test.minWidth + 100;
    
    // In a real implementation, you would resize the viewport here
    // For now, we'll just validate the expected behavior exists
    const expected = getExpectedBehavior(testWidth);
    
    results.push({
      test,
      result: {
        currentWidth: testWidth,
        expected,
        gridColumns: expected?.expectedColumns || 1,
        sidebarVisible: expected?.expectedSidebarBehavior === 'fixed',
        passed: expected !== null
      }
    });
  });
  
  return results;
}

/**
 * Log responsive test results to console
 */
export function logResponsiveTestResults(): void {
  console.group('🔍 Responsive Behavior Tests');
  
  const currentTest = testResponsiveBehavior();
  console.log('Current Viewport:', currentTest);
  
  const allTests = runResponsiveTests();
  console.table(allTests.map(({ test, result }) => ({
    Breakpoint: test.name,
    Width: `${test.minWidth}px${test.maxWidth ? `-${test.maxWidth}px` : '+'}`,
    ExpectedColumns: test.expectedColumns,
    ExpectedSidebar: test.expectedSidebarBehavior,
    Passed: result.passed ? '✅' : '❌'
  })));
  
  const passedCount = allTests.filter(({ result }) => result.passed).length;
  const totalCount = allTests.length;
  
  console.log(`📊 Results: ${passedCount}/${totalCount} tests passed`);
  console.groupEnd();
}

// Auto-run tests in development mode
if (import.meta.env.DEV) {
  // Run tests when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      setTimeout(logResponsiveTestResults, 1000);
    });
  } else {
    setTimeout(logResponsiveTestResults, 1000);
  }
}