# A destructive action styled like a safe one

An admin page for one deployed app.

## Before

Three buttons in a row under the app name. Redeploy, view logs, delete
application. Same size, same accent fill, same weight, same corner radius.
Delete is third because that is the order they were written in.

Every one of them is one click with no confirmation. Two of those clicks are
free. One of them is not.

The failure is that a reflex aimed at redeploy lands on delete. Nothing on the
screen slows the hand down.

## After

Redeploy carries the accent. It is the thing you came to do, so it gets the
weight, and it stays in the row.

View logs is a plain link next to it. Wanted often, but it is navigation, not
an action.

Delete leaves the row. It moves to the bottom of the page, under a rule, in a
block of its own, in `danger`. It asks you to type the app name before it
enables. GitHub's treatment, and it is worth copying.

## Why

Principle 7, make safe and dangerous actions look different. Principle 4 does
the rest of the work, since weight follows how often you want the thing, and
nobody wants delete often.

Colour alone is not enough. Distance and a typed confirmation are what stop the
reflex. Red is the label, not the guard.

## Carry this

If two controls can be hit by the same reflex and one of them is irreversible,
the layout is wrong.
