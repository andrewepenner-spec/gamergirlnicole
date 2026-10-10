# Agent/competency workstream assignments

This document assigns **subagent-style roles and file ownership** for continued parallel development. The tasks below were integrated directly in this session; independent autonomous agents were **not** actually invoked. These assignments provide clear boundaries if a coding platform with true parallel agents is later used.

| Workstream / specialist | Owned files | Delivered scope | Acceptance gate / future assignment |
|---|---|---|---|
| UX / visual designer | `web/styles.css`, `docs/reference-*.png` | Desktop/mobile design system, cinematic hero, VHS scene view, dossier, cards, notebook, accusation and result UI | Validate actual screenshots across tablet, laptop and phone; accessibility contrast/focus audit |
| Front-end engineer | `web/main.js`, `web/index.html` | Lobby, scene flows, private hand/actions, notes, identities, accusations, reconnect, mobile layout | Browser E2E across 2+ profiles; no focus-loss and all keyboard interactions |
| Theater / media engineer | `web/theater.html`, `web/theater.js`, `web/assets/` | Anonymous read-only TV display, timed original storyboards and synchronized phase playback | Add licensed/filmed/animated media with cue sheets; network-lag playback test |
| Rules / gameplay engineer | `server/engine.py` | Turn guards, six investigation actions, true personal facts, deductions, elimination, suspense round, win logic | Property-based playthroughs; add explicit replay pause-and-resume authorization, host migration |
| Backend / networking engineer | `server/app.py` | Authentication tokens, FastAPI, HTTP command interface, revision WebSocket and polling | Validate reconnect and concurrency under load; network hardening |
| Database / privacy engineer | `server/app.py` | SQLite persistent room state, token separation, public/private response models | Migrations, audit logging, retention policy, Postgres production support, session revocation |
| Narrative / puzzle author | `server/content.py` | 3 chapters × 5 scenes, 18 original cases, 28 clue facts per chapter/case overlay, 10 character fact sets | Human playtesting, more sophisticated relational clues, voice scripts and continuity checks |
| QA / red-team specialist | `tests/test_engine.py`, `tests/test_api.py` | 28 automated checks, full-case engine simulation, HTTP multiplayer end-to-end, truth privacy | Playwright once available, accessibility E2E, multi-device latency, adversarial token/room probing |
| DevOps / release engineer | `run.py`, Docker files, README | Python/Docker run paths and portability, source package | Deploy HTTPS and backups, health alerts, per-room TTL and CI pipeline |
| IP / producer review | `docs/reference-specification.docx`, README | Clear boundary between historic reference and new playable game content | Seek rights clearance if using original Clue brand, stories, performances, music or case text |

## Parallelization rule

The content/rules/backend streams can work concurrently against an agreed typed `GameState` / `PlayerProjection` schema. The frontend must not assume that a property omitted from its private projection exists. Integration goes through the authenticated API; only game-end results may contain the true solution. QA's acceptance suite should be a hard gate before release.

## What was verified during this build

- 18 cases: five scenes each, required facts and winning solution by authoritative engine.
- HTTP two-player game with case selection, five scenes, disclosures, card actions, and a correct accusation.
- Private projections do not contain other players' identities or hands; theater projection omits all live secrets.
- Correct murders + incorrect rival IDs trigger one final challenger turn.
- Server returns no solution before the case ends.
- Python test suite and JavaScript syntax checks run successfully.

See the test files for executable contract examples, and `docs/PRODUCTION_BACKLOG.md` for deferred product work.
