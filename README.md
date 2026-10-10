# Mystery Tapes: The Manor Files — Director’s Cut (v2.0)

**A runnable, multiplayer, video-driven deduction game based on the UX exploration and reconstruction brief for the 1985 Clue VCR Mystery Game.**

This is a complete original *playable adaptation*, not a reproduction of the copyrighted 1985 film and its unrecovered casebook. The 18 cases in this package have newly authored/generated, internally consistent solutions, the scenes are new timed illustrated storyboards, and no original VHS/audio footage or archival case-answer text is bundled. The original character names are used for reference in this private prototype. Obtain appropriate IP permissions before commercial release or replace the names and brand.

## Quick start (Python)

1. Install Python 3.11+ (recommended). The server annotations have also been patched for Python 3.9; this has been syntax-checked but not separately runtime-tested under 3.9.
2. Open a terminal in the `clue_rebuilt` directory.
3. Run:

   ```bash
   python -m pip install -r requirements.txt
   python run.py
   ```

4. Open **http://localhost:8000** in a browser on the host computer.
5. Choose **Create new room**, enter your detective name, and send the five-character code to 1–5 other people.
6. Players join from **http://HOST_COMPUTER_IP:8000** on the same network, using their own phone or laptop. Replace `HOST_COMPUTER_IP` with the actual LAN address of the computer running the server.
7. Choose any of 18 cases, pick a detective specialty (or switch to Classic), start, and follow the prompts.
8. For a safe TV/projector view, the host opens **Open TV / theater display** from the film screen, or visits `http://HOST_COMPUTER_IP:8000/theater?code=ABCDE` using the actual code.

**Two people on a single device is not a supported competitive mode** because hands and identities must remain private. Use two separate browsers/devices (different browser profiles work).

### Alternative: Docker

```bash
docker compose up --build
```

Open http://localhost:8000. The Docker Compose file persists game rooms in a local `./data` folder.

### Run the tests

```bash
python -m pytest -q tests/test_engine.py tests/test_api.py tests/test_directors_cut.py
node --check web/main.js
node --check web/theater.js
```

Node is required only for the optional JavaScript static checks, not for playing.

To regenerate **offline Chromium UX screenshots**, install Playwright and Chromium separately and run `PYTHONPATH=. python tests/preview_mockups.py`. This uses live state fixtures, but not a network browser playthrough.

## New in Director’s Cut (v2)

**The web game now creates Director’s Cut rooms by default.** The host may switch to Classic at any time before starting, retaining the prior game rules. Director’s Cut adds:

- **Spot-the-detail micro-challenges:** every scene shows a timed clue flash and four-choice observation puzzle, worth up to 15 points; submissions are private and one attempt per detective per scene.
- **Four detective specialties:** Eagle Eye, Archivist, Interrogator and Analyst. Choose one in the lobby; use it once during the case from the **Toolkit** tab.
- **Two majority-vote group forks:** after scenes two and four, each player secretly votes to unlock extra archived alibis or an early murder clue. The choice actually changes public evidence.
- **Personalized private hints:** two per player; eliminate two false candidates in a selected category at an 8-point cost.
- **Tension meter and final scoreboard:** scoring for attentiveness and activity, with a winner bonus; the winner is still determined by actual murder and identity deductions, not points.
- **A Director’s Cut public theater:** the group sees suspense and the vote count, but never private answers, hands, specialty intelligence or secret identities.
- **Polished scene stills:** original screen mockup imagery cropped to show only the cinematic subject during playback (interim art).

See **`docs/DIRECTORS_CUT.md`** for a complete design and technical explanation.

## What is playable now

- **18 distinct cases**, six per chapter. Case difficulties range from 1 to 5 linked murders.
- **Three tape chapters**, each with five illustrated scenes (15 unique scenes total).
- **28 chapter clue cards**, each resolving to one of six case-specific facts (84 physical clue IDs across three chapters; 504 case-specific entries).
- **10 secret character identities**, never transferable, plus unassigned-character cards.
- **18 investigation cards** in the active game deck, including steal, give, force a public reveal, bury, force a personal fact and replay.
- **Real multiplayer (2–6 human players)** with a room code; secure-by-default private state projections, WebSocket revision notices and polling fallback.
- Five-card initial deal; held-investigation-action priority; immediate play of a drawn investigation card; shared evidence; a discard pile that can be reshuffled.
- Required truthful personal-fact disclosure between scenes; forced target responses; investigation turns and action resolution.
- Personal detective notebook with suspect/victim/room/weapon elimination marks and saved free-form notes.
- Multiple murder chain builder; server-only accusation scoring; elimination after a wrong murder answer; final opponent-identity challenge round; victory and postgame solution reveal.
- Standalone read-only **public theater screen**, containing no private cards, private notebooks or live identities.
- SQLite persistence for rooms and gameplay, so a browser can refresh and resume from its saved room/token.
- Responsive desktop and phone interfaces, with design treatment based on supplied mockups.

