# CP-001 — Extensible Experiment Registry Foundation

Status: **Proposed — awaiting human approval**  
Implementation owner after approval: **Hermes**  
Scope: design only; this checkpoint does not implement application code.

## 1. Requirements, assumptions, dependencies, and non-goals

### Requirements

CP-001 should establish a small, explicit foundation for adding agent experiments without prematurely introducing a service, persistence layer, plugin framework, or third-party dependency.

The implementation contract is:

1. Preserve the existing public Python behavior:
   - `list_experiments()` remains importable from `agent_lab`.
   - `python3 agent_lab.py list` remains valid.
   - The sample `hello-agent` entry remains present.
2. Represent each experiment with a stable name and human-readable description.
3. Validate registry entries at construction time or through one deterministic validation path:
   - names are non-empty, trimmed, and unique;
   - descriptions are non-empty, trimmed;
   - malformed registrations fail clearly and deterministically.
4. Keep listing deterministic and human-readable.
5. Make the registry the single source of truth; avoid duplicating experiment metadata in CLI branches or tests.
6. Add focused tests for valid registration, invalid metadata, duplicate names, deterministic listing, and CLI compatibility.
7. Keep the solution dependency-free and runnable with the repository's documented Python commands.

### Assumptions

- CP-001 is a local/library-and-CLI increment, not a hosted service.
- The registry is authored in Python source and loaded at process start.
- The first useful scale is tens to hundreds of experiments, not thousands or dynamic multi-tenant catalogs.
- Experiment execution is outside this checkpoint. An entry may describe a planned experiment but does not need a callable runner yet.
- Python 3.9+ is available; the current code already uses modern typing syntax and `dataclasses`.
- There is no requirement for backward compatibility with undocumented behavior beyond the current import and CLI behavior.

### Dependencies

- Python standard library only: `argparse`, `dataclasses`, and optionally `typing`/`collections` as needed.
- No database, network service, package manager dependency, environment variable, credential, or external API.

### Non-goals

- Running agents or experiments.
- Scheduling, retries, queues, workers, or concurrency control.
- Persistent storage, CRUD commands, configuration files, or remote registry synchronization.
- Dynamic plugin discovery or arbitrary code loading.
- JSON output or a versioned external API.
- Authentication, authorization, secrets management, or production deployment.
- Replacing the current CLI with a framework or introducing a package layout solely for abstraction.

## 2. High-level architecture

The proposed architecture remains a single-process Python module with four logical responsibilities:

```text
CLI parser -> application command handler -> registry -> experiment metadata
                                  |
                                  +-> formatted stdout
```

- **Experiment metadata model**: immutable value object containing the public fields needed to identify and describe an experiment.
- **Registry**: owns the ordered collection, validates entries, and exposes lookup/listing primitives suitable for future commands.
- **Application/CLI layer**: parses `list`, invokes the registry, formats output, and maps expected command errors to a non-zero exit code if needed.
- **Tests**: verify model and registry invariants independently from CLI behavior, plus one subprocess-level or parser-level compatibility test.

The initial registry remains in memory and source-controlled. This keeps startup and failure behavior simple while leaving a clean seam for a future persistent or dynamically loaded implementation.

## 3. Low-level design, data models, API contracts, and flows

### Data model

Recommended model:

```python
@dataclass(frozen=True)
class Experiment:
    name: str
    description: str
```

CP-001 should retain the current two-field model. Future fields such as `status`, `owner`, `tags`, or `runner` should not be added until a concrete consumer requires them.

The registry is an ordered tuple or an immutable snapshot of entries. Declaration order is the display order and must be stable.

### Proposed internal API

The exact names may be adjusted during implementation only if behavior remains equivalent:

```python
class ExperimentRegistry:
    def __init__(self, experiments: Iterable[Experiment]) -> None: ...
    def list(self) -> tuple[Experiment, ...]: ...
    def get(self, name: str) -> Experiment | None: ...
    def render_list(self) -> str: ...
```

The module-level default registry is built from the current `EXPERIMENTS` declaration. `list_experiments()` remains a compatibility wrapper around that default registry and returns the same line-oriented format:

```text
<name>: <description>
```

Validation contract:

