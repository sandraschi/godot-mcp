# Vibecoder Runner — Game Concept

A 2D side-scrolling runner where you play as a vibecoder (headphones on,
energy drink in hand, 12 terminals open) fighting through the AI underworld.

## Enemies

| Enemy | Behavior | Visual |
|-------|----------|--------|
| **The Hallucinator** | Teleports randomly, spawns fake power-ups that are actually traps | Glitchy, flickering polygon with hallucination particles |
| **The Prompt Injector** | Hacks your controls — every 5s it swaps a key binding | Green matrix-styled text streams from it |
| **The Tokenmaxxer Bankruptor** | Slow but huge — eats your score. Must dodge not fight | Bloated, moneybag-shaped with counter ticking up |
| **Context Window Overflow** | Wall-like enemy that shrinks your playable area | Closing brackets `]` from both sides |
| **Merge Conflict** | Splits into two copies on death unless you "resolve" them | Red and blue ghost-like duplicates |

## Player

- Vibecoder with laptop, headphones, slippers
- Moves with arrow keys, space to "deploy fix" (attack)
- Score = lines of code written
- Collects "energy drinks" for score multiplier
- "Ship it!" button clears all enemies (limited use, 3 per game)

## Visual Style

- Dark terminal theme (green text on black)
- Procedural visuals only — no external assets
- ASCII/tech aesthetic where possible
- Enemies made of colored polygons and text characters
- Particles for code effects

## Narrative

You're shipping a critical feature at 3 AM. The AI tools keep hallucinating,
injecting, bankrupting. Each level is a sprint to the "merge button."
