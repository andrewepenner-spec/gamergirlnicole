# Director’s Cut — gameplay design and implementation notes

**Release:** 2.0 — October 2026  
**Scope:** optional upgraded ruleset alongside the fully playable Classic reconstruction.

## Design premise

Classic mode is predominantly a passive scene → mandatory fact disclosures → draw/play card → accuse loop. Director’s Cut adds **decisions during scenes, once-per-game individual abilities, group choices and a reason to replay** without making it possible to reveal other detectives' hands or the solution by inspecting page source. Scores reward activity, but **winning still depends on deduction**.

### 1. Scene Observation Challenge

- Every one of the five scenes carries a four-choice observation challenge.
- A targeted visual-detail caption appears *during playback* (about 8–25 seconds) and disappears. Players need to watch, not merely read the revealed scene transcript afterwards.
- Choices draw from truthful scene data: people’s keepsakes, room features or forensic traces. All are server-validated.
- Correct answers: **12 points**, plus **3 speed points** if submitted within 25 seconds of the scene starting. Incorrect answers cost no points.
- Exactly one submission per player per scene. Submissions and accuracy are private until the endgame scoreboard; the public TV sees only the participation count.
- Players are not forced to answer, and the host can still advance the scene; for a fair experience allow the full 42-second scene to play.

### 2. Detective Specialties

The detective chooses an ability before the first scene. This is not the secret character identity. Each is **once per case** and is activated through **Toolkit** after a scene (except while a scene is playing):

| Specialty | Server-validated effect |
|---|---|
| Eagle Eye | Privately inspect one as-yet-unreleased case-specific murder clue |
| Archivist | Draw one extra private clue card from the actual deck without consuming your ordinary turn |
| Interrogator | Privately receive a true character fact relating to another selected player |
| Analyst | Privately eliminate two false candidates for the selected answer dimension and death |

Private leads are never included in the projection of another detective or the public theater screen. **Six points** are awarded when an ability is successfully used.

### 3. Branching Group Decisions

After the second and fourth scenes, immediately after all players give their truthful character fact, a secret vote is opened:

- **Search the Archives:** publicly reveal two as-yet-unseen *corroborated alibi* clues.
- **Follow the Shadow:** publicly reveal one as-yet-unseen crucial murder clue from a later scene.

Each player gets one vote. The winner is determined by majority; ties favor the host's vote. All votes are kept hidden until resolution; only counts submitted are shown while the ballot is active. Each voter receives **4 participation points**. The choice changes information availability, not the predetermined answer or scripted dialogue. These are **evidence branches**, not alternate filmed story endings.

### 4. Private Hints

- Request a hint from Toolkit or the personal notebook; choose a death and answer category.
- The server eliminates two false candidates without revealing the actual answer directly.
- Two hints maximum per player per case; the same death/category cannot be requested twice.
- Each hint costs **8 points**. The fact remains private.

### 5. Suspense and Endgame

- A tension bar fills as the group advances scenes and resolves story choices.
- The ending screen shows a full points leaderboard: scene observations, specialties, voting, hints and a +50 victory bonus.
- Scores are **not** used to adjudicate who wins; original murder + hidden-identity victory conditions still apply.
- Public TV/projector view displays only public clues, phase and suspense: never hands, secret identities, private hints, observation accuracy or unrevealed solutions.

## Modes and defaults

- **Create a room in the web UI:** Director’s Cut is enabled by default.
- **Create through the backwards-compatible API:** Classic is the default unless `enhanced: true` is explicitly passed.
- Host can toggle Classic / Director’s Cut from the lobby before starting; mode locks upon starting.
- Classic mode does not add DECISION intermissions, observation tasks, hints or specialties, so preexisting gameplay and API clients remain functional.

## Engineering map

| Concern | Implementation |
|---|---|
| New authoritative rules and projections | `server/enhancements.py` |
| Integration with Classic turn machine | `server/engine.py` |
| Endpoint commands `configure`, `talent_select`, `observe`, `vote`, `talent`, `hint` | `server/app.py` |
| All new player screens, controls and scene cues | `web/main.js` |
| Responsive styling and public TV mode | `web/styles.css`, `web/theater.js` |
| End-to-end rule testing, permission tests and 18-case regressions | `tests/test_directors_cut.py` |
| Offline browser UI fixture renderer (no local server navigation required) | `tests/preview_mockups.py` |

## Production-quality limitations

- The scene “film” is a staged illustrated storyboard with subtitles and still imagery, not 1985 source footage or a new live-action film. The current observation tasks are an initial content pass, not a substitute for richer authored visual puzzle design.
- The illustrated scene stills were cropped from prior mockup references to remove nested interface elements. These are **temporary development art**, not licensed release assets.
- Group choices branch **which information is found first**. They do not change the murder outcome or story performances.
- The independent human playtest, production security, account/recovery, matchmaking, sound-design and accessibility work in `PRODUCTION_BACKLOG.md` still needs to happen before public release.