- Empty or whitespace-only names and descriptions raise `ValueError`.
- Leading/trailing whitespace is rejected or normalized consistently; the preferred behavior is normalization followed by validation, documented in tests.
- Duplicate names raise `ValueError` and identify the conflicting name.
- `get(name)` returns the matching immutable value or `None`; it does not execute anything.
- An empty registry renders as the empty string.

### CLI contract

Existing command:

```text
python3 agent_lab.py list
```

Exit code `0` on success. Output is one experiment per line, in declaration order. No output is required for an empty registry. Argument parsing remains handled by `argparse`; no new commands are proposed in CP-001.

### Sequence flows

#### Successful listing

1. Process starts and imports `agent_lab`.
2. The default experiment declarations are constructed.
3. Registry validation runs once during initialization.
4. `argparse` parses `list`.
5. `main()` calls `list_experiments()`.
6. The registry renders its immutable snapshot.
7. `main()` writes the result to stdout and returns `0`.

#### Invalid source registration

1. Process imports the module.
2. Registry construction detects empty metadata or a duplicate name.
3. Construction raises a clear `ValueError` before command handling.
4. The process exits non-zero with a diagnostic; no partial registry is exposed.

#### Future execution seam

Future work may use `get(name)` to resolve metadata and then pass the name to a separately designed runner. CP-001 must not infer or invoke a runner from the metadata model.

## 4. Back-of-the-envelope estimates

These are planning estimates, not capacity commitments.

| Dimension | Estimate | Basis |
|---|---:|---|
| Registry size | 10–500 entries | Source-controlled experiments at this stage |
| Metadata memory | <1 MiB | A few hundred short Python strings and objects |
| Startup overhead | <10 ms typical | Import, validation, and argument parsing on a local machine |
| List throughput | 100–1,000 CLI invocations/s per process | Formatting a small in-memory tuple; shell startup may dominate |
| Concurrent requests | 1 per process | CLI is synchronous and has no server or shared mutable state |
| Persistent storage | 0 bytes | No persistence is introduced |
| Network traffic | 0 bytes | No network path exists |
| Infrastructure cost | $0 incremental | Runs as a local Python process; no service or cloud resource |

The relevant scaling limit is human maintainability of a source-defined tuple, not runtime capacity. If the catalog grows beyond roughly hundreds of entries or requires independent ownership, a separate design should evaluate file-backed or package-discovered registration.

## 5. Alternatives, trade-offs, and rationale

### Keep only the current tuple and add more tests

- **Pros**: smallest diff and no new abstraction.
- **Cons**: validation and lookup behavior remain implicit; future CLI features would duplicate logic.
- **Decision**: not preferred. A small registry boundary is justified because it centralizes invariants without adding infrastructure.

### Introduce `ExperimentRegistry` around the tuple — selected

- **Pros**: explicit ownership of validation, ordering, lookup, and rendering; remains in-memory and dependency-free; preserves the compatibility wrapper.
- **Cons**: adds a modest abstraction before a second command exists.
- **Rationale**: this is the smallest seam that prevents metadata rules from spreading as experiments are added.

### Use a JSON/YAML configuration file

- **Pros**: metadata can be edited without changing Python code; potentially easier for non-developers.
- **Cons**: introduces parsing, file-path/error semantics, schema versioning, and deployment concerns; YAML would add a dependency.
- **Decision**: defer until a real external-authoring requirement exists.

### Use entry points or plugin discovery

- **Pros**: independently installable experiments and automatic discovery.
- **Cons**: packaging and trust boundaries become central; discovery errors and version compatibility are more complex.
- **Decision**: defer. Arbitrary plugin loading is outside the current repository's needs.

### Add a web service or database

- **Pros**: remote access, shared state, and concurrent clients.
- **Cons**: disproportionate operational, security, and reliability cost for a one-command local registry.
- **Decision**: reject for CP-001.

## 6. Security, reliability, observability, and failure handling

### Security

- Keep all metadata declarative and source-controlled.
- Do not execute code while listing or looking up an experiment.
- Do not load paths, modules, URLs, credentials, or user-provided code in CP-001.
- Avoid printing environment variables or exception internals that could contain secrets.

### Reliability

- Validate the complete registry atomically at startup; never expose a partially validated collection.
- Use immutable experiment objects and an immutable registry snapshot to prevent accidental mutation.
- Keep output deterministic so shell scripts and future tests can rely on it.
- A malformed source declaration should fail fast and visibly rather than silently omitting an experiment.

