# A system-initiated change with no trace

A deployment admin page. The service polls git and redeploys itself when a
commit lands.

## Before

The page says `Running`. It said `Running` yesterday too.

Something changed overnight. The site is on a new commit, the container was
rebuilt, and the page looks exactly as it did before. To find out what
happened you ssh in and read the logs.

The tell is that a person clicking redeploy and the poller firing on its own
leave the same trace, which is none.

## After

Under the status, three lines of history.

```
Running
Redeployed today 14:02   a3f91c2   poll
             yesterday 09:31   7c02b19   poll
        3 days ago 18:44   d81ee40   j.rivera
```

Commit hash in mono, because you compare it character by character against
what you pushed. Who or what triggered it in the last column, in plain words.
Three entries is enough. The full list is a click away and almost nobody
clicks it.

## Why

Principle 7. It must not matter whether the system acted or the end user
acted, either way the end user sees what happened and why.

An automatic action that leaves no trace is worse than a manual one, because
there is nobody to ask.

## Carry this

If the system can change state on its own, the screen showing that state shows
when it last changed and what caused it.
