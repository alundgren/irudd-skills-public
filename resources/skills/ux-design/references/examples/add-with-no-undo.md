# Adding a thing with no way to see or remove it

A recipe editor. The task is building an ingredient list.

## Before

A form with a name field, an amount field, and a save button. You fill it in,
press save, the form clears and the fields go empty again. Nothing else on the
screen changes.

To check what you have added so far you leave the page and open the recipe.
To fix a typo you leave the page, find the row, and come back.

This is not laziness, it is how the feature got built. The form was the ask.
The list felt like the recipe page's job, and the recipe page already existed.

## After

The list of what has been added sits directly under the form. Newest first,
each row showing the two values you typed and a remove control. Save the form,
a row appears. Press remove, the row goes.

Removal is one click with no confirmation, because re-adding it costs the same
one click. Confirmation is for things you cannot get back.

## Why

Principle 7, consequences stay visible and reversible. If something can be
added, it can be seen and removed.

Principle 8 comes free. Nobody has to be told the save worked, because the row
appearing says it.

## Carry this

A screen that adds a thing shows the things and can remove them. If removal is
genuinely impossible, say so on the screen before the add, not after.
