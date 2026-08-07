---
name: spring-boot-dev
description: Java/Spring 코드를 쓸 때 연다 — 계층·트랜잭션 경계·JPA 위생·Testcontainers.
---
# Spring Boot 3.x Development Playbook

Authoritative conventions for backend work. When design.md conflicts with this file, design.md wins for WHAT to build; this file wins for HOW.

## 1. Project layout — package by feature

```
com.example.app
├── order/                     # one package per business feature
│   ├── OrderController.java   # HTTP only: binding, @Valid, status mapping
│   ├── OrderService.java      # business rules, @Transactional boundary
│   ├── OrderRepository.java   # Spring Data JPA interface
│   ├── Order.java             # JPA entity — never leaves the service layer
│   ├── dto/
│   │   ├── OrderCreateRequest.java   # record + Bean Validation
│   │   └── OrderResponse.java        # record, static from(Order) factory
│   └── OrderNotFoundException.java
├── common/
│   ├── error/GlobalExceptionHandler.java  # single @RestControllerAdvice
│   ├── error/ErrorCode.java
│   └── config/                # JpaConfig, ClockConfig, WebConfig...
└── AppApplication.java
```

Layer rules (violations are review MAJORs):
- controller → service → repository, never skip or reverse. No repository injected into a controller.
- Constructor injection, single constructor, `final` fields. No field/setter `@Autowired`.
- Entities and DTOs never mix: controller sees only DTOs; DTOs are records; map via static factories (`OrderResponse.from(order)`), not reflection mappers.
- Business logic lives in services. A controller method body over ~10 lines is a smell.
- Inject `Clock` (define a bean) instead of `LocalDateTime.now()` — makes time testable.

### Modular monolith rules (default architecture style)

New services start as a modular monolith: one deployable, feature packages as MODULE boundaries. What makes it "modular":

- Dependency direction controlled: modules depend on `common`, never sideways on another module's internals. Cross-module needs go through the other module's service (or an explicitly exported facade) — NEVER inject another module's repository or entity.
- Data ownership: each module is the sole writer of its tables; others read via the owning module's service/DTO, never a join into its tables.
- Transaction boundaries stay inside one module (`@Transactional` at the owning service). A cross-module use case = two transactions + an explicit consistency strategy (event, outbox, or compensation) — decided in design.md, not improvised.
- These boundaries let a module graduate to its own service later (per design.md ADR). Violations are review MAJORs.

### Layered vs hexagonal (when to deviate)

Default: the layered flow above. Move a module to hexagonal (ports & adapters: `Input Adapter → UseCase → Port → Output Adapter`) only when it earns the extra interfaces — 2+ external technologies to isolate (payment gateways, LLM APIs, brokers) or domain rules complex enough to test without Spring. Symptoms: a Service dragged around by web/DB/vendor concerns, or test setup dominated by infrastructure mocking. Plain CRUD stays layered — hexagonal there is ceremony. Either way, the deviation is an ADR in design.md.

## 2. REST API conventions

- Versioned base path `/api/v1/...`; resource nouns, plural: `/api/v1/orders/{orderId}`.
- Status codes: 201+`Location` create, 200 read/update, 204 delete, 400 validation, 401/403 auth, 404 not found, 409 conflict/duplicate, 422 semantically invalid.
- Pagination: Spring `Pageable` (`?page=0&size=20&sort=createdAt,desc`), cap size (`@PageableDefault(size=20)` + max 100). Stable wrapper `{ "content": [...], "page": { "number", "size", "totalElements", "totalPages" } }` — never raw `Page` internals as the public contract.
- Errors: RFC 9457 ProblemDetail everywhere, produced ONLY by the global advice:

```json
{
  "type": "https://api.example.com/errors/order-not-found",
  "title": "Order Not Found",
  "status": 404,
  "detail": "Order 42 does not exist",
  "instance": "/api/v1/orders/42",
  "code": "ORDER-404",
  "errors": [ { "field": "quantity", "message": "must be >= 1" } ]
}
```

`code` from a central `ErrorCode` enum; `errors[]` only for validation failures. Never leak stack traces or SQL in `detail`.

## 3. JPA pitfalls

