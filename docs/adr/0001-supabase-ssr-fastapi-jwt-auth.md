# Supabase SSR & Stateless FastAPI JWT Authentication

We adopt Supabase Auth with `@supabase/ssr` middleware in Next.js 15 and stateless JWT signature verification in FastAPI.

## Context
LearnSync AI consists of a Next.js 15 web client and a FastAPI compute engine backed by Supabase PostgreSQL. We require secure authentication supporting Email/Password and Google OAuth without compromising API latency or introducing race conditions.

## Decision
1. **Frontend Session Management**: Next.js 15 uses `@supabase/ssr` server utilities and middleware for cookie-based session persistence and route protection, paired with a client-side `AuthProvider` (`onAuthStateChange`) for instantaneous UI reactivity.
2. **UI & Aesthetic**: Unified `/login` tabbed card (Sign In, Sign Up, Forgot Password) adhering strictly to `DESIGN.md` (electric purple `#3a10e5`, yellow `#ffd300`, navy `#10162f`, font-black headings, `rounded-[32px]` containers, 150ms transitions, and Google OAuth 1-click button).
3. **Backend Stateless Verification**: FastAPI verifies Supabase JWT access tokens via a `get_current_user` dependency, extracting `sub` (UUID) without outbound HTTP calls to Supabase, with an environment-gated `X-Test-User-Id` header for development/testing ease.
4. **Database Trigger & Lifecycle**: An `AFTER INSERT ON auth.users` PostgreSQL trigger automatically provisions a baseline `public.profiles` record with `onboarding_completed = FALSE`. First-time logins are routed into the `OnboardingGate`.

## Consequences
- Eliminates outbound auth verification network overhead on every FastAPI invocation.
- Server-side middleware redirects unauthenticated requests before rendering, preventing flash-of-unauthenticated-content.
- Guarantees 1-to-1 consistency between `auth.users` and `public.profiles`.
- Unified auth experience matching platform design tokens without layout flashing.
