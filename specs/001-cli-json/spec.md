# Feature Specification: `--json` output for the slugify CLI

**Feature Branch**: `001-cli-json` | **Created**: 2026-10-18 | **Status**: Ready
**Input**: Add an opt-in `--json` flag that prints the input and slug as a JSON object.

## User Scenarios & Testing

### User Story 1 - Machine-readable output (Priority: P1)
A script calls `slugify --json Hello World` and gets one line of JSON it can parse, containing both the original text and the slug.

**Acceptance Scenarios**:
1. **Given** `slugify --json Hello World`, **Then** stdout is exactly `{"input": "Hello World", "slug": "hello-world"}` followed by a newline, exit code 0.
2. **Given** `--json` with other options (e.g. `--separator _`), **Then** `slug` reflects those options.
3. **Given** `--json --stdin` with stdin `Hi There`, **Then** `input` is the exact stdin text (including any trailing newline) and `slug` is its slug.

### User Story 2 - Nothing changes without the flag (Priority: P1)
**Acceptance Scenarios**:
1. **Given** any command without `--json`, **Then** output is identical to before this feature.

### Edge Cases
- Non-ASCII input is escaped the standard-library way (`json.dumps` default, `ensure_ascii=True`), e.g. `Café` → `"Caf\u00e9"`.
- Empty input: `slugify --json` prints `{"input": "", "slug": ""}`.

## Requirements
- **FR-001**: The CLI MUST accept a new boolean flag `--json`.
- **FR-002**: With `--json`, the CLI MUST print exactly `json.dumps({"input": <input text>, "slug": <slug>})` and a newline. Key order: `input`, then `slug`. Default `json.dumps` separators and escaping.
- **FR-003**: The slug MUST be computed with the same options as without `--json`.
- **FR-004**: Without `--json`, behaviour and output MUST be unchanged.
- **FR-005**: The parsed arguments without `--json` MUST keep their current shape (constitution III).
- **FR-006**: The Python API and `slugify/_legacy.py` are out of scope and MUST NOT change.

## Success Criteria
- **SC-001**: All existing tests still pass, unchanged.
- **SC-002**: New tests cover FR-001 to FR-005.
