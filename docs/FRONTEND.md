# Frontend Plan

## Goals

- Build a React and TypeScript frontend for the Housework API.
- Optimize the experience for mobile first, while adapting cleanly to tablet and desktop widths.
- Prefer accessibility, legibility, predictable controls, and clear feedback over visual polish.
- Use the approved color palette consistently:
  - `#B56152` for alerts and errors
  - `#749A96` for emphasis and selected states
  - `#DDE3C0` for page backgrounds
  - `#948466` for UI structure such as borders, dividers, and grid-like surfaces
  - `#343434` for primary text

## Initial Project Skeleton

- Place the frontend in `frontend/` so it can live beside the existing Flask backend.
- Use Vite with React and TypeScript for a small, conventional build setup.
- Use Yarn as the package manager and commit a `yarn.lock`.
- Use Yarn Classic for the initial skeleton because it is simple, broadly supported by GitHub Actions, and can be installed with npm when needed.
- Record the expected package manager as `packageManager: "yarn@1.22.22"` in `frontend/package.json`.
- Add scripts for:
  - `yarn lint`
  - `yarn test`
  - `yarn test:ci`
  - `yarn build`
- Use `yarn test` for local Vitest watch mode and `yarn test:ci` for non-watch CI execution.
- Add GitHub Actions coverage for installing dependencies with Yarn, then running linting, unit tests, and a production build from the `frontend/` working directory.
- In CI, use `actions/setup-node` with `cache: yarn` and `cache-dependency-path: frontend/yarn.lock`.
- In CI, install dependencies with `yarn install --frozen-lockfile` so lockfile drift fails.
- Keep the first PR limited to the frontend skeleton, configuration, CI, and this plan. No auth flow, API integration, or task UI should be implemented in the skeleton PR.

## Skeleton File Targets

- `frontend/package.json`
- `frontend/yarn.lock`
- `frontend/index.html`
- `frontend/vite.config.ts`
- `frontend/tsconfig.json`
- `frontend/tsconfig.app.json`
- `frontend/tsconfig.node.json`
- `frontend/eslint.config.js`
- `frontend/src/main.tsx`
- `frontend/src/App.tsx`
- `frontend/src/App.test.tsx`
- `frontend/src/setupTests.ts`
- `frontend/src/styles/tokens.css`
- `frontend/src/styles/global.css`
- `.github/workflows/frontend-ci.yml`

`App.tsx` should be a minimal accessible placeholder and smoke-test target only. It should not start implementing authentication, API integration, task lists, or task forms.

## Stack Decisions

- React with TypeScript for UI implementation.
- Vite for local development and production builds.
- Vitest with `jsdom`, React Testing Library, and `@testing-library/jest-dom` for unit and component tests.
- ESLint for TypeScript, React, and JSX accessibility linting.
- CSS modules or plain CSS for the first iteration; add a component library only if repeated accessible primitives become expensive to maintain.
- Keep generated API clients out of the first skeleton. Revisit after the first real UI slice, using `openapi/openapi.yaml` as the source of truth.

## Design Direction

- Mobile layout should be the default layout, then scale up with responsive breakpoints.
- Target comfortable touch use:
  - minimum 44px touch targets
  - generous spacing between destructive and primary actions
  - forms that avoid cramped multi-column layouts on small screens
- Use semantic HTML controls before custom widgets.
- Maintain visible focus states on all interactive elements.
- Preserve high text contrast against `#DDE3C0` and other background surfaces.
- Use clear inline validation and error summaries with `#B56152`; do not rely on color alone to communicate errors.
- Keep primary text at readable sizes, with body copy around 16px or larger.
- Support keyboard and screen reader use from the start.
- Define design tokens as CSS custom properties for the approved palette, focus outline, spacing, border width, text sizing, and minimum touch target size.

## Future App Direction

These items describe the intended product direction after the skeleton PR. They are not part of the first frontend bootstrap.

- Authentication screen using Google sign-in, then app bearer token storage.
- Primary task list optimized for common mobile use:
  - due or upcoming tasks first
  - clear pending/completed state
  - quick completion action
  - visible overdue or invalid states
- Task creation and editing flow:
  - title, description, end goal date, repeating toggle, recurrence fields
  - recurrence controls that expose only relevant fields for the selected frequency
  - accessible validation tied to each field
- Filtering:
  - date range
  - pending/completed
  - repeating/one-off
- Empty, loading, and error states for every API-driven view.

## API Integration Plan

- Use the existing REST API documented in `openapi/openapi.yaml`.
- Keep the API base URL configurable through a Vite environment variable.
- Represent API response and request shapes with TypeScript types.
- Centralize fetch handling for:
  - bearer token attachment
  - JSON parsing
  - API error normalization
  - network failure messages
- Add integration-level tests around API helpers once API code is introduced.

## Testing Plan

- Unit test shared utilities and API helpers.
- Component test forms, validation behavior, list rendering, empty states, and error states.
- Prefer user-facing queries in React Testing Library.
- Include at least one smoke test for the bootstrapped app shell in the initial skeleton.
- Keep tests fast enough to run on every pull request.

## Accessibility Checks

- Add `eslint-plugin-jsx-a11y` in the initial skeleton so obvious accessibility issues fail linting early.
- Add automated accessibility checks after core screens exist.
- Manually verify:
  - keyboard navigation
  - visible focus order
  - screen reader labels for controls
  - error message association
  - reduced-motion behavior if animation is added

## Open Decisions

- Whether to generate TypeScript API types from the OpenAPI contract or maintain hand-written types until the API stabilizes.
- Whether auth token storage should use memory-only storage, session storage, or another approach.
- Whether to introduce a routing library before the app has more than one primary screen.
