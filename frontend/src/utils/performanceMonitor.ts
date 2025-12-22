/**
 * Performance monitoring utilities for the job application
 */

export interface PerformanceMetrics {
  renderTime: number;
  memoryUsage: number;
  jobCount: number;
  scrollPerformance: number;
  interactionLatency: number;
}

/**
 * Monitor rendering performance
 */
export function measureRenderPerformance(): Promise<number> {
  return new Promise((resolve) => {
    const startTime = performance.now();
    
    // Use requestAnimationFrame to measure actual render time
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        const endTime = performance.now();
        resolve(endTime - startTime);
      });
    });
  });
}

/**
 * Get memory usage information
 */
export function getMemoryUsage(): number {
  if ('memory' in performance) {
    const memory = (performance as { memory: { usedJSHeapSize: number } }).memory;
    return memory.usedJSHeapSize / 1024 / 1024; // Convert to MB
  }
  return 0;
}

/**
 * Monitor scroll performance
 */
export function measureScrollPerformance(): Promise<number> {
  return new Promise((resolve) => {
    const jobList = document.querySelector('.job-list');
    if (!jobList) {
      resolve(0);
      return;
    }

    let frameCount = 0;
    const startTime = performance.now();
    
    const measureFrame = () => {
      frameCount++;
      if (frameCount < 60) { // Measure for ~1 second at 60fps
        requestAnimationFrame(measureFrame);
      } else {
        const endTime = performance.now();
        const fps = (frameCount * 1000) / (endTime - startTime);
        resolve(fps);
      }
    };

    // Trigger a scroll to measure performance
    jobList.scrollTop += 100;
    requestAnimationFrame(measureFrame);
  });
}

/**
 * Measure interaction latency
 */
export function measureInteractionLatency(): Promise<number> {
  return new Promise((resolve) => {
    const button = document.querySelector('.job-card') as HTMLElement;
    if (!button) {
      resolve(0);
      return;
    }

    const startTime = performance.now();
    
    const handleClick = () => {
      const endTime = performance.now();
      button.removeEventListener('click', handleClick);
      resolve(endTime - startTime);
    };

    button.addEventListener('click', handleClick);
    
    // Simulate click
    setTimeout(() => {
      button.click();
    }, 10);
  });
}

/**
 * Run comprehensive performance tests
 */
export async function runPerformanceTests(): Promise<PerformanceMetrics> {
  const jobCount = document.querySelectorAll('.job-card').length;
  
  const [renderTime, scrollPerformance, interactionLatency] = await Promise.all([
    measureRenderPerformance(),
    measureScrollPerformance(),
    measureInteractionLatency()
  ]);

  return {
    renderTime,
    memoryUsage: getMemoryUsage(),
    jobCount,
    scrollPerformance,
    interactionLatency
  };
}

/**
 * Log performance test results
 */
export async function logPerformanceResults(): Promise<void> {
  console.group('⚡ Performance Tests');
  
  try {
    const metrics = await runPerformanceTests();
    
    console.log(`📊 Job Cards Rendered: ${metrics.jobCount}`);
    console.log(`🎨 Render Time: ${metrics.renderTime.toFixed(2)}ms`);
    console.log(`🧠 Memory Usage: ${metrics.memoryUsage.toFixed(2)}MB`);
    console.log(`📜 Scroll FPS: ${metrics.scrollPerformance.toFixed(1)}`);
    console.log(`👆 Interaction Latency: ${metrics.interactionLatency.toFixed(2)}ms`);
    
    // Performance assessment
    const renderScore = metrics.renderTime < 16 ? 100 : Math.max(0, 100 - (metrics.renderTime - 16) * 2);
    const scrollScore = metrics.scrollPerformance > 55 ? 100 : (metrics.scrollPerformance / 55) * 100;
    const interactionScore = metrics.interactionLatency < 100 ? 100 : Math.max(0, 100 - (metrics.interactionLatency - 100));
    
    const overallScore = (renderScore + scrollScore + interactionScore) / 3;
    
    console.log(`📈 Performance Score: ${Math.round(overallScore)}/100`);
    
    // Recommendations
    if (overallScore < 80) {
      console.warn('⚠️ Performance recommendations:');
      if (renderScore < 80) console.warn('  - Consider reducing DOM complexity');
      if (scrollScore < 80) console.warn('  - Enable virtual scrolling for large lists');
      if (interactionScore < 80) console.warn('  - Optimize event handlers');
    } else {
      console.log('✅ Performance is good!');
    }
    
  } catch (error) {
    console.error('❌ Performance test failed:', error);
  }
  
  console.groupEnd();
}

/**
 * Monitor performance continuously in development
 */
export function startPerformanceMonitoring(): void {
  if (!import.meta.env.DEV) return;

  // Run initial performance test
  setTimeout(logPerformanceResults, 2000);

  // Monitor performance on window resize (responsive behavior)
  let resizeTimeout: number;
  window.addEventListener('resize', () => {
    clearTimeout(resizeTimeout);
    resizeTimeout = window.setTimeout(() => {
      console.log('🔄 Responsive layout change detected, measuring performance...');
      logPerformanceResults();
    }, 500);
  });

  // Monitor performance when new jobs are loaded
  const observer = new MutationObserver((mutations) => {
    const jobCardsAdded = mutations.some(mutation => 
      Array.from(mutation.addedNodes).some(node => 
        node instanceof Element && node.classList.contains('job-card')
      )
    );

    if (jobCardsAdded) {
      console.log('📝 New job cards loaded, measuring performance...');
      setTimeout(logPerformanceResults, 100);
    }
  });

  const jobList = document.querySelector('.job-list');
  if (jobList) {
    observer.observe(jobList, { childList: true, subtree: true });
  }
}

// Auto-start performance monitoring in development
if (import.meta.env.DEV) {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', startPerformanceMonitoring);
  } else {
    startPerformanceMonitoring();
  }
}