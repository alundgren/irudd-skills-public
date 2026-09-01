---
name: ux-design
description: House UI and UX guidance for designing and reviewing anything a person sees or clicks. Use for screens, pages, views, forms, layouts, navigation, states, user-facing wording, visual design, and complete flows. Load `code-guidance` too for a change or review with both user-facing and technical behavior. Do not use for API design, database schemas, module boundaries, file formats, config keys, or CLI flags on their own.
license: MIT
---

# UX design guidance

Shared UI and UX preferences for small apps used by their author and a small
circle. The guidance is advisory. Deviate when an app needs something different
and record the reason in its `ux.md`.

## Decision ownership

`ux-design` decides what the end user sees and clicks. It does not decide API
design, data structures, database schemas, module boundaries, dependencies, or
implementation structure. When a technical decision creates a bad experience,
name its practical interface cost, such as duplicate entry, lost progress, an
extra wait, a misleading state, or an unnecessary control. Leave the technical
correction to `code-guidance`.

## Principles

1. **Build for tasks, not for data.** Name the task the end user is doing, then
   show what that task needs. "The data is genuinely that big" is not a defence
   for a crowded screen, it means the screen has no task behind it. A calorie
   app exists to hit a number while cooking, so it shows one number per food,
   not every nutrient.

2. **One view, one job.** Many focused views beat few multi-purpose ones.
   Anything secondary on a page has to earn its place by serving the primary
   job. Model by the goal, not by what data exists.

3. **Cognitive load is the measure, not item count.** The end user should only
   have to hold a reasonable number of things at once, and how many that is
   depends on how hard the task is. Easy choices can share a page. A hard one
   gets the page to itself. Splitting is right when it lowers load and wrong
   when it just adds steps. Wizards are endorsed for hard or multi-step tasks.

4. **Visual weight follows frequency of use.** Style by how often someone wants
   the thing, never by what category of metadata it belongs to. The common
   destination gets the weight, the rarely used control gets less, even when
   they sit in the same row and belong to the same "type".

5. **The end user must know what is interactive.** On a view that is one kind of
   thing, context can carry it and a plain control is fine. The moment a view
   mixes kinds, controls have to look interactive on their own. Nothing
   non-interactive may look clickable.

6. **Hierarchy has to be predictable.** An end user should be able to guess what
   changes before clicking, and the answer should be the same everywhere in the
   app. Nested boxes are not hierarchy. When a box is doing the hierarchy work,
   the layout is wrong.

7. **Consequences stay visible and reversible.** If something can be added, it
   can be seen and removed, unless removal is genuinely impossible. It must not
   matter whether the system acted or the end user acted, either way the end
   user sees what happened and why. Make safe and dangerous actions look
   different, in the spirit of GitHub's destructive-action styling.

8. **Self-explanatory beats explained.** Things do what you would guess. Prefer
   no text over good text. Documentation must never paper over a bad workflow.

9. **Write like a colleague, not a salesperson.** Explain what a thing does
   without manufacturing urgency or pressure. Selling is fine when there is an
   actual sale. Countdown timers, false scarcity, and interstitials that argue
   back are not. Run `unslop` over user-facing copy.

10. **Respect eyes and context.** Consider where the app is actually used,
    phone, laptop, big TV, and do not overindex on cramming. No fixed minimum
    sizes here, it is a judgement per app. Design against real text limits, not
    the shortest string you can imagine.

## Review a complete experience

For a task-scoped review, judge the screen or flow as one experience before
commenting on visual details.

- Name the end user's task. Does the change let them complete it?
- Check the full path through the task. Look for missing entry points, states,
  errors, recovery actions, and ways to cancel, leave, or undo.
- Test the design against realistic content and conditions, including empty
  results, long text, large result sets, delayed responses, and invalid or
  partial data when they apply.
- Remove controls, settings, and information that do not help with this task.
- Check whether one screen is combining tasks that need different actions or
  information.
- Read the app's `ux.md` when present. Treat a recorded decision with a reason
  as settled. Apply the house defaults when there is no `ux.md`.
- Raise a technical decision here only when it creates a named interface cost,
  such as duplicate entry, lost progress, an extra wait, a misleading state,
  or a control the end user should not need.

Rank findings by their consequence for the task. A missing recovery path or
unclear primary action matters more than a spacing inconsistency. Cite
checkable evidence such as a screen element, state, interaction, screenshot,
or source location. Separate blocking findings from suggestions. Give a
concrete correction for every objection. Do not report source formatting or
choices enforced by tooling. Layout and spacing remain reviewable when they
affect the task.

## House style

Warm, calm, low key, and plain. Earth tones. Soft edges over sharp ones. The
target is a garden, not a hospital room, and not an office building either.

Contrast comes from distance in lightness, with both colours kept muted. Never
from saturation, and never by heading toward pure white or pure black. Primary
text around 7:1. Low contrast is allowed for genuinely secondary information
and never for primary.

Type is plain and quiet too. Three weights at most, hierarchy from weight and
space before size, monospace only for things an end user compares character by
character. Weight follows frequency of use, same as everything else.

For any actual colour, type, or surface decision, load `references/palette.md`.
Do not invent muted browns from adjectives, and do not invent a type scale.

### Two looks to avoid

Stated as the failure first, the name second, because the names will date.

- **Decoration standing in for hierarchy.** Uniform grid, thin grey rules,
  white page, everything styled the same regardless of importance. Old
  Bootstrap.
- **Every element on its own floating surface.** Stat cards in bordered boxes,
  pills, boxes nested inside boxes, near-black plus grey plus one bright
  accent. The house style current AI tools default to.

## Working rules

- Prefer responsive for anything on the web.
- Icons over text when the intent stays obvious. Text when it does not.
- English only. No translation i18n. Date and number formatting can still
  matter.
- Screenreader support when it is cheap. No major sacrifices for it.
- One style per app. No dark and light mode, no theming, unless a specific app
  genuinely calls for it.

## References

Load only what the task needs.

| File | Load it when |
| --- | --- |
| `references/palette.md` | Any colour, surface, contrast, or type decision. Has the derivation rule, the role table with real hex values, and the type scale. |
| `references/archetypes.md` | The app has a clear archetype, such as reading, data entry, search, admin, or overlay, and you want to know which principles sharpen or relax. |
| `references/ux-md-template.md` | Writing or updating an app's `ux.md` adoption record. |
| `references/rationale.md` | You want to deviate from a principle, or you are arguing a review point and need the reasoning behind a rule. |
| `references/examples/` | You want a worked before and after. Start with the README. |

## Deviation

Deviating is allowed and expected. Record it in the app's `ux.md` with the
reason, so nobody relitigates it later. An app with no `ux.md` is fine too, it
just means the defaults apply.
