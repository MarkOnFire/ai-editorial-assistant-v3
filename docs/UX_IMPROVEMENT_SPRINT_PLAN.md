# UX Improvement Sprint Plan
## PBS Wisconsin Editorial Assistant Web Dashboard

**Generated:** 2025-12-30
**Assessment Score:** 5.4/10 (Composite)
**Target Score:** 8.0/10

---

## Executive Summary

Five parallel UX assessments identified 47 discrete issues across accessibility, cognitive load, navigation, neurodivergent-friendliness, and interactive feedback. This document organizes these into actionable sprints for agent assignment.

### Assessment Scores

| Area | Current | Target | Gap |
|------|---------|--------|-----|
| Visual Hierarchy & Cognitive Load | 6.6/10 | 8.0/10 | 1.4 |
| WCAG Accessibility Compliance | 52% | 85% | 33% |
| Navigation & Information Architecture | 6.2/10 | 8.0/10 | 1.8 |
| Neurodivergent-Friendly Patterns | 5.4/10 | 8.0/10 | 2.6 |
| Interactive Elements & Feedback | 4.9/10 | 8.0/10 | 3.1 |

---

## Agent Assignment Guidelines

| Agent Type | Best For | Complexity |
|------------|----------|------------|
| `the-drone` | Implementation tasks, component creation, file modifications | Medium |
| `cli-agent/gemini` | Boilerplate generation, utility functions, CSS additions | Low |
| `orchestrator` | Multi-file refactors, architectural changes | High |
| `adhd-friendly-ui-designer` | Design review, validation of completed work | Review |

---

## Sprint 1: Critical Accessibility Foundation

**Priority:** CRITICAL
**Estimated Tasks:** 8
**Dependencies:** None (foundational)
**Blocks:** All subsequent sprints

### Task 1.1: Add Skip Navigation Link

**Agent:** `the-drone`
**Complexity:** Low
**File:** `web/src/components/Layout.tsx`

**Description:**
Add a skip link as the first focusable element to allow keyboard users to bypass navigation.

**Acceptance Criteria:**
- [ ] Skip link is visually hidden by default
- [ ] Skip link becomes visible on focus
- [ ] Clicking/activating navigates to `#main-content`
- [ ] Main content area has `id="main-content"` and `tabindex="-1"`

**Implementation:**
```tsx
// Add as first child of Layout's return
<a
  href="#main-content"
  className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-blue-600 focus:text-white focus:rounded-md transition-all"
>
  Skip to main content
</a>

// Update main element
<main id="main-content" tabIndex={-1} className="...">
```

---

### Task 1.2: Add Focus-Visible States Globally

**Agent:** `cli-agent/gemini`
**Complexity:** Low
**File:** `web/src/index.css`

**Description:**
Add global focus-visible styles that work with Tailwind's dark theme.

**Acceptance Criteria:**
- [ ] All interactive elements show visible focus ring on keyboard navigation
- [ ] Focus ring uses blue-500 color with offset for dark backgrounds
- [ ] Mouse clicks do not trigger focus ring (focus-visible, not focus)

**Implementation:**
```css
/* Add to index.css after @tailwind utilities */

/* Screen reader only utility */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}

.sr-only.focus\:not-sr-only:focus {
  position: absolute;
  width: auto;
  height: auto;
  padding: 0;
  margin: 0;
  overflow: visible;
  clip: auto;
  white-space: normal;
}

/* Global focus-visible for accessibility */
button:focus-visible,
a:focus-visible,
input:focus-visible,
select:focus-visible,
[role="button"]:focus-visible,
[tabindex]:focus-visible {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
}

/* Remove default focus outline since we're using focus-visible */
button:focus,
a:focus,
input:focus,
select:focus {
  outline: none;
}
```

---

### Task 1.3: Fix Color Contrast Violations

**Agent:** `the-drone`
**Complexity:** Medium
**Files:** Multiple (see list below)

**Description:**
Replace all instances of low-contrast text colors with accessible alternatives.

**Color Mapping:**
| Current Class | Replacement | Contrast Ratio |
|---------------|-------------|----------------|
| `text-gray-600` | `text-gray-400` | ~4.5:1 |
| `text-gray-500` | `text-gray-300` | ~6.0:1 |
| `text-gray-400` | `text-gray-300` | ~6.0:1 (for important text) |

**Files to Modify:**
- `web/src/components/Layout.tsx:25` - Version text
- `web/src/components/StatusBar.tsx:73, 150` - Arrow and timestamp
- `web/src/pages/Home.tsx:160` - StatCard labels
- `web/src/pages/Projects.tsx:239` - Section headers
- `web/src/pages/Queue.tsx:272-278` - Table cells
- `web/src/pages/Settings.tsx:294-297` - Descriptions

**Acceptance Criteria:**
- [ ] No text below 4.5:1 contrast ratio against its background
- [ ] Visual hierarchy maintained (gray-300 vs gray-400 for emphasis)
- [ ] Test with WebAIM Contrast Checker

---

### Task 1.4: Add Labels to Form Inputs

**Agent:** `the-drone`
**Complexity:** Low
**Files:** `Projects.tsx`, `Queue.tsx`, `Settings.tsx`

**Description:**
Add accessible labels to all form inputs. Labels can be visually hidden with `sr-only` class if design requires.

**Locations:**
| File | Line | Element | Label Text |
|------|------|---------|------------|
| `Projects.tsx` | 202-207 | Search input | "Search projects by filename" |
| `Queue.tsx` | 181-186 | Search input | "Search jobs by filename" |
| `Settings.tsx` | 317-327 | Select dropdowns | "[Agent name] tier selection" |
| `Settings.tsx` | 374-382 | Range inputs | "Duration threshold" / "Failure threshold" |

**Implementation Pattern:**
```tsx
<div className="relative">
  <label htmlFor="search-projects" className="sr-only">
    Search projects by filename
  </label>
  <input
    id="search-projects"
    type="text"
    aria-describedby="search-projects-hint"
    // ... existing props
  />
  <span id="search-projects-hint" className="sr-only">
    Type to filter projects, press Enter to search
  </span>
</div>
```

**Acceptance Criteria:**
- [ ] Every input has an associated `<label>` with matching `htmlFor`/`id`
- [ ] Screen reader announces input purpose
- [ ] Optional: Add `aria-describedby` for additional context

---

### Task 1.5: Add ARIA to Navigation

