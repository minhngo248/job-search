import { useEffect, useCallback, useRef, useState } from 'react';

interface UseKeyboardNavigationProps {
  itemCount: number;
  onItemSelect?: (index: number) => void;
  onItemActivate?: (index: number) => void;
  enabled?: boolean;
  gridColumns?: number; // For grid navigation
}

export const useKeyboardNavigation = ({
  itemCount,
  onItemSelect,
  onItemActivate,
  enabled = true,
  gridColumns = 1
}: UseKeyboardNavigationProps) => {
  const [currentIndex, setCurrentIndex] = useState<number>(-1);
  const containerRef = useRef<HTMLDivElement>(null);

  const setFocusedIndex = useCallback((index: number) => {
    if (index < 0 || index >= itemCount) return;
    
    setCurrentIndex(index);
    
    // Find the item element and focus it
    if (containerRef.current) {
      const items = containerRef.current.querySelectorAll('[role="listitem"]');
      const targetItem = items[index] as HTMLElement;
      if (targetItem) {
        const focusableElement = targetItem.querySelector('[tabindex="0"]') as HTMLElement || targetItem;
        focusableElement.focus();
        
        // Scroll into view if needed
        focusableElement.scrollIntoView({
          behavior: 'smooth',
          block: 'nearest',
          inline: 'nearest'
        });
      }
    }
    
    onItemSelect?.(index);
  }, [itemCount, onItemSelect]);

  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    if (!enabled || itemCount === 0) return;

    let newIndex = currentIndex;

    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault();
        if (gridColumns === 1) {
          // Single column: move to next item
          newIndex = Math.min(currentIndex + 1, itemCount - 1);
        } else {
          // Grid: move down one row
          newIndex = Math.min(currentIndex + gridColumns, itemCount - 1);
        }
        break;

      case 'ArrowUp':
        event.preventDefault();
        if (gridColumns === 1) {
          // Single column: move to previous item
          newIndex = Math.max(currentIndex - 1, 0);
        } else {
          // Grid: move up one row
          newIndex = Math.max(currentIndex - gridColumns, 0);
        }
        break;

      case 'ArrowRight':
        if (gridColumns > 1) {
          event.preventDefault();
          // Grid: move to next column
          const currentCol = currentIndex % gridColumns;
          if (currentCol < gridColumns - 1) {
            newIndex = Math.min(currentIndex + 1, itemCount - 1);
          }
        }
        break;

      case 'ArrowLeft':
        if (gridColumns > 1) {
          event.preventDefault();
          // Grid: move to previous column
          const currentCol = currentIndex % gridColumns;
          if (currentCol > 0) {
            newIndex = Math.max(currentIndex - 1, 0);
          }
        }
        break;

      case 'Home':
        event.preventDefault();
        newIndex = 0;
        break;

      case 'End':
        event.preventDefault();
        newIndex = itemCount - 1;
        break;

      case 'Enter':
      case ' ':
        if (currentIndex >= 0) {
          event.preventDefault();
          onItemActivate?.(currentIndex);
        }
        break;

      default:
        return; // Don't handle other keys
    }

    if (newIndex !== currentIndex && newIndex >= 0 && newIndex < itemCount) {
      setFocusedIndex(newIndex);
    }
  }, [enabled, itemCount, gridColumns, currentIndex, onItemActivate, setFocusedIndex]);

  // Initialize focus on first item when items are loaded
  useEffect(() => {
    if (enabled && itemCount > 0 && currentIndex === -1) {
      // Use setTimeout to avoid synchronous setState in effect
      setTimeout(() => setFocusedIndex(0), 0);
    }
  }, [enabled, itemCount, currentIndex, setFocusedIndex]);

  // Add keyboard event listeners
  useEffect(() => {
    if (!enabled) return;

    const container = containerRef.current;
    if (container) {
      container.addEventListener('keydown', handleKeyDown);
      return () => {
        container.removeEventListener('keydown', handleKeyDown);
      };
    }
  }, [enabled, handleKeyDown]);

  // Reset focus when items change
  useEffect(() => {
    if (itemCount === 0 && currentIndex !== -1) {
      setTimeout(() => setCurrentIndex(-1), 0);
    } else if (currentIndex >= itemCount && itemCount > 0) {
      setTimeout(() => setFocusedIndex(Math.max(0, itemCount - 1)), 0);
    }
  }, [itemCount, currentIndex, setFocusedIndex]);

  return {
    containerRef,
    currentIndex,
    setFocusedIndex
  };
};