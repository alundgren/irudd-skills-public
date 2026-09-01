# The per-app `ux.md`

Optional. An app that has one records how it applies this guidance and, more
importantly, where it does not and why. Its job is to stop a reviewer from
relitigating decisions that were already made on purpose.

Keep it short. It gets read often, so it costs context every time.

Put it where the app's other docs live. Write the first draft when a UI task
first touches the app, then keep it current as decisions get made.

## Template

```markdown
# UX notes for <app>

**What it is for.** One or two sentences. The task the app exists to serve,
not the data it holds.

**Where it is used.** Phone, laptop, big screen, on top of a game. Anything
that changes readability judgements.

**Archetype.** One of reading, data entry, search, admin, overlay, or none.

## Palette

Ground: <light warm paper | derived dark | other>. If derived, say from what.

| Role | Value |
| --- | --- |
| bg | |
| surface | |
| text | |
| accent | |

Only the roles this app actually uses.

## Type

Family, and the sizes in use with what each is for. Say why if the app needed
larger or smaller than feels normal.

## Components

The named pieces this app has, one line each. Enough that an agent adds to
the set instead of inventing a parallel one.

## Deviations

Each one as: what we do differently, and why. This section is the point of
the file.
```

## Rules for filling it in

- Deviations without a reason are not deviations, they are drift. Write the
  reason or fix the code.
- Do not restate the guidance. Only what is specific to this app.
- No aspirations. Record what the app does today.
