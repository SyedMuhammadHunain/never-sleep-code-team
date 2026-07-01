# ui-enhancements Implementation Plan

## Overview
We are implementing UI polishes including a Theme Toggle, Toast Notifications, a bottom-centered sleek Input Box, Skeleton loaders for perceived performance, and an active node Rainbow Glow animation using Feather Icons and no emojis.

## Prerequisites
- Feather Icons zip file (`~/Downloads/feather.zip`) needs to be extracted to the project assets.

## Phase Summary
- **Phase 1**: Icons & Theme Toggle Setup
- **Phase 2**: Toast Notifications System
- **Phase 3**: Input Box Overhaul
- **Phase 4**: Skeleton Loaders
- **Phase 5**: Rainbow Border Glow Animation

---

## Phase 1: Icons & Theme Toggle Setup

### Objective
Unzip the Feather icons and implement the Theme Toggle component at the upper top right of the application layout.

### Rationale
Icons are needed across all other phases (toggle buttons, toasts). The theme affects the entire UI styling.

### Tasks
- [ ] Extract `~/Downloads/feather.zip` to `frontend/src/assets/icons`.
- [ ] Create a `ThemeService` using Angular Signals to manage `light`, `dark`, and `system` modes.
- [ ] Create `ThemeToggleComponent` with Feather icons (e.g., `sun.svg`, `moon.svg`, `monitor.svg`).
- [ ] Add the toggle component to `app-layout` header (upper top right).

### Success Criteria
- [ ] Theme toggles between light and dark modes instantly.
- [ ] Icons display correctly instead of emojis.

### Files Likely Affected
- `frontend/src/assets/icons/*`
- `frontend/src/app/services/theme.service.ts`
- `frontend/src/app/components/theme-toggle/theme-toggle.component.ts`
- `frontend/src/app/app.html`

---

## Phase 2: Toast Notifications System

### Objective
Implement a top-center Toast Notification system for Error, Success, and Warning messages.

### Rationale
Essential for providing user feedback before overhauling the input and actions.

### Tasks
- [ ] Create `ToastService` utilizing Angular Signals to manage an array of active toasts.
- [ ] Create `ToastComponent` to render the messages top-center, styled appropriately for Success, Warning, and Error (using Feather icons).
- [ ] Ensure toasts auto-dismiss after a few seconds.

### Success Criteria
- [ ] Calling `ToastService.show('message', 'success')` displays a top-center toast.
- [ ] Toast dismisses automatically and smoothly.

### Files Likely Affected
- `frontend/src/app/services/toast.service.ts`
- `frontend/src/app/components/toast/toast.component.ts`
- `frontend/src/app/app.html` (to place the toast container)

---

## Phase 3: Input Box Overhaul

### Objective
Replace the textarea with a sleek, bottom-centered input box.

### Rationale
Improves the core interaction area for the AI Prompt.

### Tasks
- [ ] Refactor `prompt.component.ts` to use a standard `<input type="text">` instead of `<textarea>`.
- [ ] Style the input container to be bottom-centered, floating above the layout.
- [ ] Bind "Enter" key to submission.

### Success Criteria
- [ ] Prompt input is fixed at the bottom center of the screen.
- [ ] Enter submits the prompt without needing a button click.

### Files Likely Affected
- `frontend/src/app/components/prompt/prompt.component.ts`
- `frontend/src/app/app.css`

---

## Phase 4: Skeleton Loaders

### Objective
Replace the generic loading spinner/text with skeleton block loaders.

### Rationale
Enhances perceived performance during workflow generation.

### Tasks
- [ ] Create a `SkeletonComponent` that displays generic pulsating blocks.
- [ ] Display the skeleton in the main content area when `isRunning()` is true.

### Success Criteria
- [ ] Skeleton blocks pulse with a CSS animation while loading.
- [ ] They disappear smoothly when content arrives.

### Files Likely Affected
- `frontend/src/app/components/skeleton/skeleton.component.ts`
- `frontend/src/app/app.html`

---

## Phase 5: Rainbow Border Glow Animation

### Objective
Add a clockwise rainbow border glow to the actively running node in the workflow graph.

### Rationale
Provides direct, beautiful visual feedback on what the agents are currently doing.

### Tasks
- [ ] Define `@keyframes` in global `styles.css` for a rotating conic gradient.
- [ ] Update `ngx-graph` node template in `graph.component.ts` to apply a wrapper class to the active node.
- [ ] Apply the glowing border mask/background specifically to that class.

### Success Criteria
- [ ] The currently active agent node has a smoothly rotating rainbow border.
- [ ] Inactive nodes remain visually subdued.

### Files Likely Affected
- `frontend/src/styles.css`
- `frontend/src/app/components/graph/graph.component.ts`

---

## Post-Implementation
- [ ] Documentation updates
- [ ] Testing strategy
- [ ] Performance validation

## Notes
- We are specifically avoiding emojis and heavily relying on the Feather icon set for a clean aesthetic.
