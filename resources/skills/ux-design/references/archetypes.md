# Archetypes

The principles in `SKILL.md` apply to every archetype. This file says which
ones need extra weight and which can relax.

## Reading and content

A blog, recipe pages, anything where the end user came to read.

- Line length and rhythm matter more than density. Give text room.
- This is the one archetype where a serif is allowed. See `palette.md`.
- Navigation stays minimal. One clear path, not links pointing everywhere.
- Frequency-based weight applies hard: the thing they came to read outweighs
  every chrome element on the page.

## Data entry

Forms, logging, anything where the end user is putting something in.

- Cognitive load is the binding constraint. Split when splitting lowers load.
  A hard question earns its own page.
- Design for real input limits, not the shortest plausible value.
- Consequences visible: after saving, the end user sees what now exists.
- Affordance relaxes on a single-question page. The one button is obvious.

## Search and lookup

Type a thing, get the thing. The calorie app is the model.

- The field is the brightest surface on the page and the first thing the eye
  lands on.
- Show what the task needs per result, not everything known about the result.
- Results and the controls that filter them must read as connected. No heavy
  unrelated band between them.
- Density can go higher here than anywhere else, because the page is one kind
  of thing. It still should not go as high as it can.

## Admin and control

Dashboards, management panels, anything with dangerous buttons.

- Safe and dangerous actions must look different. This is where it matters
  most.
- Hierarchy predictability is the usual failure. Do not stack boxes to imply
  structure.
- Resist the dashboard reflex of surfacing every stat. Name the tasks an
  operator actually performs.
- System-initiated changes get the same visibility as user-initiated ones.

## Overlay

The Last Epoch overlay, and anything drawn on top of something else.

- The host application owns the screen. The overlay is a guest, and it takes
  the space it needs and no more.
- Readability against an unknown, moving background is the hard problem.
  Contrast against the palette is not enough on its own.
- No dark or light mode logic here either, but the ground may need to differ
  from the warm paper default. Derive it, see `palette.md`.
- Interaction is often glance-only. Assume the end user is busy doing something
  else.
