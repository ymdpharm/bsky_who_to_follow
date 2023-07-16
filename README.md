## bsky_who_to_follow
Simple user recommendation for Bluesky. 

1. Fetch the list of current follows
2. List up candidates (follows of current follows)
3. Calc popularity of each candidate (using similarity, followers count)
4. Filter out candidates

```
❯ poetry run python main.py -h yourhandle.bsky.social -p yourpass -t 50
```
