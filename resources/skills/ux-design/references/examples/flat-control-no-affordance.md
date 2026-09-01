# A flat control that does not read as interactive

A settings page. Some rows can be changed, some are just facts.

## Before

Three rows, stacked, identical.

```
Units            metric
Daily target     2200 kcal
Version          1.4.2
```

Same colour, same weight, no border, no chevron, no hover. Two of them open an
editor when clicked. The third does nothing.

The end user finds out which is which by clicking. That is the whole defect.

## After

The two changeable rows get the `field` surface, which is the lightest thing on
the page, a chevron on the right, and a hover state. Version stays plain text
in `muted`, left where it is, with nothing suggesting you can press it.

```html
<button class="row row-editable">
  <span class="row-label">Daily target</span>
  <span class="row-value">2200 kcal</span>
  <span class="row-chevron" aria-hidden="true">&rsaquo;</span>
</button>

<div class="row row-static">
  <span class="row-label">Version</span>
  <span class="row-value muted">1.4.2</span>
</div>
```

```css
.row-editable { background: var(--field); cursor: pointer; }
.row-editable:hover { background: var(--surface); }
.row-static { background: transparent; }
```

## Why

Principle 5. On a view that is one kind of thing, context carries affordance
and a plain row is fine. Kalori's result list is exactly that, every row is a
food, and none of them need a border to say so.

This view mixes kinds. The moment it does, each control has to look
interactive on its own, and nothing that is not interactive may look like it
is.

## Carry this

Ask whether the view is one kind of thing. If yes, plain is fine. If no, plain
is a guessing game.
