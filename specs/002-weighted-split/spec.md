# Feature Specification: Weighted bill split

**Feature Branch**: `002-weighted-split`

**Created**: 2026-10-22

**Status**: Implemented

**Input**: User description: "Add split_weighted(total_cents, weights) to bill_split: split a bill in proportion to integer weights (for example one person ordered twice as much), so the shares add up exactly to the total. Keep the existing split_bill unchanged. Use the short name weighted-split."

## Clarifications

### Session 2026-10-22

- Q: Which input container types should `split_weighted` accept for the `weights` argument? → A: Accept a list or tuple only; generators, strings, and `None` raise `TypeError`.
- Q: When an argument is invalid in more than one way, which error type takes precedence? → A: `TypeError` wins; validate all types before any value checks.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Split in proportion to what each person ordered (Priority: P1)

A user shares a bill where people consumed different amounts. Each person provides a positive integer weight representing how much they ordered, and receives a share proportional to that weight. Every cent of the bill is assigned.

**Why this priority**: Proportional splitting is the entire purpose of the feature; without it there is no feature.

**Independent Test**: Split a total using two or more different weights and verify each share is proportional to its weight and the shares sum exactly to the total.

**Acceptance Scenarios**:

1. **Given** a total of 1000 cents and weights `[2, 1]`, **When** the bill is split, **Then** the shares are `[667, 333]` and sum to 1000.
2. **Given** a total of 1000 cents and weights `[1, 1]`, **When** the bill is split, **Then** the shares are `[500, 500]`.
3. **Given** a total of 100 cents and weights `[3, 1]`, **When** the bill is split, **Then** the shares are `[75, 25]`.
4. **Given** a total of 0 cents and weights `[1, 2]`, **When** the bill is split, **Then** the shares are `[0, 0]`.

---

### User Story 2 - Fair rounding when proportions are not whole cents (Priority: P1)

When the exact proportional share is not a whole number of cents, the system rounds every share while still assigning the full total. No cent is created or lost.

**Why this priority**: Most real totals and weights do not divide evenly; incorrect rounding would break the core guarantee that shares add up exactly.

**Independent Test**: Use totals and weights that produce fractional shares, verify each share is within one cent of its exact proportional value, and verify the sum equals the total.

**Acceptance Scenarios**:

1. **Given** a total of 1000 cents and weights `[1, 1, 1]`, **When** the bill is split, **Then** the shares are `[334, 333, 333]`.
2. **Given** a total of 100 cents and weights `[1, 1, 1]`, **When** the bill is split, **Then** the shares are `[34, 33, 33]`.
3. **Given** any valid total and weights, **When** the bill is split, **Then** every share differs by less than one cent from its exact proportional amount and the shares sum exactly to the total.

---

### User Story 3 - Invalid input is rejected (Priority: P1)

A user or caller makes a mistake in the total or weights. The system rejects the input with a clear error instead of returning misleading shares.

**Why this priority**: Money calculations must fail loudly rather than silently produce an impossible split.

**Independent Test**: Call the split with each invalid input category and verify the documented error type is raised.

**Acceptance Scenarios**:

1. **Given** a negative total, **When** the bill is split, **Then** a `ValueError` is raised.
2. **Given** an empty weight list, **When** the bill is split, **Then** a `ValueError` is raised.
3. **Given** weights that are all zero, **When** the bill is split, **Then** a `ValueError` is raised.
4. **Given** any negative weight, **When** the bill is split, **Then** a `ValueError` is raised.
5. **Given** a non-integer total, weight, or `bool` value, **When** the bill is split, **Then** a `TypeError` is raised.

---

### Edge Cases

- A weight of zero is valid and yields a zero-cent share for that person, as long as at least one other weight is positive.
- A total of zero returns zero for every person, regardless of valid positive weights.
- A single person with any positive weight receives the entire total.
- Very large totals and weights are handled exactly, with no floating-point rounding.
- Equal weights produce the same shares as the existing even split for the same total and number of people.
- A weights argument that is not a sequence of integers (for example a generator, string, or `None`) raises a `TypeError`; lists and tuples are accepted.
- When an argument is both the wrong type and out of range (for example `-1.5`), `TypeError` is raised because type validation runs first.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The library MUST provide `split_weighted(total_cents: int, weights: list[int] | tuple[int, ...]) -> list[int]` in `bill_split/__init__.py`.
- **FR-002**: The result MUST contain exactly one share per weight, in the same order as the weights.
- **FR-003**: Every returned share MUST be a non-negative integer number of cents.
- **FR-004**: The returned shares MUST sum exactly to `total_cents`.
- **FR-005**: Each share MUST be within one cent of the exact proportional amount `total_cents * weight / sum(weights)`.
- **FR-006**: When proportional shares are not whole cents, leftover cents MUST be assigned deterministically, one cent per share, to the shares with the largest fractional remainders; ties are resolved in favour of the earlier weight. This makes equal weights match the existing even split.
- **FR-007**: A weight of zero MUST produce a zero-cent share.
- **FR-008**: `total_cents` MUST be a non-negative integer and every weight MUST be a non-negative integer. `bool` values MUST NOT be accepted as integers.
- **FR-009**: `total_cents < 0`, an empty weights sequence, a negative weight, or a sum of weights of zero MUST raise `ValueError`.
- **FR-010**: Non-integer arguments, including `bool` and `float`, MUST raise `TypeError`. The `weights` argument MUST be a `list` or `tuple` of integers; any other type (generators, strings, `None`, `range`, and other sequences) MUST raise `TypeError`. Type validation MUST run before value validation, so an argument that is both non-integer and out of range raises `TypeError`.
- **FR-011**: The function MUST be deterministic and pure: identical inputs always produce identical outputs with no I/O, randomness, or clock access.
- **FR-012**: The existing `split_bill` function and its behaviour MUST remain unchanged.

### Key Entities *(include if feature involves data)*

- **Bill total**: The amount to split, expressed as an integer number of cents.
- **Weight**: A non-negative integer describing each person's relative share of the bill.
- **Share**: The non-negative integer number of cents assigned to one person; shares sum to the bill total.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For every valid total and weights sequence tested, the returned shares sum exactly to the total in 100% of cases.
- **SC-002**: For every valid input tested, each share is within one cent of its exact proportional amount.
- **SC-003**: Every acceptance scenario in this specification is covered by at least one automated test.
- **SC-004**: Equal weights produce exactly the same shares as `split_bill` for the same total and number of people in 100% of tested cases.
- **SC-005**: Every invalid input category in this specification raises the documented error type in automated tests, with no invalid input silently producing shares.
- **SC-006**: All existing `split_bill` tests continue to pass unchanged.

## Assumptions

- Weights are non-negative integers, and at least one weight is positive; a zero weight means that person ordered nothing.
- The number of shares equals the length of the weights sequence, and the weights order defines the output order.
- Leftover cents are allocated by largest fractional remainder, with ties going to the earliest weight, matching the existing even split for equal weights.
- Negative totals and zero-sum weight lists have no meaningful proportional interpretation and are rejected.
- Only integer cents are used; floating-point amounts are out of scope, consistent with the project constitution.
- The feature is a pure library function with no CLI or user-interface changes.