- `spring.jpa.open-in-view: false` — always. OSIV hides lazy-loading problems until connection-pool exhaustion.
- Associations default `FetchType.LAZY` (incl. `@ManyToOne` — EAGER by default, override it). Load per use case via fetch join or `@EntityGraph`.
- N+1: any loop touching a lazy association is a suspect. Verify in tests (SQL logging or query counting); a list endpoint must not scale queries with row count.
- `LazyInitializationException` = lazy association touched outside a transaction; fix the query (fetch join) — never by widening the transaction or re-enabling OSIV.
- `@Transactional` on service methods only; `readOnly = true` for queries. Self-invocation (`this.otherMethod()`) bypasses the proxy — no transaction. `REQUIRES_NEW` suspends the caller: outer rollback will NOT roll back the inner commit — use deliberately only (e.g., audit logs).
- Dirty checking: inside a transaction mutations flush automatically — `save()` on a managed entity is redundant; mutating outside a transaction silently persists nothing.
- Bulk `@Modifying` queries bypass the persistence context — pair with `clearAutomatically = true`.
- `ddl-auto: validate` in every non-local profile. Schema changes = Flyway migrations (`db/migration/V<next>__<desc>.sql`), never edit an applied version, prefer expand/contract (add → backfill → switch → drop) for zero-downtime.

## 4. Validation

- Request DTOs carry Bean Validation (`@NotNull`, `@Size`, `@Positive`, custom validators); controllers use `@Valid` (`@Validated` on the class for param-level constraints).
- Format/shape validation belongs to DTOs; business rules (duplicate email, insufficient stock) belong to services and throw domain exceptions mapped in the advice.
- `MethodArgumentNotValidException` → 400 ProblemDetail with `errors[]`; `ConstraintViolationException` → 400. Wire both in the global advice once.

## 5. Testing strategy

| Level | Tool | Use for | Speed |
|---|---|---|---|
| Unit | JUnit 5 + Mockito + AssertJ | service logic, mappers, validators | ms — the bulk of tests |
| Web slice | `@WebMvcTest` + MockMvc | controller binding, status codes, ProblemDetail contract | fast |
| JPA slice | `@DataJpaTest` + Testcontainers | custom queries, mappings, N+1 checks | medium |
| Integration | `@SpringBootTest` + Testcontainers | migration validity, transaction behavior, e2e API happy paths | slow — few, high-value |

- Testcontainers runs the SAME database engine/version as prod; one shared static container (base class or `@ServiceConnection`). H2-instead-of-Postgres is forbidden for anything asserting SQL behavior.
- Naming: `methodOrBehavior_expectedOutcome_underCondition`, e.g. `createOrder_returns409_whenIdempotencyKeyReused`; Given/When/Then blocks inside.
- Assert behavior, not wiring: no `verify()` on every mock; assert returned values, persisted state, exceptions, HTTP contracts.
- Every bug fix starts with a failing regression test.

## 6. Gradle commands

```bash
./gradlew test                                   # full suite (verification gate)
./gradlew test --tests 'com.example.order.*'     # focused
./gradlew build                                  # compile + test + jar
./gradlew bootRun --args='--spring.profiles.active=local'
./gradlew dependencies --configuration runtimeClasspath   # dependency audit
./gradlew test --rerun-tasks                     # bust test-result cache when suspicious
```

## 7. Config & profiles

- `application.yml` (safe defaults) + `application-local.yml` / `-dev.yml` / `-prod.yml`; select via `SPRING_PROFILES_ACTIVE`.
- NO secrets in any yml, ever — including dev. Env placeholders: `spring.datasource.password: ${DB_PASSWORD}`. Locally env vars or gitignored `.env`; in prod Cloud Run injects from Secret Manager (`--set-secrets`). See the sre agent for the GCP side.
- Bind config into `@ConfigurationProperties(prefix = "app")` records — no scattered `@Value` strings.

## 8. Observability

- Actuator: expose `health,info,metrics,prometheus` only; `management.endpoint.health.probes.enabled: true` for Cloud Run probes; never expose `env`/`heapdump` publicly.
- Structured JSON logs to stdout (Logback JSON encoder) with `severity`, logger, correlation ID (MDC filter per request). Log at boundaries: request in/out (no PII bodies), external calls with latency, every caught exception exactly once — no log-and-rethrow.
- Domain exceptions in the advice log at WARN; unexpected 500s at ERROR with stack trace.

## 9. Definition of done — check ALL before marking a backend task complete

- [ ] Acceptance criteria in plan.md each covered by at least one test
- [ ] `./gradlew test` fully green (evidence in the .harness/logs/ entry)
- [ ] design.md contract matched exactly: paths, DTO fields, status codes, error codes
- [ ] No entity crosses the controller boundary; DTOs are records with validation
- [ ] `@Transactional` boundaries at service layer; `readOnly` on queries; no self-invocation traps introduced
- [ ] New/changed queries checked for N+1; open-in-view still false
- [ ] Schema changes as new Flyway migration; no applied migration edited; rollback story stated
- [ ] Errors flow through the global advice as ProblemDetail; nothing leaks internals
- [ ] No secrets/credentials in code, config, or test fixtures
- [ ] Log entry appended to .harness/logs/, insights recorded as wiki nodes (.harness/wiki/)
