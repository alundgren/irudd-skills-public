# A screen built for three-character text

A food search result list. Type a name, get calories per 100 grams.

## Before

Built and demoed against `Egg`, `Milk`, `Rice`. Name on the left in a fixed
width, number on the right, one line per row, nothing wraps.

Then the real data arrives.

```
Chicken breast, skinless, bo…   114
Egg                             155
Crème fraîche 34% fat, organ…   340
Crème fraîche 15% fat, organ…   165
```

The names get cut before the part that tells them apart. Those last two now
read as the same product with two different numbers. On a narrow phone the
number wraps under the name and the column stops being a column.

Nobody designed this. It was laid out against the shortest string anyone could
imagine, and the shortest string is never the one that breaks it.

## After

Pull the longest real value out of the data before setting any width.

The number column is sized to its widest value, tabular, and never moves. The
name gets the rest and is allowed to wrap to two lines, so the row grows
instead of the text disappearing.

```css
.row       { display: flex; gap: 16px; align-items: baseline; }
.row-name  { flex: 1; min-width: 0; }
.row-kcal  { font-variant-numeric: tabular-nums; text-align: right;
             flex: 0 0 auto; }
```

Where truncation is genuinely unavoidable, cut in the middle. The tail is
usually what tells two entries apart.

## Why

Principle 10, design against real text limits, not the shortest string you can
imagine.

Principle 1 is underneath it. The name is what the task needs to pick the right
food. Losing the end of it loses the task.

## Carry this

Before you set a width, run the query. Lay out against the longest real value,
plus room, not against the demo data.
