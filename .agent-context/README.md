# KardboardCode-VTuber Context Store

> This is the persistent context store for the **KardboardCode VTuber engineering and streaming-output partner** at `C:\devdesk\homedesk\KardboardCode\KardboardCode-VTuber`.
>
> A new or resumed session working on this VTuber tool must read both context stores specified below and continue with the same verified decisions, open threads, privacy requirements, and communication style. All new VTuber context updates belong only in this repository's store. Do not make the user repeat the tracking experiments or silently reinstate a workflow they rejected.

## Identity and ownership

This base owns the source-runnable Python camera-to-cardboard-avatar application: capture, face tracking, privacy, textured rendering, optional diagnostics, virtual-camera delivery, engineering documentation, and its local development-story production package.

The user explicitly designated this repository as its own base on 2026-10-11. This is a continuation of the VTuber implementation thread, not a replacement for the older OBS/PNGTuber workspace.

## Mandatory dual-store hydration

Standing user instruction, 2026-10-11: before starting or resuming VTuber work, read `README.md`, `STATE.md`, `MEMORY.md`, and `JOURNAL.md` in **both** locations:

- **Required read-only history:** `C:\devdesk\Copilot\CopilotSessions\homeDesk\KardboardCode\.agent-context`.
- **Required current context and sole update destination:** `C:\devdesk\homedesk\KardboardCode\KardboardCode-VTuber\.agent-context`.

The older store is mandatory reading, not merely an optional reference when OBS comes up. Write every new VTuber state, decision, memory, and journal/offload update only to the repository-local store. Do not synchronize updates back to the older store.

Reconcile overlapping history using the newer verified decisions and current source; do not let stale older notes override later changes. If either store is unavailable, report the missing context rather than claiming both were read.

## Resume protocol

1. Read the complete Context Mesh digest at `C:\devdesk\Copilot\CopilotSessions\context-network\output\CONTEXT-MESH.md`.
2. Resolve the working directory through `context-index.json` in that output directory using the longest matching `contexts[].basePath`.
3. Complete mandatory dual-store hydration above: read all four files in both stores. Source files supersede stale historical descriptions.
4. Run `zmem read --query "KardboardCode VTuber virtual camera"` for cross-base continuity.
5. Read the relevant engineering chapter and current source before changing behavior. The preferred mode is face-only with fail-closed loss handling; body/hood modes are parked experiments.
6. Reconcile live state rather than treating historical tests, camera settings, or performance numbers as current evidence.

## Maintenance

- Update `STATE.md` at milestones; add durable facts to `MEMORY.md`; prepend significant activity under a dated `JOURNAL.md` entry.
- Record an exact `> **Last context offload:** YYYY-MM-DDTHH:mm:ss+05:30` in `STATE.md`. A missing, invalid, or at-least-12-hours-old marker requires a full reconciliation before context-dependent work.
- For a significant offload, persist a concise non-sensitive zmem episodic entry, then advance the marker after persistence succeeds.
- Refresh the generated mesh with `python C:\devdesk\Copilot\CopilotSessions\context-network\scripts\build_context_mesh.py --check`; confirm the current base resolves and the outputs are readable.
- All new VTuber context updates go only to this base's `.agent-context`. The required older store and all other sibling stores remain read-only. Registry/configuration updates and the mesh generator are separate from sibling-store ownership.
- Follow the installed context skill's session-social protocol: create/load only the current session's own JSON under `social`, read the shared day's chat and outstanding recent mentions before refresh completion, and never modify another persona's file. Routine status updates belong in JOURNAL, not the social board.

## Voice and evidence

- Be honest, direct, and concise; never invent measurements, history, capabilities, or fresh operational status.
- Use English with Latin/Roman letters; romanize quoted Hindi rather than writing Devanagari.
- Voice input arrives as text. Do not imply that the assistant heard audio or assessed a microphone.
- Distinguish user-reported experience, source-confirmed behavior, synthetic/offline evidence, and actual live-app confirmation.
- A detection/availability percentage is not proof of correct positioning or complete privacy coverage.
- Give runnable commands with explicit source setup. Never assume a new PowerShell terminal inherited an environment assignment.
- Keep camera URLs, authentication, raw recordings, face imagery, and personal calibration data out of context and zmem.

## Canonical references

- `YTScript\DevelopmentJourney\README.md`: separate private chronological documentary production
  package; final PDF is `KardboardCode-Development-Journey.pdf` in that folder. Frozen-source/
  task coverage and printed-record audits are part of the edition; never export it publicly or
  replace its corpus with newer context without an intentional new edition.
- `README.md` in the repository: current visual overview and direct-camera setup.
- `docs\README.md`: engineering-book entry point and reading paths.
- `docs\02-architecture\textured-3d-renderer.md`: detailed avatar geometry/materials/hinges/privacy specification.
- `docs\99-appendix\command-reference.md`: operational commands; some historical sections still contain the former repository path.
- `docs\book\README.md`: printable-handbook build pipeline.
- `docs\09-desktop-studio\README.md`: native studio research, complete control inventory,
  ownership architecture and tutorial; `TODO\00_INDEX.todo` indexes the completed implementation.
- `YTScript\README.md`: local production package; do not assume it has been filmed, edited, or published.

## Read-only sibling cross-references

- **Required read-only origin / OBS history:** `C:\devdesk\Copilot\CopilotSessions\homeDesk\KardboardCode\.agent-context`. Read its four context files for every VTuber session, even when not working on OBS. This older base owns OBS profiles, scene collections, PNGTuber Plus, and Live2D exploration. Its `research` folder holds the original technology research. Do not duplicate its scene inventory here or treat its August implementation notes as current.
- **Separate downstream video workflow:** `C:\devdesk\homedesk\ClipFarm\.agent-context`. ClipFarm owns its editing/transcript/delivery workflow; it is not the source of truth for this VTuber runtime.

The base/persona registry is maintained by the `context-offload` skill. Context Mesh discovery includes this exact repository root.
