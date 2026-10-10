# Production backlog and decision log

## Scope boundary

The supplied UX references and reconstruction spec describe the historical **Clue VCR Mystery Game**, but do not provide a licensed original video asset, the complete original clue card text, or all of the original case solutions. This project therefore ships an **original playable adaptation with 18 internally consistent puzzles**. It is a functional game, not a representation that the original puzzles were completely recovered.

## Priority 0: pre-release security and stability

1. Production HTTPS, trusted-host and origin policy, load/stress tests, command rate limiting and abuse handling.
2. Database migrations, backups, game-room TTL, operational dashboards and secrets lifecycle/rotation.
3. Player connection/readiness status, host handover and player timeout/resume policies.
4. End-to-end browser and multi-device test suite, including TV and mobile views; this execution environment blocked direct localhost Chromium navigation. Offline Chromium UI fixtures render without JavaScript errors, but a real hosted multi-device browser playthrough is still pending.
5. Accessibility audit: reduced motion, keyboard-only game operations, focus management, labels and responsive text.

## Priority 1: faithful scene and game polish

1. Replace storyboard slide playback with original licensed media **or** newly produced animation, synchronized scene timecodes, voice and subtitles.
2. Add a separate host controller panel so a projector screen never shows private UI while advancing scenes.
3. Distinguish action-card replay mechanics from ordinary scene review and add synchronized seeking/confirmation.
4. Add audio cues, atmospheric transitions, card animations and visual clue bookmarking.
5. Add a complete authoring GUI for scenes, cases, character facts and card overlays; current pack is editable Python content.

## Priority 2: deeper case design

1. Human writer pass on all case stories and clues to improve mystery plausibility, pacing, and suspects' motives.
2. Add semantic linkage constraints that require multi-card inference rather than four clues each directly implying one answer dimension.
3. Have independent playtesters validate each case without seeing its solution; automated integrity checks are not a substitute for puzzle design testing.
4. Upgrade the two newly implemented private hints into adaptive, difficulty-dependent assistance, and add an explainer timeline after a case ends.
5. Support locale packs and case-author QA preview.

## Decisions for the product owner

- Do you want an **archival recreation** using rights-cleared 1985 footage/card text and exact solutions, or the **new original adaptation** currently shipped?
- Should there be an AI detective / solo variant? It requires separate fairness and information-hiding rules.
- Should the application be public hosted, LAN-first, or deployed to a private team event?
- Is commercial use intended? If so, finalize rights, trademarks and likeness clearances before marketing.
