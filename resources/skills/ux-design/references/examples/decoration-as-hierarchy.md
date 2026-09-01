# Decoration standing in for hierarchy

A training app's home screen. You open it to see whether you have trained
today.

## Before

Four stat cards in a row. Each in a rounded box with a border and a soft
shadow, each with a small uppercase pill above the number, all four the same
size, all four sitting on a card that sits on the page.

```
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ STREAK   │ │ SESSIONS │ │ VOLUME   │ │ LAST     │
│ 12       │ │ 4        │ │ 8.2t     │ │ 2d ago   │
└──────────┘ └──────────┘ └──────────┘ └──────────┘
```

It looks designed. It is the house style current AI tools default to, and it
is decoration doing hierarchy's job. Four numbers with identical weight say
that all four matter equally, which is false. You opened the app for one of
them.

Boxes inside boxes are the tell. When you find yourself nesting a surface to
show that something is grouped, the layout has already failed.

## After

The number the task needs is large and 600. The other three sit under it as one
line of secondary text. No boxes, no pills, no shadows. One rule separates the
block from the list below it.

```
Last session 2 days ago

12 day streak

4 sessions this week · 8.2t volume
────────────────────────────────────
```

Zero borders. One accent on the page, and it is not spent here.

## Why

Principle 6, nested boxes are not hierarchy. If a box is doing the hierarchy
work, the layout is wrong.

Principle 4, weight follows frequency of use. Three of those numbers are read
once a month.

This is the second named anti-look in `SKILL.md`, every element on its own
floating surface.

## Carry this

Delete every border and shadow, then look. If the page stopped making sense,
the decoration was carrying the hierarchy and the hierarchy has to be rebuilt.
