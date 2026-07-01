# ui-enhancements Research

## Overview
This feature introduces UI polishes including a Theme Toggle (light/dark/system), top-center Toast notifications, a sleek bottom-centered input box for prompt interaction, Skeleton loaders to improve perceived loading time, and a dynamic rotating rainbow border glow to highlight active workflow nodes.

## Problem Statement
- The current interface relies entirely on light mode without options to switch.
- The AI prompt box is currently a plain textarea which looks clunky and takes up unneeded space.
- The "Loading workflow..." state is generic.
- It is difficult to immediately tell which agent is currently active when a workflow runs.
- Missing feedback notifications for success, error, or warning actions.
- Missing high quality icons (emojis are currently used as placeholders).

## User Stories / Use Cases
- As a user, I want to toggle between light and dark modes easily to match my system preference or environment.
- As a user, I want to type my prompts into a floating, centered, sleek input box at the bottom.
- As a user, I want to see a skeleton layout when a workflow is generating so that I understand what is being prepared.
- As a user, I want a very obvious animated rainbow border to indicate precisely which agent node is actively working in the graph.
- As a user, I want top-center toasts to confirm actions or notify me of errors.

## Technical Research

### Approach Options

**1. Icons:**
- Emojis (current approach) - Pros: Built-in. Cons: Not professional, cross-platform inconsistency.
- Feather Icons from `~/Downloads/feather.zip` - Pros: Clean, lightweight, professional. Cons: Requires extraction and setup.

**2. Rainbow Border Glow:**
- Use SVG filters directly in `ngx-graph`.
- Wrap the node content in a DIV and use CSS `@keyframes` with `conic-gradient` mask or rotating background. **(Recommended)**

**3. Skeleton Loaders:**
- CSS pulsing backgrounds mimicking the graph and nodes. **(Recommended)**

**4. Toast Notifications:**
- Leverage a third party library like `ngx-toastr`.
- Build a lightweight custom `ToastService` and Component mounted on the app root, using Angular Signals. **(Recommended)**

### Recommended Approach
- Unzip `feather.zip` to `frontend/src/assets/icons`.
- Build a custom `ToastService` and `ThemeService` leveraging Angular Signals for state management.
- Update `ngx-graph` node templates to inject a CSS `conic-gradient` animation when the node state is marked "active".

### Required Technologies
- Angular Signals
- Feather Icons (SVG)
- Modern CSS (Flexbox, CSS Variables, Animations)

### Data Requirements
- `localStorage` for saving the user's theme preference.

## UI/UX Considerations
- Toasts should appear smoothly at `top-center` and self-dismiss.
- The prompt box should float slightly above the bottom boundary with a soft shadow.

## Integration Points
- Theme CSS variables must cleanly map across all UI elements.
- The graph component must know which node is "active" to attach the animation.

## Risks and Challenges
- **SVG constraints in ngx-graph**: CSS border effects on SVGs can be tricky; we might need to apply the rainbow border to a `foreignObject` or HTML wrapper inside the node.

## Open Questions
- Is there a specific speed for the rotating rainbow glow? (Default to 2s per rotation).

## References
- Angular Signals Documentation
- Feather Icons
