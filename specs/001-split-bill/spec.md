# Feature Specification: Split a bill fairly

**Feature Branch**: `001-split-bill` | **Created**: 2026-10-18 | **Status**: Ready
**Input**: Split a total (in cents) between N people so the shares add up exactly.

## User Scenarios & Testing

### User Story 1 - Even split with remainder (Priority: P1)
A user splits a bill and every cent is accounted for.

**Acceptance Scenarios**:
1. **Given** total 1000 and 3 people, **Then** shares are `[334, 333, 333]`.
2. **Given** total 900 and 3 people, **Then** shares are `[300, 300, 300]`.
3. **Given** total 0 and 2 people, **Then** shares are `[0, 0]`.

### User Story 2 - Bad input is rejected (Priority: P1)
**Acceptance Scenarios**:
1. **Given** people = 0 or negative, **Then** `ValueError` is raised.
2. **Given** a negative total, **Then** `ValueError` is raised.
3. **Given** a non-integer total or people (including `bool` and `float`), **Then** `TypeError` is raised.

## Requirements
- **FR-001**: Provide `split_bill(total_cents: int, people: int) -> list[int]` in `bill_split/__init__.py`.
- **FR-002**: Return a list of length `people` whose sum equals `total_cents`.
- **FR-003**: Each share is `total_cents // people`; the remainder `total_cents % people` is given one extra cent each to the FIRST shares in the list.
- **FR-004**: `people < 1` or `total_cents < 0` raises `ValueError`.
- **FR-005**: Non-`int` arguments, or `bool`, raise `TypeError`.

## Success Criteria
- **SC-001**: Tests cover every acceptance scenario.
