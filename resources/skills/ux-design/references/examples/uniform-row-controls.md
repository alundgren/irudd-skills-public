# Row controls styled by category instead of by use

A link list. One row per article, with its metadata under the title.

Hacker News is deliberately plain, but one row still gives equal weight to
actions people use at very different rates.

## Before

```
Some article title (example.com)
123 points by alice 3 hours ago | hide | 47 comments
```

The whole second line is the same small muted grey. Points, author, age, hide,
comments. All of it styled identically because all of it is metadata.

But almost everyone on that row clicks the title or clicks comments. Almost
nobody clicks hide, and almost nobody reads the points count. Two of the five
things carry the traffic and none of the styling.

The mistake is grouping by type and styling the group uniformly.

## After

```
Some article title (example.com)
123 points by alice 3 hours ago · 47 comments      hide
```

Comments moves to primary text colour and weight. It is the second most wanted
thing on the row, so it gets the second most weight.

Points, author and age stay muted. They are context, read occasionally, never
clicked.

Hide becomes the smallest thing on the row and moves to the far end, or waits
for hover. It stays readable, because unreadable is not the goal. It is
destructive and rare, and it was competing with the thing everyone wants.

Nothing about the information changed. Only what the styling claims about it.

## Why

Principle 4, visual weight follows frequency of use. Style by how often someone
wants the thing, never by what category of metadata it belongs to.

## Carry this

For every control in a row, ask what share of visits touches it. If two
controls with wildly different answers look the same, fix the styling, not the
row.
