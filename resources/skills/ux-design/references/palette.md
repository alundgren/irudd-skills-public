# Palette and type

Load this for any colour, surface, contrast, or typography decision.

Two halves. The derivation rule is the identity, and it travels to any app. The
role table is one worked instance of the rule, ready to paste. An app that
needs different values should re-derive from the rule rather than nudge these
hexes around, and it will still look like family.

## The derivation rule

1. **Hue anchor 25.** Every neutral, background, surface, border, muted text,
   sits on hue 25 or within a few degrees. That is what makes the greys warm
   without anyone choosing a warm grey.
2. **Saturation 20% to 26% below 75% lightness.** Above 75% lightness go up to
   60%, where saturation reads as warmth rather than as colour.
3. **Supporting hues near 105 and 200.** Sage and greyed blue, a third and two
   thirds of the way round from the anchor. Spread, not clustered. The shared
   saturation ceiling is what makes them one family instead of three unrelated
   colours.
4. **One saturated accent, hue 33 at 44% to 52% saturation.** That is the
   accent budget for a whole screen.
5. **Roles separate by lightness, never by saturation.** Background, surface,
   raised, and border are four steps 4 to 5 lightness points apart on the
   anchor hue.
6. **Primary text at 7:1, plus or minus 0.8.** Get there by moving lightness
   apart, never by heading for white or black. Secondary text 4.5:1 or better,
   and only for genuinely secondary information.

Nothing is pure. No white, no black, no primary colours. Every colour should
have an object behind it: soil, sage leaf, pear, water, dusk.

## Roles: warm paper

The settled ground. Warm paper at 91% lightness, not white.

| Role | Hex | H | S | L | On bg | Use for |
| --- | --- | --- | --- | --- | --- | --- |
| bg | `#F2EADE` | 36 | 43% | 91% | - | Page background |
| surface | `#EADFCD` | 37 | 41% | 86% | - | Panels, alternating rows |
| raised | `#E0D2BD` | 36 | 36% | 81% | - | Headers, the layer above a panel |
| line | `#C1AF9A` | 32 | 24% | 68% | - | Borders, rules, dividers |
| field | `#F9F6F0` | 37 | 45% | 96% | - | Inputs, the place to act |
| text | `#604939` | 25 | 25% | 30% | 7.0 | Primary text |
| muted | `#66574D` | 25 | 14% | 35% | 5.8 | Secondary text only |
| accent | `#784F26` | 30 | 52% | 31% | 6.0 | The one accent |
| link | `#3D5D71` | 203 | 30% | 34% | 5.9 | Links |
| ok | `#3D6034` | 108 | 30% | 29% | 6.0 | Success |
| warn | `#7E5220` | 32 | 60% | 31% | 5.7 | Warning |
| danger | `#8F3A2D` | 8 | 52% | 37% | 6.3 | Destructive actions |

Every role clears 4.5:1 on bg, surface, and raised.

Note the direction of the field colour. Inputs are the *lightest* surface on
the page, above the background, not a sunken well. On a search-first app the
field is where you act on every visit, so it reads as the brightest thing.

## Using it

- Show the roles the screen actually needs. A page is not a swatch board.
- Depth comes from one lightness step, not from a border plus a shadow plus a
  tint. Alternating table rows are one step, no colour change.
- The accent is a budget, not a palette. One saturated thing per screen.
- Soft corners. Sharp edges read as harsh next to these colours.
- Do not reach for grey. There is no grey here, the neutrals carry hue 25.

## If an app needs a dark ground

Derive it, do not invent it. Start from background `#292019` at 13% lightness,
which holds four clear surface steps and a working accent, and keep primary
text near 66% lightness so it lands at about 7:1 rather than running to 15:1.

A ground in the middle does not work. Brown at 25% lightness leaves the ramp
no room, forces everything else above 60% lightness to stay readable, and the
screen drifts pale and muddy. That was tested and rejected.

## Type

Same idea as the colour half. The rules are the identity, the numbers are one
worked instance.

### Faces

IBM Plex Sans for text, IBM Plex Mono for anything monospaced. Warm and
functional without being characterful.

Licensed under the SIL Open Font License 1.1, copyright IBM Corp. Free to use,
embed, modify, and redistribute, commercially or not. The two conditions do not
bite here: the fonts may not be sold on their own, and "Plex" is a Reserved Font
Name so a modified copy has to be renamed. Ship the OFL text alongside the font
files when self hosting.

Self host it. If an app cannot carry font files, an overlay, an offline tool,
anything where an external request is wrong, fall back to the system UI stack
and the system monospace. Do not load a webfont from a third party CDN.

A serif is allowed for the reading archetype, and only there. Nowhere else.

### Scale

A starting point on a desktop viewport, not a floor and not a ceiling. An
overlay read from a couch, or a phone used outdoors, needs more.

| Role | Size | Weight | Notes |
| --- | --- | --- | --- |
| Body | 16px / 1.6 | 400 | The base. Most text is this. |
| Page title | 28px to 40px, fluid | 600 | Letter spacing -0.015em |
| Section | 22px | 600 | Letter spacing -0.01em |
| Subsection | 17px | 600 | |
| Secondary | 13.5px | 400 | `muted` colour, genuinely secondary only |
| Label | 11px to 12px | 500 | Mono, uppercase, letter spacing 0.07em |

### Rules

- **Three weights, 400, 500, 600.** No 700 and above, it reads as shouting
  against these colours. No 300 and below, it fails the contrast intent.
- **Get hierarchy from weight and space before you reach for size.** A six step
  size ramp is a sign the page has too many levels.
- **Weight follows frequency of use**, same as everything else. The number the
  task needs gets 600. The timestamp nobody reads does not.
- **Tabular numerals for any number an end user compares or scans.** Table columns,
  totals, counts. `font-variant-numeric: tabular-nums`.
- **Mono for anything compared character by character.** Hashes, versions, ids,
  hex values, file paths, anything copied and pasted. Not for prose, and not as
  decoration.
- **Prose lines cap around 62 to 75 characters.** Use `ch`, not pixels.
- **Negative letter spacing only above about 22px. Positive only on small
  uppercase labels.** Never touch body text.
- **Primary information never drops below the base size.** Secondary can, and
  that is the only thing that can.

## Where these came from

The anchor is Sherwin Williams Grounded, SW 6089, `#785B47`. It is the hue
anchor, not a surface. The supporting hues come from the same Natural Elegance
set: Napery, Easy Green, Antler Velvet, Agate Green, Bosc Pear, Smoky Blue.
The family keeps neutrals warm while leaving room for sage, blue, and one pear
accent.

Before a phone-first app adopts the palette, check the real screen outdoors on
a phone. Desktop contrast measurements do not cover that context.