**Agent:** `cli-agent/gemini`
**Complexity:** Low
**File:** `web/src/components/Layout.tsx`

**Description:**
Add proper ARIA attributes to navigation landmarks.

**Implementation:**
```tsx
// Line 18 - Add aria-label to nav
<nav className="bg-gray-800 border-b border-gray-700" aria-label="Main navigation">

// Line 27-40 - Add role="list" and aria-current
<div className="flex space-x-1" role="list">
  <NavLink
    to="/"
    className={navLinkClass}
    aria-current={({ isActive }) => isActive ? 'page' : undefined}
  >
    Dashboard
  </NavLink>
  // ... repeat for other links
</div>
```

**Acceptance Criteria:**
- [ ] Navigation has `aria-label="Main navigation"`
- [ ] Active link has `aria-current="page"`
- [ ] Screen reader announces "Main navigation, list, 4 items"

---

### Task 1.6: Fix Modal Accessibility

**Agent:** `the-drone`
**Complexity:** Medium
**Files:** `Projects.tsx:396-425`, `JobDetail.tsx:402-431`

**Description:**
Make modals fully accessible with focus trap, escape key, and proper ARIA.

**Requirements:**
1. Add `role="dialog"` and `aria-modal="true"`
2. Add `aria-labelledby` pointing to modal title
3. Trap focus inside modal when open
4. Close modal on Escape key press
5. Return focus to trigger element on close

**Implementation:**
```tsx
// Create a custom hook: web/src/hooks/useFocusTrap.ts
import { useEffect, useRef } from 'react';

export function useFocusTrap(isOpen: boolean) {
  const containerRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!isOpen) return;

    // Store the element that triggered the modal
    triggerRef.current = document.activeElement as HTMLElement;

    const container = containerRef.current;
    if (!container) return;

    // Find all focusable elements
    const focusableSelector = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';
    const focusableElements = container.querySelectorAll(focusableSelector);
    const firstElement = focusableElements[0] as HTMLElement;
    const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

    // Focus first element
    firstElement?.focus();

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        // Will be handled by parent component
        return;
      }

      if (e.key === 'Tab') {
        if (e.shiftKey && document.activeElement === firstElement) {
          e.preventDefault();
          lastElement?.focus();
        } else if (!e.shiftKey && document.activeElement === lastElement) {
          e.preventDefault();
          firstElement?.focus();
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      // Return focus to trigger
      triggerRef.current?.focus();
    };
  }, [isOpen]);

  return containerRef;
}

// Usage in Projects.tsx modal:
const modalRef = useFocusTrap(!!viewingArtifact);

useEffect(() => {
  const handleEscape = (e: KeyboardEvent) => {
    if (e.key === 'Escape' && viewingArtifact) {
      setViewingArtifact(null);
    }
  };
  document.addEventListener('keydown', handleEscape);
  return () => document.removeEventListener('keydown', handleEscape);
}, [viewingArtifact]);

// In JSX:
<div
  ref={modalRef}
  role="dialog"
  aria-modal="true"
  aria-labelledby="artifact-modal-title"
  className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4"
>
  <div className="bg-gray-900 rounded-lg ...">
    <h3 id="artifact-modal-title" className="text-lg font-medium">
      {viewingArtifact.name}
    </h3>
    // ...
  </div>
</div>
```

**Acceptance Criteria:**
- [ ] Modal has `role="dialog"` and `aria-modal="true"`
- [ ] Focus moves to modal when opened
- [ ] Tab key cycles through modal elements only
- [ ] Escape key closes modal
- [ ] Focus returns to trigger button on close
- [ ] Background content is inert (cannot be tabbed to)

---

### Task 1.7: Add Reduced Motion Support

**Agent:** `cli-agent/gemini`
**Complexity:** Low
**File:** `web/src/index.css`

**Description:**
Respect user's motion preferences by disabling animations when `prefers-reduced-motion: reduce` is set.

**Implementation:**
```css
/* Add to index.css */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

**Acceptance Criteria:**
- [ ] Set `prefers-reduced-motion: reduce` in OS/browser
- [ ] Verify `animate-pulse` elements are static
- [ ] Verify transitions are instant
- [ ] No jerky/broken animations (use 0.01ms not 0)

---

### Task 1.8: Add Error Announcements

**Agent:** `the-drone`
**Complexity:** Low
**Files:** `Settings.tsx`, `JobDetail.tsx`, `System.tsx`

**Description:**
Add `role="alert"` to error messages so screen readers announce them immediately.

**Locations:**
| File | Lines | Current | Fix |
|------|-------|---------|-----|
| `Settings.tsx` | 280-283 | `<div className="bg-red-900/20...">` | Add `role="alert" aria-live="assertive"` |
| `JobDetail.tsx` | 349-356 | Error display | Add `role="alert"` |
| `System.tsx` | 128-159 | Offline state | Add `role="alert"` |

**Acceptance Criteria:**
- [ ] Screen reader announces error messages immediately when they appear
- [ ] Success messages use `role="status"` (polite announcement)

---

## Sprint 2: Interactive Feedback System

**Priority:** HIGH
**Estimated Tasks:** 7
**Dependencies:** Sprint 1 (focus states needed)
**Blocks:** Sprint 4

### Task 2.1: Create Toast Notification Component

**Agent:** `the-drone`
**Complexity:** Medium
**File:** `web/src/components/ui/Toast.tsx` (new file)

**Description:**
Create a toast notification system for action feedback (success, error, info).

**Requirements:**
- Toast appears in bottom-right corner
- Multiple toasts stack vertically
- Auto-dismiss after 5 seconds (configurable)
- Manual dismiss with X button
- Accessible with `role="status"` and `aria-live="polite"`

**Implementation:**
```tsx
// web/src/components/ui/Toast.tsx
import { createContext, useContext, useState, useCallback, ReactNode } from 'react';

interface Toast {
  id: string;
  type: 'success' | 'error' | 'info';
  message: string;
  duration?: number;
}

