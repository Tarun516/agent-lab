# Engineering Rules

## Architecture
- Read existing code and approved decisions before editing.
- Prefer the smallest maintainable solution.
- Document new architectural decisions and trade-offs.
- Avoid unnecessary dependencies and abstractions.

## Checkpoint process
1. Codex produces the design and implementation contract.
2. Human reviews and explicitly approves the contract.
3. Hermes implements in an isolated Git worktree.
4. Hermes runs tests and reports actual changes.
5. Codex independently reviews the diff.
6. Human approves merge and checkpoint completion.

## Implementation boundaries
- Do not silently change approved API or schema contracts.
- Escalate missing or contradictory requirements.
- Do not change unrelated files.
- Do not expose credentials or secrets.
- Do not run destructive migrations or production deployments
  without explicit approval.

## Completion evidence
Report:
- Files created, modified, and deleted
- Reasons for each change
- Tests run and their results
- Known limitations and remaining risks
- Deviations from the approved specification
