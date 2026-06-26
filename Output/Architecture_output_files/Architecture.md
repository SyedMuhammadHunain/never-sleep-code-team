# Shopping App Architecture

## Overview
This project follows Clean Architecture and Domain-Driven Design (DDD) principles to ensure scalability and maintainability. The application is structured by bounded contexts rather than technical layers.

## Directory Structure
- `src/app/core`: Global configurations, interceptors, and application-wide services (AuthService).
- `src/app/modules/authentication`: User login and registration logic.
- `src/app/modules/product-catalog`: Product listing, filtering, and detail logic.
- `src/app/modules/shopping-cart`: Cart management logic using Zustand for state management.
- `src/app/modules/user-profile`: User account and preferences management.
- `src/app/infrastructure`: Database interfaces and API service wrappers.

## Design Principles
- **State Management**: Use `Zustand` for global state (e.g., shopping cart, user session). Custom React Context for state is explicitly banned.
- **Separation of Concerns**: Business logic is separated from UI components. API interactions are encapsulated within service classes.
- **Naming Conventions**: No generic folders like `utils` or `helpers`. Use domain-specific names (e.g., `PriceCalculator`, `CartPersistenceManager`).
- **Code Quality Limits**:
  - Functions MUST be under 80 lines.
  - Files MUST be under 200 lines.
  - Enforce early return patterns and avoid deep nesting (max 3 levels).

## Technology Stack
- **Frontend**: Angular (TypeScript).
- **Backend**: Node.js.
- **Auth**: JWT-based via dedicated Auth service.
- **Local Storage**: For offline cart persistence.

## Compliance Checklist
- [x] Did I use an external library (e.g., Zustand) instead of custom React Context?
- [x] Are generic folder names (`utils`, `helpers`) completely banned?
- [x] Are function/file size constraints explicitly mentioned?