interface ToastContextValue {
  addToast: (type: Toast['type'], message: string, duration?: number) => void;
  removeToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) throw new Error('useToast must be used within ToastProvider');
  return context;
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback((type: Toast['type'], message: string, duration = 5000) => {
    const id = crypto.randomUUID();
    setToasts(prev => [...prev, { id, type, message, duration }]);

    if (duration > 0) {
      setTimeout(() => {
        setToasts(prev => prev.filter(t => t.id !== id));
      }, duration);
    }
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ addToast, removeToast }}>
      {children}
      <div
        className="fixed bottom-4 right-4 space-y-2 z-50"
        role="region"
        aria-label="Notifications"
      >
        {toasts.map(toast => (
          <div
            key={toast.id}
            role="status"
            aria-live="polite"
            className={`
              px-4 py-3 rounded-lg shadow-lg flex items-center gap-3 min-w-[300px]
              animate-slide-in-right
              ${toast.type === 'success' ? 'bg-green-900 border border-green-500/30' : ''}
              ${toast.type === 'error' ? 'bg-red-900 border border-red-500/30' : ''}
              ${toast.type === 'info' ? 'bg-blue-900 border border-blue-500/30' : ''}
            `}
          >
            <span className="flex-1 text-white">{toast.message}</span>
            <button
              onClick={() => removeToast(toast.id)}
              className="text-gray-400 hover:text-white"
              aria-label="Dismiss notification"
            >
              <span aria-hidden="true">×</span>
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

// Add to tailwind.config.js:
// keyframes: {
//   'slide-in-right': {
//     '0%': { transform: 'translateX(100%)', opacity: '0' },
//     '100%': { transform: 'translateX(0)', opacity: '1' },
//   },
// },
// animation: {
//   'slide-in-right': 'slide-in-right 0.3s ease-out',
// },
```

**Integration:**
```tsx
// In App.tsx, wrap with ToastProvider
import { ToastProvider } from './components/ui/Toast';

function App() {
  return (
    <ToastProvider>
      <RouterProvider router={router} />
    </ToastProvider>
  );
}
```

**Acceptance Criteria:**
- [ ] `useToast()` hook available throughout app
- [ ] Toasts appear with slide-in animation
- [ ] Toasts auto-dismiss after configured duration
- [ ] Manual dismiss works
- [ ] Screen reader announces toast content
- [ ] Multiple toasts stack without overlap

---

### Task 2.2: Create Confirm Dialog Component

**Agent:** `the-drone`
**Complexity:** Medium
**File:** `web/src/components/ui/ConfirmDialog.tsx` (new file)

**Description:**
Replace native `confirm()` with styled, accessible dialog component.

**Implementation:**
```tsx
// web/src/components/ui/ConfirmDialog.tsx
import { useEffect, useRef } from 'react';

interface ConfirmDialogProps {
  isOpen: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: 'danger' | 'default';
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmDialog({
  isOpen,
  title,
  message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  variant = 'default',
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  const cancelRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (isOpen) {
      cancelRef.current?.focus();

      const handleEscape = (e: KeyboardEvent) => {
        if (e.key === 'Escape') onCancel();
      };
      document.addEventListener('keydown', handleEscape);
      return () => document.removeEventListener('keydown', handleEscape);
    }
  }, [isOpen, onCancel]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4"
      role="alertdialog"
      aria-modal="true"
      aria-labelledby="confirm-dialog-title"
      aria-describedby="confirm-dialog-message"
    >
      <div className="bg-gray-900 rounded-lg border border-gray-700 p-6 max-w-md w-full shadow-xl">
        <h2
          id="confirm-dialog-title"
          className="text-lg font-semibold text-white mb-2"
        >
          {title}
        </h2>
        <p
          id="confirm-dialog-message"
          className="text-gray-400 mb-6"
        >
          {message}
        </p>
        <div className="flex justify-end gap-3">
          <button
            ref={cancelRef}
            onClick={onCancel}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-md transition-colors"
          >
            {cancelLabel}
          </button>
          <button
            onClick={onConfirm}
            className={`px-4 py-2 rounded-md text-white transition-colors ${
              variant === 'danger'
                ? 'bg-red-600 hover:bg-red-500'
                : 'bg-blue-600 hover:bg-blue-500'
            }`}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
```

**Acceptance Criteria:**
- [ ] Dialog is centered on screen with backdrop
- [ ] Focus moves to Cancel button by default (safer option)
- [ ] Escape key closes dialog (triggers cancel)
- [ ] Clicking backdrop does NOT close (intentional - force decision)
- [ ] Screen reader announces as alertdialog

---

### Task 2.3: Replace Native Dialogs in Queue.tsx

**Agent:** `the-drone`
**Complexity:** Low
**File:** `web/src/pages/Queue.tsx`

**Description:**
Replace `confirm()` and `alert()` calls with ConfirmDialog and Toast components.

**Locations to Update:**
| Line | Current | Replace With |
|------|---------|--------------|
| 51 | `if (confirm(...))` | `ConfirmDialog` state |
| 63 | `if (confirm(...))` | `ConfirmDialog` state |
| 73 | `alert(...)` | `addToast('success', ...)` |

**Implementation Pattern:**
```tsx
// Add state for confirm dialog
const [confirmDialog, setConfirmDialog] = useState<{
  isOpen: boolean;
  title: string;
  message: string;
  onConfirm: () => void;
} | null>(null);

// Replace confirm() in handleCancel
const handleCancel = async (jobId: number) => {
  setConfirmDialog({
    isOpen: true,
    title: 'Cancel Job',
    message: 'Are you sure you want to cancel this job? This action cannot be undone.',
    onConfirm: async () => {
      try {
        await fetch(`/api/jobs/${jobId}/cancel`, { method: 'POST' });
        addToast('success', 'Job cancelled successfully');
        fetchJobs();
      } catch (err) {
        addToast('error', 'Failed to cancel job');
      }
      setConfirmDialog(null);
    },
  });
};

// In JSX, add ConfirmDialog
{confirmDialog && (
  <ConfirmDialog
    isOpen={confirmDialog.isOpen}
    title={confirmDialog.title}
    message={confirmDialog.message}
    confirmLabel="Cancel Job"
    variant="danger"
    onConfirm={confirmDialog.onConfirm}
    onCancel={() => setConfirmDialog(null)}
  />
)}
```

**Acceptance Criteria:**
- [ ] No native `confirm()` or `alert()` calls remain
- [ ] All destructive actions show styled confirmation dialog
- [ ] Success/error feedback uses toast notifications
- [ ] Dialog matches application design language

---

### Task 2.4: Create Loading Spinner Component

**Agent:** `cli-agent/gemini`
**Complexity:** Low
**File:** `web/src/components/ui/LoadingSpinner.tsx` (new file)

**Description:**
Create a reusable loading spinner to replace "Loading..." text.

**Implementation:**
```tsx
// web/src/components/ui/LoadingSpinner.tsx
interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function LoadingSpinner({ size = 'md', className = '' }: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
  };

  return (
    <svg
      className={`animate-spin ${sizeClasses[size]} text-blue-500 ${className}`}
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      aria-label="Loading"
      role="status"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
  );
}

// Full-page loading state
export function LoadingPage({ message = 'Loading...' }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-12">
      <LoadingSpinner size="lg" />
      <p className="mt-4 text-gray-400">{message}</p>
    </div>
  );
}
```

**Acceptance Criteria:**
- [ ] Three sizes available (sm, md, lg)
- [ ] Proper `role="status"` and `aria-label`
- [ ] Respects `prefers-reduced-motion` (via Sprint 1.7)
- [ ] LoadingPage variant for full-page states

---

### Task 2.5: Create Skeleton Loader Components

**Agent:** `the-drone`
**Complexity:** Medium
**File:** `web/src/components/ui/Skeleton.tsx` (new file)

**Description:**
Create skeleton loaders to prevent layout shift during data loading.

**Implementation:**
```tsx
// web/src/components/ui/Skeleton.tsx

// Base skeleton element
export function Skeleton({ className = '' }: { className?: string }) {
  return (
    <div
      className={`animate-pulse bg-gray-700 rounded ${className}`}
      aria-hidden="true"
    />
  );
}

// Skeleton for stat cards (Home.tsx)
export function StatCardSkeleton() {
  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
      <Skeleton className="h-4 w-20 mb-2" />
      <Skeleton className="h-8 w-12" />
    </div>
  );
}

// Skeleton for job list items
export function JobCardSkeleton() {
  return (
    <div className="p-4 bg-gray-800 rounded-lg border border-gray-700">
      <div className="flex justify-between items-start mb-2">
        <Skeleton className="h-5 w-48" />
        <Skeleton className="h-5 w-20 rounded-full" />
      </div>
      <Skeleton className="h-4 w-32" />
    </div>
  );
}

// Skeleton for table rows (Queue.tsx)
export function TableRowSkeleton({ columns = 7 }: { columns?: number }) {
  return (
    <tr className="border-b border-gray-700">
      {Array.from({ length: columns }).map((_, i) => (
        <td key={i} className="px-4 py-3">
          <Skeleton className="h-4 w-full" />
        </td>
      ))}
    </tr>
  );
}

// Skeleton for project cards
export function ProjectCardSkeleton() {
  return (
    <div className="p-3 bg-gray-900 rounded border border-gray-700">
      <Skeleton className="h-5 w-3/4 mb-2" />
      <div className="flex gap-2">
        <Skeleton className="h-4 w-16" />
        <Skeleton className="h-4 w-16" />
      </div>
    </div>
  );
}
```

**Acceptance Criteria:**
- [ ] Skeletons match dimensions of actual content
- [ ] Pulse animation respects reduced-motion preference
- [ ] `aria-hidden="true"` on all skeleton elements
- [ ] No layout shift when real content loads

---

### Task 2.6: Replace Loading Text with Skeletons

**Agent:** `the-drone`
**Complexity:** Low
**Files:** `Home.tsx`, `Queue.tsx`, `Projects.tsx`, `JobDetail.tsx`

**Description:**
Replace "Loading..." text with appropriate skeleton components.

**File-specific Changes:**

**Home.tsx (lines 68-74):**
```tsx
if (loading) {
  return (
    <div className="space-y-6">
      <Skeleton className="h-8 w-48" /> {/* Title */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCardSkeleton />
        <StatCardSkeleton />
        <StatCardSkeleton />
        <StatCardSkeleton />
      </div>
      <div className="space-y-3">
        <JobCardSkeleton />
        <JobCardSkeleton />
        <JobCardSkeleton />
      </div>
    </div>
  );
}
```

**Queue.tsx (lines 227-228):**
```tsx
{loading ? (
  <tbody>
    <TableRowSkeleton />
    <TableRowSkeleton />
    <TableRowSkeleton />
    <TableRowSkeleton />
    <TableRowSkeleton />
  </tbody>
) : (
  // existing tbody
)}
```

**Acceptance Criteria:**
- [ ] All "Loading..." text replaced with skeletons
- [ ] Skeleton structure matches actual content layout
- [ ] Smooth transition from skeleton to content

---

### Task 2.7: Add Action Feedback to JobDetail

**Agent:** `the-drone`
**Complexity:** Low
**File:** `web/src/pages/JobDetail.tsx`

**Description:**
Add toast notifications for all job actions (pause, resume, retry, cancel).

**Implementation:**
```tsx
// Add useToast hook
const { addToast } = useToast();

// Update handleAction function (around line 95)
const handleAction = async (action: string) => {
  try {
    await fetch(`${API_BASE}/jobs/${id}/${action}`, { method: 'POST' });

    const actionMessages: Record<string, string> = {
      pause: 'Job paused',
      resume: 'Job resumed',
      retry: 'Job queued for retry',
      cancel: 'Job cancelled',
    };

    addToast('success', actionMessages[action] || `Action ${action} completed`);
    fetchJob();
  } catch (err) {
    console.error(`Failed to ${action} job:`, err);
    addToast('error', `Failed to ${action} job. Please try again.`);
  }
};
```

**Acceptance Criteria:**
- [ ] Success toast appears after each successful action
- [ ] Error toast appears on failure with retry suggestion
- [ ] Toast messages are action-specific and clear

---

## Sprint 3: Navigation & Wayfinding

**Priority:** HIGH
**Estimated Tasks:** 6
**Dependencies:** Sprint 1 (focus states)
**Blocks:** None

### Task 3.1: Fix Back Navigation in JobDetail

**Agent:** `the-drone`
**Complexity:** Low
**File:** `web/src/pages/JobDetail.tsx`

**Description:**
Replace hardcoded `/queue` back link with browser history navigation.

**Current (line 172-177):**
```tsx
<Link to="/queue" className="...">
  ← Back to queue
</Link>
```

**Implementation:**
```tsx
import { useNavigate } from 'react-router-dom';

// Inside component
const navigate = useNavigate();

// Replace Link with button
<button
  onClick={() => navigate(-1)}
  className="text-sm text-gray-400 hover:text-white mb-2 inline-flex items-center gap-1"
>
  <span aria-hidden="true">←</span>
  Back
</button>
```

**Acceptance Criteria:**
- [ ] Clicking back returns to previous page (Queue, Projects, or Home)
- [ ] Works correctly regardless of entry point
- [ ] Screen reader announces "Back, button"

---

### Task 3.2: Add Breadcrumb Component

**Agent:** `the-drone`
**Complexity:** Medium
**File:** `web/src/components/ui/Breadcrumb.tsx` (new file)

**Description:**
Create a breadcrumb component for multi-level navigation context.

**Implementation:**
```tsx
// web/src/components/ui/Breadcrumb.tsx
import { Link } from 'react-router-dom';

interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface BreadcrumbProps {
  items: BreadcrumbItem[];
}

export function Breadcrumb({ items }: BreadcrumbProps) {
  return (
    <nav aria-label="Breadcrumb" className="mb-4">
      <ol className="flex items-center space-x-2 text-sm">
        {items.map((item, index) => (
          <li key={index} className="flex items-center">
            {index > 0 && (
              <span className="mx-2 text-gray-600" aria-hidden="true">/</span>
            )}
            {item.href ? (
              <Link
                to={item.href}
                className="text-gray-400 hover:text-white transition-colors"
              >
                {item.label}
              </Link>
            ) : (
              <span className="text-white" aria-current="page">
                {item.label}
              </span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}

// Usage in JobDetail.tsx:
<Breadcrumb items={[
  { label: 'Dashboard', href: '/' },
  { label: 'Queue', href: '/queue' },
  { label: `Job #${job.id}` },
]} />
```

**Acceptance Criteria:**
- [ ] Breadcrumb shows full path to current page
- [ ] Last item is current page (not a link)
- [ ] `aria-label="Breadcrumb"` on nav element
- [ ] `aria-current="page"` on current item

---

### Task 3.3: Add System Page to Main Navigation

**Agent:** `the-drone`
**Complexity:** Low
**File:** `web/src/components/Layout.tsx`

**Description:**
Add System page to main navigation instead of hiding it in StatusBar.

**Implementation:**
```tsx
// Add to navigation links (around line 30-35)
<NavLink to="/system" className={navLinkClass}>
  System
</NavLink>
```

**Alternative: Add as icon in nav bar:**
```tsx
<NavLink
  to="/system"
  className={({ isActive }) => `p-2 rounded ${isActive ? 'bg-gray-700' : 'hover:bg-gray-700/50'}`}
  title="System Status"
>
  <span className="sr-only">System Status</span>
  <svg className="w-5 h-5" /* gear icon */ />
</NavLink>
```

**Acceptance Criteria:**
- [ ] System page accessible from main navigation
- [ ] Active state matches other nav items
- [ ] StatusBar can still link to System (optional shortcut)

---

### Task 3.4: Add Filter Counts to Queue Tabs

**Agent:** `the-drone`
**Complexity:** Low
**File:** `web/src/pages/Queue.tsx`

**Description:**
Show job counts on filter tabs to provide context without clicking.

**Current (lines 210-222):**
```tsx
{['all', 'pending', 'in_progress', 'completed', 'failed'].map((s) => (
  <button key={s} ...>
    {s === 'all' ? 'All' : s.replace('_', ' ')}
  </button>
))}
```

**Implementation:**
```tsx
// Calculate counts from jobs data
const statusCounts = useMemo(() => {
  const counts: Record<string, number> = { all: jobs.length };
  jobs.forEach(job => {
    counts[job.status] = (counts[job.status] || 0) + 1;
  });
  return counts;
}, [jobs]);

// Update tab rendering
{['all', 'pending', 'in_progress', 'completed', 'failed'].map((s) => (
  <button key={s} ...>
    {s === 'all' ? 'All' : s.replace('_', ' ')}
    <span className="ml-1.5 px-1.5 py-0.5 text-xs rounded-full bg-gray-700">
      {statusCounts[s] || 0}
    </span>
  </button>
))}
```

**Acceptance Criteria:**
- [ ] Each tab shows count of jobs in that status
- [ ] Counts update when jobs change
- [ ] Count badge styled consistently with app

---

### Task 3.5: Implement Instant Search with Debounce

**Agent:** `the-drone`
**Complexity:** Medium
**Files:** `web/src/pages/Queue.tsx`, `web/src/pages/Projects.tsx`

**Description:**
Replace form-submit search with instant search that filters as user types.

**Implementation:**
```tsx
// Create a useDebounce hook: web/src/hooks/useDebounce.ts
import { useState, useEffect } from 'react';

export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => clearTimeout(handler);
  }, [value, delay]);

  return debouncedValue;
}

// Usage in Queue.tsx:
import { useDebounce } from '../hooks/useDebounce';

// Replace search state
const [searchInput, setSearchInput] = useState('');
const debouncedSearch = useDebounce(searchInput, 300);

// Effect to trigger search
useEffect(() => {
  setSearch(debouncedSearch);
  setPage(1);
}, [debouncedSearch]);

// Remove form submission - input directly filters
<input
  type="text"
  value={searchInput}
  onChange={(e) => setSearchInput(e.target.value)}
  placeholder="Search by filename..."
  // Remove onKeyDown Enter handler
/>
// Remove Search button
```

**Acceptance Criteria:**
- [ ] Typing immediately starts filtering (after 300ms debounce)
- [ ] No submit button needed
- [ ] Clear button still works
- [ ] URL updates with search param for bookmarking

---

### Task 3.6: Add Keyboard Shortcuts

**Agent:** `the-drone`
**Complexity:** Medium
**File:** `web/src/hooks/useKeyboardShortcuts.ts` (new file)

**Description:**
Add global keyboard shortcuts for navigation and common actions.

**Implementation:**
```tsx
// web/src/hooks/useKeyboardShortcuts.ts
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export function useKeyboardShortcuts() {
  const navigate = useNavigate();

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't trigger when typing in inputs
      if (e.target instanceof HTMLInputElement ||
          e.target instanceof HTMLTextAreaElement ||
          e.target instanceof HTMLSelectElement) {
        return;
      }

      // Navigation shortcuts (g + key)
      if (e.key === 'g') {
        const handleSecondKey = (e2: KeyboardEvent) => {
          switch (e2.key) {
            case 'h': navigate('/'); break;
            case 'q': navigate('/queue'); break;
            case 'p': navigate('/projects'); break;
            case 's': navigate('/settings'); break;
            case 'y': navigate('/system'); break;
          }
          document.removeEventListener('keydown', handleSecondKey);
        };
        document.addEventListener('keydown', handleSecondKey, { once: true });
        setTimeout(() => document.removeEventListener('keydown', handleSecondKey), 1000);
      }

      // Global shortcuts
      if (e.key === '?' && !e.shiftKey) {
        // Show keyboard shortcuts help
        console.log('Show shortcuts modal');
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [navigate]);
}

// Use in App.tsx or Layout.tsx:
useKeyboardShortcuts();
```

**Shortcuts to Implement:**
| Shortcut | Action |
|----------|--------|
| `g h` | Go to Home/Dashboard |
| `g q` | Go to Queue |
| `g p` | Go to Projects |
| `g s` | Go to Settings |
| `g y` | Go to System |
| `?` | Show shortcuts help |
| `/` | Focus search input |

**Acceptance Criteria:**
- [ ] Shortcuts work from any page
- [ ] Shortcuts disabled when typing in form fields
- [ ] Help modal shows all available shortcuts

---

## Sprint 4: Cognitive Load Reduction

**Priority:** MEDIUM
**Estimated Tasks:** 5
**Dependencies:** Sprint 2 (Toast system for feedback)
**Blocks:** None

### Task 4.1: Refactor Settings Page with Tabs

**Agent:** `orchestrator`
**Complexity:** HIGH
**File:** `web/src/pages/Settings.tsx`

**Description:**
Break the 630-line Settings page into tabbed sections to reduce cognitive overload.

**Tab Structure:**
1. **Agents** - Agent Base Tiers (lines 291-344)
2. **Routing** - Duration-Based + Failure-Based (lines 346-499)
3. **Worker** - Worker Settings (lines 548-606)
4. **Accessibility** - New section (see Sprint 5)

**Implementation Approach:**
```tsx
const [activeTab, setActiveTab] = useState('agents');

const tabs = [
  { id: 'agents', label: 'Agents' },
  { id: 'routing', label: 'Routing' },
  { id: 'worker', label: 'Worker' },
  { id: 'accessibility', label: 'Accessibility' },
];

// Tab navigation
<div className="border-b border-gray-700 mb-6">
  <nav className="flex space-x-4" aria-label="Settings sections">
    {tabs.map(tab => (
      <button
        key={tab.id}
        onClick={() => setActiveTab(tab.id)}
        className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
          activeTab === tab.id
            ? 'border-blue-500 text-white'
            : 'border-transparent text-gray-400 hover:text-white'
        }`}
        aria-selected={activeTab === tab.id}
        role="tab"
      >
        {tab.label}
      </button>
    ))}
  </nav>
</div>

// Tab panels
<div role="tabpanel" aria-labelledby={`tab-${activeTab}`}>
  {activeTab === 'agents' && <AgentsSection />}
  {activeTab === 'routing' && <RoutingSection />}
  {activeTab === 'worker' && <WorkerSection />}
  {activeTab === 'accessibility' && <AccessibilitySection />}
</div>
```

**Acceptance Criteria:**
- [ ] Settings split into 4 logical tabs
- [ ] Tab state persists during session
- [ ] Only active tab content renders
- [ ] Keyboard navigation between tabs (arrow keys)
- [ ] URL updates with tab param for deep linking

---

### Task 4.2: Simplify StatusBar Information

**Agent:** `the-drone`
**Complexity:** Medium
**File:** `web/src/components/StatusBar.tsx`

**Description:**
Reduce StatusBar information density by moving details to tooltip/popover.

**Current State:**
- Connection status (dot)
- Backend name
- Preset OR Model name
- Active model
- Tokens used
- Cost
- Last updated timestamp

**Proposed Simplified State:**
- Connection status (dot + text)
- Queue count (if pending > 0)
- Everything else on hover/click

**Implementation:**
```tsx
// Simplified StatusBar
<div className="text-sm flex items-center justify-between">
  {/* Left: Connection status */}
  <div className="flex items-center gap-2">
    <div className={`w-2 h-2 rounded-full ${error ? 'bg-red-500' : 'bg-green-500'}`} />
    <span className="text-gray-300">{error ? 'Offline' : 'Connected'}</span>

    {/* Show queue count if pending */}
    {health?.queue?.pending > 0 && (
      <span className="ml-4 text-yellow-400">
        {health.queue.pending} pending
      </span>
    )}
  </div>

  {/* Right: Details dropdown */}
  <details className="relative">
    <summary className="text-gray-400 hover:text-white cursor-pointer list-none">
      <span className="flex items-center gap-1">
        System Details
        <ChevronDownIcon className="w-4 h-4" />
      </span>
    </summary>
    <div className="absolute right-0 mt-2 p-4 bg-gray-800 border border-gray-700 rounded-lg shadow-lg min-w-[300px] z-50">
      {/* Full details here */}
      <dl className="space-y-2 text-sm">
        <div className="flex justify-between">
          <dt className="text-gray-400">Backend</dt>
          <dd className="text-cyan-400 font-mono">{health?.llm?.active_backend}</dd>
        </div>
        {/* ... other details */}
      </dl>
    </div>
  </details>
</div>
```

**Acceptance Criteria:**
- [ ] Default view shows only essential info
- [ ] Full details available on click/hover
- [ ] Screen reader can access all information
- [ ] Mobile-friendly (no hover-only content)

---

### Task 4.3: Add Relative Time Display

**Agent:** `cli-agent/gemini`
**Complexity:** Low
**File:** `web/src/utils/formatTime.ts` (new file)

**Description:**
Create utility functions for human-friendly time display.

**Implementation:**
```tsx
// web/src/utils/formatTime.ts

export function formatRelativeTime(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffSecs < 60) return 'just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;

  return date.toLocaleDateString();
}

export function formatDuration(startStr: string, endStr: string): string {
  const start = new Date(startStr);
  const end = new Date(endStr);
  const diffMs = end.getTime() - start.getTime();
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);

  if (diffSecs < 60) return `${diffSecs}s`;
  if (diffMins < 60) return `${diffMins}m ${diffSecs % 60}s`;
  return `${diffHours}h ${diffMins % 60}m`;
}

export function formatTimestamp(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleString();
}
```

**Acceptance Criteria:**
- [ ] "just now" for < 60 seconds
- [ ] "Xm ago" for minutes
- [ ] "Xh ago" for hours
- [ ] "Xd ago" for days (up to 7)
- [ ] Full date for > 7 days

---

### Task 4.4: Apply Relative Times Throughout App

**Agent:** `the-drone`
**Complexity:** Low
**Files:** `Home.tsx`, `Queue.tsx`, `JobDetail.tsx`, `StatusBar.tsx`

**Description:**
Replace absolute timestamps with relative times using the utility from Task 4.3.

**Locations:**
| File | Line | Current | Change To |
|------|------|---------|-----------|
| `Home.tsx` | 133 | `toLocaleString()` | `formatRelativeTime()` |
| `Queue.tsx` | 272 | `toLocaleString()` | `formatRelativeTime()` |
| `JobDetail.tsx` | 380-395 | Absolute times | Relative + absolute on hover |
| `StatusBar.tsx` | 149-153 | `toLocaleTimeString()` | `formatRelativeTime()` |

**Pattern for showing both:**
```tsx
<time
  dateTime={job.queued_at}
  title={formatTimestamp(job.queued_at)}
>
  {formatRelativeTime(job.queued_at)}
</time>
```

**Acceptance Criteria:**
- [ ] All timestamps show relative time by default
- [ ] Hovering/focusing shows full timestamp
- [ ] Screen readers announce full timestamp

---

### Task 4.5: Add Duration to Completed Jobs

**Agent:** `the-drone`
**Complexity:** Low
**Files:** `Home.tsx`, `Queue.tsx`, `JobDetail.tsx`

**Description:**
Show processing duration for completed jobs to help with time estimation.

**Implementation in JobDetail.tsx:**
```tsx
// In timeline section (around line 380)
{job.started_at && job.completed_at && (
  <div className="flex items-center gap-2 text-sm">
    <span className="text-gray-400">Duration:</span>
    <span className="text-white font-mono">
      {formatDuration(job.started_at, job.completed_at)}
    </span>
  </div>
)}
```

**Implementation in Queue.tsx table:**
```tsx
// Add column after "Queued" column
<th scope="col" className="px-4 py-3 font-medium">Duration</th>

// In row
<td className="px-4 py-3 text-sm text-gray-400">
  {job.status === 'completed' && job.started_at && job.completed_at
    ? formatDuration(job.started_at, job.completed_at)
    : '—'
  }
</td>
```

**Acceptance Criteria:**
- [ ] Duration shown for completed jobs
- [ ] "—" or empty for non-completed jobs
- [ ] Format: "Xs", "Xm Ys", or "Xh Ym"

---

## Sprint 5: Accessibility Preferences

**Priority:** LOW
**Estimated Tasks:** 3
**Dependencies:** Sprint 1 (reduced motion CSS), Sprint 4 (Settings tabs)
**Blocks:** None

### Task 5.1: Create Preferences Context

**Agent:** `the-drone`
**Complexity:** Medium
**File:** `web/src/contexts/PreferencesContext.tsx` (new file)

**Description:**
Create a context for user preferences that persists to localStorage.

**Implementation:**
```tsx
// web/src/contexts/PreferencesContext.tsx
import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface Preferences {
  reduceMotion: boolean;
  textSize: 'normal' | 'large' | 'larger';
  highContrast: boolean;
  persistNotifications: boolean;
  simplifiedStatusBar: boolean;
}

const defaultPreferences: Preferences = {
  reduceMotion: false,
  textSize: 'normal',
  highContrast: false,
  persistNotifications: false,
  simplifiedStatusBar: false,
};

interface PreferencesContextValue {
  preferences: Preferences;
  setPreference: <K extends keyof Preferences>(key: K, value: Preferences[K]) => void;
  resetPreferences: () => void;
}

const PreferencesContext = createContext<PreferencesContextValue | null>(null);

export function usePreferences() {
  const context = useContext(PreferencesContext);
  if (!context) throw new Error('usePreferences must be used within PreferencesProvider');
  return context;
}

export function PreferencesProvider({ children }: { children: ReactNode }) {
  const [preferences, setPreferences] = useState<Preferences>(() => {
    const stored = localStorage.getItem('ux-preferences');
    return stored ? { ...defaultPreferences, ...JSON.parse(stored) } : defaultPreferences;
  });

  useEffect(() => {
    localStorage.setItem('ux-preferences', JSON.stringify(preferences));

    // Apply preferences to document
    document.documentElement.classList.toggle('reduce-motion', preferences.reduceMotion);
    document.documentElement.classList.toggle('high-contrast', preferences.highContrast);
    document.documentElement.dataset.textSize = preferences.textSize;
  }, [preferences]);

  const setPreference = <K extends keyof Preferences>(key: K, value: Preferences[K]) => {
    setPreferences(prev => ({ ...prev, [key]: value }));
  };

  const resetPreferences = () => {
    setPreferences(defaultPreferences);
  };

  return (
    <PreferencesContext.Provider value={{ preferences, setPreference, resetPreferences }}>
      {children}
    </PreferencesContext.Provider>
  );
}
```

**Acceptance Criteria:**
- [ ] Preferences persist across page reloads
- [ ] Changes apply immediately
- [ ] Reset function restores defaults

---

### Task 5.2: Add Accessibility Settings Section

**Agent:** `the-drone`
**Complexity:** Medium
**File:** `web/src/pages/Settings.tsx`

**Description:**
Add an Accessibility tab to Settings with preference controls.

**Implementation:**
```tsx
// New section in Settings.tsx
function AccessibilitySection() {
  const { preferences, setPreference } = usePreferences();

  return (
    <div className="space-y-6">
      <p className="text-gray-400">
        Customize the interface to work better for you.
      </p>

      {/* Reduce Motion */}
      <div className="flex items-center justify-between p-4 bg-gray-900 rounded-lg">
        <div>
          <div className="font-medium text-white">Reduce Motion</div>
          <div className="text-sm text-gray-400">
            Minimize animations and transitions throughout the app
          </div>
        </div>
        <ToggleSwitch
          checked={preferences.reduceMotion}
          onChange={(v) => setPreference('reduceMotion', v)}
          label="Reduce motion"
        />
      </div>

      {/* Text Size */}
      <div className="flex items-center justify-between p-4 bg-gray-900 rounded-lg">
        <div>
          <div className="font-medium text-white">Text Size</div>
          <div className="text-sm text-gray-400">
            Increase the base font size for better readability
          </div>
        </div>
        <select
          value={preferences.textSize}
          onChange={(e) => setPreference('textSize', e.target.value as Preferences['textSize'])}
          className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white"
          aria-label="Text size"
        >
          <option value="normal">Normal</option>
          <option value="large">Large (120%)</option>
          <option value="larger">Larger (140%)</option>
        </select>
      </div>

      {/* High Contrast */}
      <div className="flex items-center justify-between p-4 bg-gray-900 rounded-lg">
        <div>
          <div className="font-medium text-white">High Contrast</div>
          <div className="text-sm text-gray-400">
            Increase color contrast for better visibility
          </div>
        </div>
        <ToggleSwitch
          checked={preferences.highContrast}
          onChange={(v) => setPreference('highContrast', v)}
          label="High contrast mode"
        />
      </div>

      {/* Persist Notifications */}
      <div className="flex items-center justify-between p-4 bg-gray-900 rounded-lg">
        <div>
          <div className="font-medium text-white">Keep Notifications Visible</div>
          <div className="text-sm text-gray-400">
            Don't automatically dismiss success and info messages
          </div>
        </div>
        <ToggleSwitch
          checked={preferences.persistNotifications}
          onChange={(v) => setPreference('persistNotifications', v)}
          label="Persist notifications"
        />
      </div>

      {/* Simplified StatusBar */}
      <div className="flex items-center justify-between p-4 bg-gray-900 rounded-lg">
        <div>
          <div className="font-medium text-white">Simplified Status Bar</div>
          <div className="text-sm text-gray-400">
            Hide technical details from the status bar
          </div>
        </div>
        <ToggleSwitch
          checked={preferences.simplifiedStatusBar}
          onChange={(v) => setPreference('simplifiedStatusBar', v)}
          label="Simplified status bar"
        />
      </div>
    </div>
  );
}
```

**Acceptance Criteria:**
- [ ] All preferences have clear labels and descriptions
- [ ] Toggle switches are accessible (keyboard, screen reader)
- [ ] Changes take effect immediately
- [ ] Settings persist across sessions

---

### Task 5.3: Apply Preferences Throughout App

**Agent:** `the-drone`
**Complexity:** Medium
**Files:** Multiple

**Description:**
Wire up preferences to actual UI behavior.

**CSS for Text Size (index.css):**
```css
html[data-text-size="large"] {
  font-size: 120%;
}

html[data-text-size="larger"] {
  font-size: 140%;
}

html.reduce-motion *,
html.reduce-motion *::before,
html.reduce-motion *::after {
  animation-duration: 0.01ms !important;
  animation-iteration-count: 1 !important;
  transition-duration: 0.01ms !important;
}

html.high-contrast {
  --gray-400: #d1d5db;
  --gray-500: #e5e7eb;
}
```

**StatusBar Integration:**
```tsx
// In StatusBar.tsx
const { preferences } = usePreferences();

{preferences.simplifiedStatusBar ? (
  <SimplifiedStatusBar health={health} error={error} />
) : (
  <FullStatusBar health={health} error={error} />
)}
```

**Toast Integration:**
```tsx
// In Toast.tsx provider
const { preferences } = usePreferences();

const addToast = useCallback((type, message, duration = 5000) => {
  // Don't auto-dismiss if user prefers persistent notifications
  const actualDuration = preferences.persistNotifications ? 0 : duration;
  // ... rest of implementation
}, [preferences.persistNotifications]);
```

**Acceptance Criteria:**
- [ ] Text size preference changes actual font size
- [ ] Reduce motion preference stops all animations
- [ ] High contrast preference improves text contrast
- [ ] Persistent notifications stay until dismissed
- [ ] Simplified status bar hides technical details

---

## Summary: Sprint Overview

| Sprint | Priority | Tasks | Dependencies | Estimated Effort |
|--------|----------|-------|--------------|------------------|
| Sprint 1: Critical Accessibility | CRITICAL | 8 | None | 2-3 days |
| Sprint 2: Interactive Feedback | HIGH | 7 | Sprint 1 | 2-3 days |
| Sprint 3: Navigation & Wayfinding | HIGH | 6 | Sprint 1 | 1-2 days |
| Sprint 4: Cognitive Load Reduction | MEDIUM | 5 | Sprint 2 | 2 days |
| Sprint 5: Accessibility Preferences | LOW | 3 | Sprints 1, 4 | 1 day |

**Total Estimated Effort:** 8-11 days of agent work

---

## Success Metrics

After completing all sprints, re-run the 5 UX assessments:

| Metric | Current | Target |
|--------|---------|--------|
| Visual Hierarchy & Cognitive Load | 6.6/10 | 8.0/10 |
| WCAG Accessibility Compliance | 52% | 85%+ |
| Navigation & Information Architecture | 6.2/10 | 8.0/10 |
| Neurodivergent-Friendly Patterns | 5.4/10 | 8.0/10 |
| Interactive Elements & Feedback | 4.9/10 | 8.0/10 |
| **Composite Score** | **5.4/10** | **8.0/10** |

---

## Files Created/Modified Summary

### New Files to Create
- `web/src/components/ui/Toast.tsx`
- `web/src/components/ui/ConfirmDialog.tsx`
- `web/src/components/ui/LoadingSpinner.tsx`
- `web/src/components/ui/Skeleton.tsx`
- `web/src/components/ui/Breadcrumb.tsx`
- `web/src/hooks/useFocusTrap.ts`
- `web/src/hooks/useDebounce.ts`
- `web/src/hooks/useKeyboardShortcuts.ts`
- `web/src/utils/formatTime.ts`
- `web/src/contexts/PreferencesContext.tsx`

### Existing Files to Modify
- `web/src/index.css` - Global styles, focus states, reduced motion
- `web/src/components/Layout.tsx` - Skip link, nav ARIA, System link
- `web/src/components/StatusBar.tsx` - Simplification, contrast fixes
- `web/src/pages/Home.tsx` - Skeleton loading, relative times
- `web/src/pages/Queue.tsx` - Confirm dialog, toast, filter counts, search
- `web/src/pages/Projects.tsx` - Modal accessibility, search
- `web/src/pages/JobDetail.tsx` - Modal, back nav, breadcrumb, toasts
- `web/src/pages/Settings.tsx` - Tabs, accessibility section
- `web/src/pages/System.tsx` - Error announcements
- `web/src/App.tsx` - Providers (Toast, Preferences)
- `web/tailwind.config.js` - Animation keyframes
