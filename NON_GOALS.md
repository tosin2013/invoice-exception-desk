# NON_GOALS — Invoice Exception Desk

Explicit exclusions. If a proposed change touches one of these, it is out of scope for this effort
and needs a separate decision (and, for anything touching data protection, separate review).

1. **No real personal data (PII).** Only synthetic, fabricated fixtures. No customer, employee, or
   contact records; no names, emails, phone numbers, addresses, or account numbers that map to people.
2. **No credentials or secrets.** No API keys, tokens, passwords, connection strings, or `.env`
   secrets in code, fixtures, or logs. The runtime is offline by design.
3. **No reminders or outbound messages.** The tool never sends email/SMS/notifications and never
   contacts anyone. Owner/notes are internal annotations only.
4. **No payment processing.** It does not move money, charge cards, initiate ACH, or integrate with
   payment gateways. Payment *events* (R2) are records for balance math, not transactions.
5. **No tax advice or tax computation.** No tax rates, filing logic, or advice; amounts are the raw
   invoice figures only.
6. **No deployment or hosting.** No servers, containers, CI/CD to production, infra-as-code, or
   release automation.
7. **No authentication or multi-tenancy.** Single-operator, local, offline use. No logins, roles,
   SSO, org accounts, or tenant isolation.
8. **Not a QuickBooks/invoicing replacement.** It does not create invoices, define charts of
   accounts, or reconcile ledgers. It is a decision queue over an imported CSV.
9. **No external services / network calls.** Standard-library-only processing; no outbound requests
   of any kind during import, aging, or queueing.
10. **No collections workflow.** No dunning, promises-to-pay automation, escalation policies, or
    legal/collections actions. A promised-pay date (R3) is a note, never a balance adjustment.

See `ACCEPTANCE.md` AT-09 (no network/secrets) for the guardrail test intent, and `ROADMAP.md` for
which stage owns each capability.
