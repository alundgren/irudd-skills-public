# Worked examples

Before and after pairs. A bad screen next to its fix, with the reason, teaches
judgement better than a swatch grid does. Each pair is small so loading one is
cheap.

Load one pair, not the folder.

## The pairs

| File | The failure it shows | Principle |
| --- | --- | --- |
| `add-with-no-undo.md` | A screen adds a thing and never shows or removes it | 7 |
| `dangerous-looks-safe.md` | Delete styled exactly like redeploy | 7, 4 |
| `flat-control-no-affordance.md` | Editable and static rows look identical | 5 |
| `silent-system-change.md` | The system acts and leaves no trace | 7 |
| `one-view-many-jobs.md` | One page serving three different goals | 2, 1 |
| `built-for-short-text.md` | Widths set against demo data, not real data | 10 |
| `decoration-as-hierarchy.md` | Boxes and pills doing hierarchy's job | 6, 4 |
| `uniform-row-controls.md` | Row metadata styled by category, not by use | 4 |

Principle numbers are the numbered list in `SKILL.md`.

## Two files that are not pairs

`gallery.html` renders every pair, before next to after, on one page. It is for
a person who wants to look at them. Do not load it as context, load the pair's
markdown file instead. The markdown carries the guidance, the gallery carries
the pictures.

`kalori-restyle.html` is the reference screen, not a before and after. See
below.

## Keeping the gallery in sync

Write the markdown file first, then add its section to `gallery.html`. If the
two disagree, the markdown is authoritative because that is what agents read.
Keep gallery sections small enough to compare directly with their source file.

## kalori-restyle.html

Open it in a browser. The live original at `kalori.irudd.net` is the before: a
Bootstrap boilerplate list on white, with correct information design
underneath. That combination is what makes it useful. The restyle proves the
palette without changing a single structural decision.

What changed:

- The number carries weight, 600 and tabular. It is the one thing the task
  needs, so it gets the weight. Frequency of use, applied.
- A "kcal / 100 g" column label. The only structural change on the screen, and
  the only thing an end user has to be told.
- Alternating row tint instead of a grey stripe. One lightness step, no colour
  change.
- The search field is the lightest surface on the page, 96% against a 91%
  ground. It is used on every visit, so it reads as the place to act.

What deliberately did not change: row order, the bolded matched substring, one
number per row, right aligned. It was already right.

The file renders the whole role table as swatches for review. A real page shows
only the roles it needs.

## Adding a pair

When something comes out weird in a real app, add a pair. This library is meant
to grow from real mistakes, not from invented ones.

Keep the shape the existing files use. One screen, a plausible before, the
fix, the principle it lands on, and one line to carry away. Around fifty lines.
Then add the gallery section.
