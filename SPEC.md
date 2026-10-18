# SPEC — Phase One (R0 / Discovery) of the Invoice Exception Desk Spec Kit plan
Source: Notion "[WORKSHOP] SpecKit developer bootstrap..." (<internal-plan-id>) -> child plan "DRAFT v0.1 — Invoice Exception Desk" (<internal-plan-id>). The parent page has no phase list; the child plan's roadmap starts at R0, the only stage marked [planned]. R0 involves no app build.

## Business case
Invoice Exception & Follow-Up Desk for a fictional B2B commercial-cleaning operator: "Which unpaid invoices need attention, what is truly outstanding, who does what next?" It's a decision queue. It is not invoicing, collections, payments, or a QuickBooks replacement.
User stories BR-01..BR-05: CSV import with accepted/rejected/duplicate reasons and idempotent retry; explicit as-of date, exact balance, days overdue, aging bucket; follow-up queue with owner and notes (no outbound messages); (later) partial payments recalculated without overwriting the original amount; (later) promised-pay date is a note only and never reduces the balance.
Policies: USD; integer cents only; key = issuer+invoice_id; identical duplicate = no-op, inconsistent duplicate = flagged; timezone America/New_York; overdue = balance>0 AND due_date < as_of; no negative payments or overpayment; payment event IDs are idempotent.

## Phase one tasks (R0), deliver as files in this directory
T1. ROADMAP.md: entries R0–R6, each with ID, objective, in/out scope, dependencies, owner, status, spec/test links, and exit evidence.
T2. data/generate_invoices.py: a deterministic seed generator (Python stdlib only, fixed seed) that writes data/invoices.csv with about 30 synthetic invoices. It must include valid rows, identical and inconsistent duplicates, invalid amounts, invalid dates, empty rows, and due-date boundary cases relative to as_of=2026-10-15 (not-due, due-today, 1/30/31/60/61/90/91+ days). Include a few rows with partial-payment data for v2a.
T3. data/oracle.json: independently computed expected results for each row (accepted/rejected/duplicate + reason, remaining balance in cents, days overdue, aging bucket) plus totals. Produce it with a separate script, data/compute_oracle.py.
T4. ACCEPTANCE.md: an acceptance-suite specification for AT-01..AT-10 (import counts/idempotency; rejection reasons with no partial import; integer-cent sums excluding zero balance; aging boundaries; deterministic prioritization plus owner/notes persistence; R2 payment idempotency/overpay/negative; promised date never reduces balance; migration preserves v1; no network/secrets; fresh-checkout reproducibility). Each item needs inputs, expected outcomes referencing oracle rows, and a pass criterion.
T5. tests/test_oracle.py: runnable stdlib unittest checks that the generator is deterministic and that oracle.json agrees with the CSV and the policies above. Run it and make it pass.
T6. NON_GOALS.md: exclusions (no PII, credentials, reminders, payments, tax advice, deployment, auth/multitenancy).
T7. R0_REPORT.md: what was done, test output, open questions for the Founder/reviewer.

## Rules
Do phase one (R0) only. Do NOT build the application (R1). No network, no git push, no external services. Stop when T1–T7 are done.