## Important gameplay instructions

The host chooses a case in the lobby and starts the round. Every player receives a private identity and five cards. The host then starts the first scene. The illustrated scene lasts approximately 42 seconds and shows three changing script beats. **The host must explicitly select “Finish scene & reveal evidence” to advance.** This releases case-relevant shared evidence and begins a required truthful personal-fact round.

Each detective reveals one authored truthful fact about their own identity. Once everyone has responded, the investigation turn begins. On your turn, **you must play an investigation card if you hold one**. Otherwise, draw a card; drawn investigation actions must be played immediately. Cards may trigger a target player's mandatory response.

When everyone has taken a turn, the host can play the next scene. After scene five, the action rounds continue until someone solves the case or all eligible players are eliminated. Accusations are available on your eligible investigation turn after at least two scenes have been viewed. To win outright, name every murderer/victim/room/weapon chain **and** every opponent's secret character. If you solve the murders but miss an identity, everyone else gets one final opportunity to steal the win; otherwise your original claim stands.

### How deduction works

Each numbered death has four clues, referring indirectly to a murderer’s distinctive garment/ornament, a victim’s keepsake, a room’s recognizable feature and a weapon’s trace. Five scenes reveal the corresponding people, keepsakes, rooms and traces. By scene five, all essential murder clues have entered the public log; private cards can provide earlier insight and investigative advantages. The automated content-consistency test checks that every answer has exactly one matching candidate for all four dimensions.

## Technical architecture

| Layer | Location | Responsibility |
|---|---|---|
| UX / layout | `web/styles.css` | Responsive component system inspired by parchment, brass, noir and VHS mockups |
| Front-end app | `web/main.js`, `web/index.html` | Player views, private cards, interaction/turn forms, notebook, accusations |
| Shared theater | `web/theater.html`, `web/theater.js` | Public-only film, evidence, events, roster |
| Game rules | `server/engine.py` | Pure authoritative state transitions, scoring, hidden-information projections |
| Content | `server/content.py` | Chapters, scenes, 10 identities, 18 original cases, generated clue overlay matrix |
| API and persistence | `server/app.py` | FastAPI endpoints, room tokens, SQLite room persistence, WebSocket notifications |
| Launch | `run.py`, `Dockerfile`, `docker-compose.yml` | Local/LAN/hosted startup |
| Verification | `tests/` | Cases, privacy, state transitions, multi-client HTTP playthrough, challenge round |

### Endpoint contract

- `GET /api/catalog` — public chapters, cases, people, rooms and weapons; no hidden answers.
- `POST /api/rooms` — create room and private player token.
- `POST /api/join` — join existing room, receive private token.
- `GET /api/rooms/{code}` — authenticated private player projection; `X-Player-Token` header.
- `POST /api/rooms/{code}/command` — authenticated action, validated by server.
- `GET /api/rooms/{code}/public` — public theater projection; no hidden facts or solution before game end.
- `WS /api/ws/{code}?token=...` — private authentication; pushes **revision number only**. Clients retrieve personalized snapshots via HTTP.
- `GET /theater?code=...` — safe TV interface.

The app exposes OpenAPI documentation at `/api/docs`.

### Saved state

The room record, including the private identity/hand data, is stored in `game.sqlite3` (created at first use), or whatever path `MYSTERY_DB` specifies. Treat this as private game data. A player's device stores only its personal room code and token in `localStorage`. Do not share browser profiles with other players. The server must not be exposed to the public Internet without TLS, rate limiting, durable managed storage, operational monitoring and access controls.

## Limits / not yet present

- Original VHS film, original 18 case solutions, original full casebook and copyrighted scripts are **not** supplied. The game is complete with its **new 18 case pack**, not an authenticated facsimile of every original case.
- Scenes are illustrated timed storyboards with dialogue and timed visual detail cues, not new filmed actors or lip-synced animated videos. Host controls progression. No original audio is bundled.
- No computer-controlled detective/solo mode. Multiplayer requires 2–6 people; browser tabs in separate profiles can substitute for physical devices during evaluation.
- No accounts, public matchmaking, voice chat, player kick/host migration or payment system. Reconnection works on the original browser/token.
- The current UI is a coded responsive implementation based on visual mockups, not a pixel-perfect extraction of them. Direct browser navigation to a localhost server is blocked in this execution environment. Offline Chromium UI fixtures have been rendered without page JavaScript errors; engine/API/security checks and JavaScript syntax checks passed. A real multi-device browser playthrough is still required.
- Commercial deployment needs additional security review and IP/licensing decisions, plus UX and accessibility audits on real devices.

Read `docs/WORKSTREAMS.md` for the role-specific development breakdown and `docs/PRODUCTION_BACKLOG.md` for the next iteration.
