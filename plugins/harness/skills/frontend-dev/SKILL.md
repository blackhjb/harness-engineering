---
name: frontend-dev
description: React + TypeScript implementation playbook for the harness — feature-folder structure, typed API client pattern, server/client state rules, forms, styling tokens, per-screen state checklist, performance basics, and testing recipes. Use for any frontend implementation, refactor, or code-review work (구현/검증 phases, or whenever writing or reviewing React/TS code).
---

# Frontend Dev Playbook (React + TypeScript)

Operating defaults for harness frontend work. Deviations require a logged reason in `.harness/logs/`.

## 1. Project structure — feature folders

```
src/
  api/
    client.ts          # fetch wrapper — the ONLY file that calls fetch
    errors.ts          # ApiError + normalization
  features/
    appointments/
      api.ts           # typed endpoint functions for this feature
      queries.ts       # TanStack Query hooks + query keys
      components/
        AppointmentList.tsx
        AppointmentList.test.tsx
        AppointmentForm.tsx
      pages/
        AppointmentsPage.tsx
      types.ts         # feature domain types (mirror API contract in design.md)
  shared/              # only after 2+ features use it (rule of two)
    components/  hooks/  utils/
  routes.tsx
  main.tsx
```

Rules: a feature folder contains everything the feature needs; cross-feature imports go through `shared/`, never feature-to-feature. Route names kebab-case, matching design.md IA.

## 2. Component conventions
- Function components, named exports. Props type `XxxProps` above the component.
- One component per file; ~150 lines max — split render-heavy JSX into children.
- Handlers `handleX` inside, props `onX` outside (`onSubmit={handleSubmit}`).
- Split container (fetches, orchestrates) from presentation only when a component both fetches AND has complex markup — never preemptively.
- No business logic in JSX; extract to hooks (`useAppointmentFilters`) or pure functions.

## 3. Server state vs client state
| Data | Where |
|---|---|
| Anything fetched from an API | TanStack Query — always |
| Form draft values | Component state / form lib |
| UI toggles (modal open, selected tab) | Component state |
| Filters, pagination, selected id | URL search params (shareable, survives refresh) |
| Cross-cutting client state (3+ levels of drilling) | Context or a small store — last resort |

Never mirror server data into `useState`. Query keys via a factory so invalidation can't typo:

```ts
export const appointmentKeys = {
  all: ['appointments'] as const,
  list: (filters: Filters) => [...appointmentKeys.all, 'list', filters] as const,
  detail: (id: string) => [...appointmentKeys.all, 'detail', id] as const,
};
```

Mutations invalidate the narrowest key covering affected data. Set `staleTime` deliberately (default 30s for lists; 0 only when freshness is a requirement).

## 4. Typed API client (fetch wrapper + error normalization)

```ts
// api/errors.ts
export type ApiErrorKind = 'network' | 'validation' | 'auth' | 'not_found' | 'server';
export class ApiError extends Error {
  constructor(
    public kind: ApiErrorKind,
    public status: number | null,
    message: string,
    public details?: unknown,
  ) { super(message); }
}
const kindFromStatus = (s: number): ApiErrorKind =>
  s === 401 || s === 403 ? 'auth' : s === 404 ? 'not_found' : s === 422 || s === 400 ? 'validation' : 'server';

// api/client.ts
export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${import.meta.env.VITE_API_BASE_URL}${path}`, {
      headers: { 'Content-Type': 'application/json', ...init?.headers },
      ...init,
    });
  } catch {
    throw new ApiError('network', null, '네트워크 연결을 확인해 주세요.');
  }
  if (!res.ok) {
    const body = await res.json().catch(() => undefined);
    throw new ApiError(kindFromStatus(res.status), res.status, body?.message ?? 'Request failed', body);
  }
  return res.status === 204 ? (undefined as T) : res.json();
}
```

Feature endpoint functions are thin and typed: `getAppointments = (f: Filters) => request<Appointment[]>('/appointments?' + qs(f))`. UI error branching switches on `error.kind`, never raw status codes. Validate untrusted payload shapes at the boundary (zod `parse`) when the contract is unstable.

## 5. Forms
- Controlled inputs. Validation schema (zod) co-located; validate on submit, re-validate on blur after first failure ("reward early, punish late").
- Submit button: disabled while pending, pending label ("저장 중..."); guard double-submit at the mutation level too (`isPending`).
- Server validation errors (`ApiError.kind === 'validation'`) map to fields via `details`; unmapped → form-level message.
- Never lose user input on error — keep values, show the message.

## 6. Styling
- Use what the project already uses. Greenfield default: Tailwind; existing CSS Modules → stay with CSS Modules.
- Design tokens (colors, spacing, radii, font sizes) in one place (Tailwind theme or `tokens.css`) — no hex literals in components.
- Mobile-first; verify at 360px and 1280px (matches the DoD).

## 7. State checklist — per screen (from design.md 화면·상태 인벤토리)
- [ ] loading: skeleton or spinner; layout doesn't jump when content arrives
- [ ] empty: message + the action that gets the user out of empty (CTA), per spec copy
- [ ] error: per-variant handling (network → 재시도 button; auth → re-login path; validation → field messages; server → generic + retry)
- [ ] success: the actual content, plus post-action feedback (toast/inline) per interaction spec
- [ ] pending mutations: optimistic update or disabled control — whichever the spec says

## 8. Performance basics
- Measure before optimizing (React DevTools Profiler); no speculative `memo`.
- `memo` list-item components in large lists; `useMemo`/`useCallback` only for provably expensive computations or referential props into memoized children.
- Code-split at the route level (`lazy()` + Suspense); heavy rarely-used widgets (charts, editors) individually.
- Lists over ~100 rendered rows: paginate or virtualize.
- Keep `key` stable (ids, never index) on dynamic lists.

## 9. Testing recipes (vitest + @testing-library/react)
Test logic-heavy components and non-trivial hooks; skip purely presentational ones.

```tsx
// test-utils.tsx — shared render with providers
const createWrapper = () => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return ({ children }: PropsWithChildren) => (
    <QueryClientProvider client={qc}><MemoryRouter>{children}</MemoryRouter></QueryClientProvider>
  );
};

// component test — behavior, not implementation
test('shows validation error when name is empty', async () => {
  render(<AppointmentForm onSubmit={vi.fn()} />, { wrapper: createWrapper() });
  await userEvent.click(screen.getByRole('button', { name: '저장' }));
  expect(await screen.findByText('이름을 입력해 주세요.')).toBeInTheDocument();
});
```

- Query by role/label (`getByRole`, `getByLabelText`) — doubles as an accessibility check.
- Mock the network at the `api/` boundary (`vi.mock('../api')`) or msw — never mock React internals.
- Each screen state (loading/empty/error/success): at least one assertion for logic-heavy screens.
- Hooks with branching logic: `renderHook` with the same wrapper.

## 10. Pre-done checklist (run before marking any task 완료)
- [ ] plan.md acceptance criteria demonstrably pass (write how in the log)
- [ ] Screen-state checklist (section 7) complete for every touched screen
- [ ] `tsc --noEmit` clean, lint clean, tests green
- [ ] Keyboard path works; focus visible; aria per design spec
- [ ] 360px and 1280px layouts verified
- [ ] No console errors/warnings on exercised paths
- [ ] No API contract workaround snuck in (if tempted, trigger the contract mismatch protocol instead)
- [ ] Log entry + retro/inbox.md candidates appended