### Observability

For this local CLI, stdout is the user-facing signal and exit status is the machine-facing signal. No logging framework or metrics dependency is warranted. Tests should assert output and exit behavior. If the project later becomes a service, add structured logs, request metrics, and health checks in that separate checkpoint.

### Failure handling

- Invalid metadata: fail at initialization with `ValueError` and a message naming the invalid field or duplicate.
- Invalid command: let `argparse` provide usage information and a non-zero exit code.
- Empty registry: succeed and emit an empty listing; this is a valid state for tests and future packaging.
- Broken output stream: allow the standard Python/OS error to surface; no retry is useful for a one-shot CLI.

## 7. Exact proposed file changes

These are the changes Hermes should make only after approval. They are not being made by this checkpoint author.

### Add

- `docs/checkpoints/CP-001/README.md` — this approved design record. It is the only file added in the current design phase.

### Modify

- `agent_lab.py` — introduce the small registry boundary and validation while preserving `Experiment`, `EXPERIMENTS`, `list_experiments()`, the `list` command, and output format.
- `tests/test_agent_lab.py` — add unit tests for registry invariants and CLI compatibility.
- `README.md` — document the registry contract and any newly exposed behavior, without promising execution or persistence.

### Delete

- None proposed.

No generated files, caches, dependencies, or unrelated source files should be added, modified, or deleted. In particular, `__pycache__` artifacts are not part of the implementation.

## 8. Ordered implementation instructions for Hermes

1. Confirm that the human has explicitly approved CP-001 and that the isolated worktree starts from the approved base commit.
2. Read `AGENTS.md`, this checkpoint document, `agent_lab.py`, `tests/test_agent_lab.py`, and `README.md`.
3. Refactor `agent_lab.py` minimally to add `ExperimentRegistry` and one default registry while retaining the current compatibility symbols and CLI.
4. Implement validation for empty/whitespace metadata and duplicate names; make the error messages deterministic.
5. Implement immutable listing and lookup behavior. Do not add execution, persistence, networking, or new CLI commands.
6. Extend tests for:
   - the existing sample listing;
   - stable order and exact rendering;
   - successful lookup and missing lookup;
   - empty name and empty description rejection;
   - duplicate-name rejection;
   - empty-registry rendering;
   - `python3 agent_lab.py list` success and output.
7. Update README usage/API notes to match the implemented contract.
8. Run the documented unit test command and the CLI command from a clean environment.
9. Review the diff for unrelated changes, generated files, dependency changes, and API drift.
10. Report actual files changed, tests and outputs, limitations, and deviations. Do not merge until the human approves the checkpoint completion.

## 9. Test cases, acceptance criteria, and definition of done

### Test cases

1. The default registry contains `hello-agent`.
2. Listing preserves declaration order.
3. Rendering uses exactly `name: description` with newline separation and no accidental trailing record.
4. `get("hello-agent")` returns the expected immutable object.
5. `get("missing")` returns `None`.
6. An empty name is rejected.
7. A whitespace-only description is rejected.
8. Duplicate names are rejected.
9. An empty registry renders as `""`.
10. The CLI accepts `list`, prints the sample entry, and exits `0`.
11. An unsupported CLI command exits non-zero and displays usage information.
12. The full test suite passes with no third-party installation.

### Acceptance criteria

- Existing documented usage continues to work unchanged.
- All registry invariants are covered by automated tests.
- No experiment code is executed by list or lookup operations.
- No new runtime dependency, persistence layer, or network call is introduced.
- Output is deterministic across repeated runs.
- Public compatibility symbols remain available unless a separately approved contract changes them.

### Definition of done

CP-001 is complete only when:

- Hermes has implemented the approved design in an isolated worktree.
- The test suite and CLI checks pass, with actual command results reported.
- Codex has independently reviewed the resulting diff against this document.
- The human has approved merge and checkpoint completion.

At the current stage, only the design artifact exists; implementation and merge are intentionally pending approval.

## Open decisions requiring approval

1. Approve the `ExperimentRegistry` foundation as the CP-001 scope.
2. Approve normalization of leading/trailing whitespace before validation, or require strict rejection instead.
3. Approve preserving `EXPERIMENTS` as a module-level compatibility symbol while introducing the registry wrapper.
