/**
 * Utility functions for testing touch interactions
 */

export interface TouchTestResult {
  hasTouchSupport: boolean;
  isCoarsePointer: boolean;
  prefersReducedMotion: boolean;
  prefersHighContrast: boolean;
  touchFriendlyElements: number;
  accessibilityScore: number;
}

/**
 * Test touch and accessibility features
 */
export function runTouchAndAccessibilityTests(): TouchTestResult {
  // Test touch support
  const hasTouchSupport = 'ontouchstart' in window || 
    navigator.maxTouchPoints > 0 || 
    ((navigator as { msMaxTouchPoints?: number }).msMaxTouchPoints || 0) > 0;
  
  // Test pointer type
  const isCoarsePointer = window.matchMedia('(pointer: coarse)').matches;
  
  // Test user preferences
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const prefersHighContrast = window.matchMedia('(prefers-contrast: high)').matches;
  
  // Count touch-friendly elements (min 44px touch targets)
  const interactiveElements = document.querySelectorAll(
    'button, a, input, select, [role="button"], [tabindex="0"]'
  );
  
  let touchFriendlyElements = 0;
  interactiveElements.forEach(element => {
    const rect = element.getBoundingClientRect();
    const styles = getComputedStyle(element as Element);
    const minHeight = parseInt(styles.minHeight, 10) || rect.height;
    const minWidth = parseInt(styles.minWidth, 10) || rect.width;
    
    if (minHeight >= 44 && minWidth >= 44) {
      touchFriendlyElements++;
    }
  });
  
  // Calculate accessibility score (0-100)
  const totalInteractiveElements = interactiveElements.length;
  const touchFriendlyRatio = totalInteractiveElements > 0 ? 
    touchFriendlyElements / totalInteractiveElements : 1;
  
  // Check for ARIA labels and other accessibility features
  const elementsWithAriaLabels = document.querySelectorAll('[aria-label], [aria-labelledby]').length;
  const ariaRatio = totalInteractiveElements > 0 ? 
    elementsWithAriaLabels / totalInteractiveElements : 1;
  
  const accessibilityScore = Math.round((touchFriendlyRatio * 50) + (ariaRatio * 50));
  
  return {
    hasTouchSupport,
    isCoarsePointer,
    prefersReducedMotion,
    prefersHighContrast,
    touchFriendlyElements,
    accessibilityScore
  };
}

/**
 * Test keyboard navigation functionality
 */
export function testKeyboardNavigation(): {
  focusableElements: number;
  tabIndexElements: number;
  keyboardNavigationSupported: boolean;
} {
  const focusableElements = document.querySelectorAll(
    'a, button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
  ).length;
  
  const tabIndexElements = document.querySelectorAll('[tabindex="0"]').length;
  
  // Test if keyboard navigation is implemented
  const jobListElement = document.querySelector('.job-list.keyboard-navigation');
  const keyboardNavigationSupported = jobListElement !== null;
  
  return {
    focusableElements,
    tabIndexElements,
    keyboardNavigationSupported
  };
}

/**
 * Log touch and accessibility test results
 */
export function logTouchAndAccessibilityResults(): void {
  console.group('👆 Touch & Accessibility Tests');
  
  const touchResults = runTouchAndAccessibilityTests();
  const keyboardResults = testKeyboardNavigation();
  
  console.log('Touch Support:', touchResults.hasTouchSupport ? '✅' : '❌');
  console.log('Coarse Pointer:', touchResults.isCoarsePointer ? '✅' : '❌');
  console.log('Reduced Motion:', touchResults.prefersReducedMotion ? '✅ (Respected)' : 'ℹ️ (Not requested)');
  console.log('High Contrast:', touchResults.prefersHighContrast ? '✅ (Respected)' : 'ℹ️ (Not requested)');
  console.log(`Touch-Friendly Elements: ${touchResults.touchFriendlyElements} (44px+ targets)`);
  console.log(`Accessibility Score: ${touchResults.accessibilityScore}/100`);
  console.log(`Focusable Elements: ${keyboardResults.focusableElements}`);
  console.log(`Keyboard Navigation: ${keyboardResults.keyboardNavigationSupported ? '✅' : '❌'}`);
  
  // Overall assessment
  const overallScore = (
    (touchResults.hasTouchSupport ? 20 : 0) +
    (touchResults.accessibilityScore * 0.6) +
    (keyboardResults.keyboardNavigationSupported ? 20 : 0)
  );
  
  console.log(`📊 Overall Touch/Accessibility Score: ${Math.round(overallScore)}/100`);
  console.groupEnd();
}

// Auto-run tests in development mode
if (import.meta.env.DEV) {
  // Run tests when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      setTimeout(logTouchAndAccessibilityResults, 1500);
    });
  } else {
    setTimeout(logTouchAndAccessibilityResults, 1500);
  }
}