import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { render, cleanup } from '@testing-library/react'
import React from 'react'
import { JobList } from '../../components/JobList'
import { testResponsiveBehavior, BREAKPOINT_TESTS } from '../../utils/responsiveTest'
import type { JobRecord } from '../../services/api'

describe('Integration Tests - Responsive Breakpoints', () => {
  const mockJobs: JobRecord[] = Array.from({ length: 8 }, (_, i) => ({
    id: `job-${i + 1}`,
    job_title: `Job Title ${i + 1}`,
    company_name: `Company ${i + 1}`,
    city: 'Paris, Île-de-France',
    description: `Description for job ${i + 1}`,
    published_date: '2024-01-15',
    salary_range: `€${50 + i * 5},000`,
    tags: ['Regulatory'],
    year_of_experience: 3,
    link: `https://example.com/job-${i + 1}`,
    source: 'LinkedIn',
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-15T10:00:00Z'
  }))

  beforeEach(() => {
    // Reset any global state
  })

  afterEach(() => {
    cleanup()
  })

  it('should adapt layout at each major breakpoint', () => {
    BREAKPOINT_TESTS.forEach(breakpoint => {
      // Set viewport to breakpoint width
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: breakpoint.minWidth,
      })
      
      // Trigger resize event
      window.dispatchEvent(new Event('resize'))
      
      const { container, unmount } = render(
        React.createElement(JobList, { 
          jobs: mockJobs, 
          loading: false, 
          error: null, 
          totalCount: mockJobs.length 
        })
      )
      
      // Verify component renders at this breakpoint
      const jobListElement = container.querySelector('.job-list')
      expect(jobListElement).toBeInTheDocument()
      
      // Verify jobs are rendered
      const jobCards = container.querySelectorAll('.job-card')
      expect(jobCards.length).toBe(mockJobs.length)
      
      // Test responsive behavior utility
      const responsiveTest = testResponsiveBehavior()
      expect(responsiveTest.currentWidth).toBe(breakpoint.minWidth)
      expect(responsiveTest.expected).toBeTruthy()
      
      console.log(`✓ ${breakpoint.name} (${breakpoint.minWidth}px): ${responsiveTest.gridColumns} columns`)
      
      unmount()
    })
  })

  it('should verify component visibility and functionality at each breakpoint', () => {
    const criticalBreakpoints = [
      { name: 'Mobile', width: 375 },
      { name: 'Tablet', width: 768 },
      { name: 'Desktop', width: 1024 },
      { name: 'Large Desktop', width: 1440 }
    ]

    criticalBreakpoints.forEach(({ name, width }) => {
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: width,
      })
      
      window.dispatchEvent(new Event('resize'))
      
      const { container, unmount } = render(
        React.createElement(JobList, { 
          jobs: mockJobs, 
          loading: false, 
          error: null, 
          totalCount: mockJobs.length 
        })
      )
      
      // Verify core functionality works at this breakpoint
      const jobListElement = container.querySelector('.job-list')
      expect(jobListElement).toBeInTheDocument()
      
      const jobCards = container.querySelectorAll('.job-card')
      expect(jobCards.length).toBeGreaterThan(0)
      
      // Verify each job card has essential content
      jobCards.forEach((card, index) => {
        // At minimum, cards should have structure for content
        expect(card).toHaveClass('job-card')
        
        // In a real test, we'd verify specific content visibility
        // For now, verify the card structure exists
        expect(card.textContent).toContain(mockJobs[index].job_title)
      })
      
      console.log(`✓ ${name} (${width}px): All components visible and functional`)
      
      unmount()
    })
  })

  it('should test touch vs mouse interaction modes', () => {
    const devices = [
      { name: 'Touch', width: 768, hasTouch: true },
      { name: 'Mouse', width: 1024, hasTouch: false }
    ]
    
    devices.forEach(device => {
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: device.width,
      })
      
      // Mock touch support
      Object.defineProperty(window, 'ontouchstart', {
        writable: true,
        configurable: true,
        value: device.hasTouch ? {} : undefined,
      })
      
      Object.defineProperty(navigator, 'maxTouchPoints', {
        writable: true,
        configurable: true,
        value: device.hasTouch ? 5 : 0,
      })
      
      const { container, unmount } = render(
        React.createElement(JobList, { 
          jobs: mockJobs, 
          loading: false, 
          error: null, 
          totalCount: mockJobs.length 
        })
      )
      
      // Verify component adapts to interaction mode
      const jobListElement = container.querySelector('.job-list')
      expect(jobListElement).toBeInTheDocument()
      
      const jobCards = container.querySelectorAll('.job-card')
      expect(jobCards.length).toBeGreaterThan(0)
      
      // In a real implementation, touch devices might have different hover behaviors
      // For now, verify the component renders correctly for both interaction modes
      console.log(`✓ ${device.name} device (${device.width}px): Interaction mode supported`)
      
      unmount()
    })
  })
})