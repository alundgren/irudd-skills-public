# Why the principles exist

Load this when a deviation or review disagreement needs the reason behind a
principle. For ordinary UI work, the rules in `SKILL.md` are enough.

## Build for tasks, not for data

People never use data without a goal. A nutrition database may contain hundreds
of fields, but a cooking tool may need one comparable calorie value per food.
A crowded database-shaped screen is usually a product-model problem, not a
spacing problem. Name the task first, then show the information it requires.

This principle stops at domain modeling. If ambiguous food names require a
better data model, hand that problem to the technical owner.

## Measure cognitive load

Item counts do not measure difficulty. Several easy choices can share a page,
while one demanding decision may need the page to itself. Split a flow when the
split reduces what someone must understand at once. Do not split when it only
adds navigation.

The same reasoning applies to font and control sizes. Test the real context
instead of treating one fixed number as universally correct.

## Weight by frequency of use

Controls that share a row do not deserve equal emphasis. On a list of articles,
opening the article and reading comments are common actions. Hiding an item is
rare. Styling them alike makes a low-value control compete with the task.

Ask how often someone wants each action. Category and data type are poor
proxies for importance.

## Let context carry affordance when it can

A plain button can work on a page containing one question and one obvious next
step. The same styling fails on a mixed dashboard where controls and static
content sit together.

Judge affordance at the view level. A single-purpose view can provide enough
context. A mixed view requires controls to look interactive by themselves.
Static elements must not resemble controls.

## Make hierarchy predictable

Before clicking, a person should be able to predict what will change. That
prediction should hold throughout the app. Borders, cards, and nesting do not
create hierarchy when the underlying relationships remain unclear.

Controls must also read as connected to what they affect. A heavy unrelated
section between filters and results weakens that relationship.

## Write like a colleague

Explain what the product does in the same plain language used with a colleague.
Sales language is appropriate only when an actual sale is taking place.
Manufactured urgency, scarcity, and obstructive interstitials make the product
adversarial.

This positive test covers more cases than a growing list of banned phrases.
Run `unslop` over user-facing copy as a final check.

## Use warmth without sacrificing clarity

The house palette is warm and muted because it should suggest paper, soil,
plants, water, and dusk rather than office software or a clinical room. Brown
as the anchor also avoids the common near-black, grey, and bright-accent look.

Warmth and low saturation matter more than whether the ground is light or dark.
The default is warm paper. Apps that need a dark ground should derive one using
the same hue and contrast rules.

## Build contrast through lightness

Muted colours remain readable when their lightness values are far enough apart.
Primary text targets roughly 7:1 without moving to pure black or white.
Secondary text may use lower contrast only when losing it would not block the
task.

## Name the two recurring failures

The old Bootstrap look uses uniform grids, thin grey rules, and equal styling
regardless of importance. The cards-and-pills look puts each element on its own
floating surface. Both use decoration instead of hierarchy.

The names are shorthand. The lasting tests are whether layout carries the
hierarchy and whether visual weight follows the task.

## Keep the guidance advisory

These apps include reading sites, data-entry tools, search pages, management
screens, phone apps, and overlays. One mandatory component or token system
would fit some and distort others. Apply the principles, record justified
deviations in `ux.md`, and avoid relitigating them later.
