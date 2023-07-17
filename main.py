import numpy as np
import pandas as pd
from atproto import Client
from typer import Option, Typer

app = Typer()
client = Client()


def _fetch_follows(actor: str, cursor: str | None):
    d = {"actor": actor, "limit": 100}
    if cursor:
        d["cursor"] = cursor

    return client.bsky.graph.get_follows(d)


def _fetch_followers_count(actor: str):
    d = {"actor": actor}
    return client.bsky.actor.get_profile(d).followersCount


def get_follows(handle: str, limit: int = 1000):
    """
    list of current follows
    """
    cursor = None
    result = []
    while True:
        fetched = _fetch_follows(handle, cursor)
        if not fetched.cursor:
            break
        result = result + [e.handle for e in fetched.follows]
        cursor = fetched.cursor
        if len(result) >= limit:
            break

    return result[0:limit]


def follows_follow_graph(my_follows: list[str], limit: int = 1000):
    """
    current follows -> list of follows of current follows
    """
    follows_two = {target: get_follows(target, limit) for target in my_follows}
    return follows_two


def follows_follow_matrix(graph: dict[str, list[str]]):
    """
    shape: (current follows, follows of current follows as candidates)
    """
    values = np.concatenate(list(graph.values()))
    unique_values = np.unique(values)
    df = pd.DataFrame(
        {k: np.isin(unique_values, v).astype(int).tolist() for k, v in graph.items()},
        index=unique_values,
    )

    return df.T


def similarity(graph: dict[str, list[str]]):
    """
    Jaccard index.
    """
    labels = list(graph.keys())
    df = pd.Series(
        {
            k: len(set(labels) & set(v)) / len(set(labels) | set(v))
            for k, v in graph.items()
        },
        index=labels,
    )
    return df


def list_recommend(handle: str, top: int):
    my_follows = get_follows(handle)
    graph = follows_follow_graph(my_follows)
    mat = follows_follow_matrix(graph)
    sim = similarity(graph)
    pre_ranked_cands = mat.mul(sim, axis=0).sum()
    pre_sorted_cands = pre_ranked_cands.sort_values(ascending=False)[
        0 : top * 2
    ]  # roughly limit
    followers = [_fetch_followers_count(e) for e in pre_sorted_cands.index]
    sorted_cand = (pre_sorted_cands / followers).sort_values(ascending=False)
    filtered_cand = [
        user
        for user, score in sorted_cand.items()
        if user not in my_follows and user != handle
    ]
    return filtered_cand[0:top]


@app.command()
def exec(
    handle: str = Option(..., "-h", "--handle", help="your handle."),
    password: str = Option(
        ..., "-p", "--password", help="your password. (It should not be required..)"
    ),
    top: int = Option(
        ..., "-t", "--top", help="number limit of recommendation result."
    ),
):
    client.login(handle, password)
    print(list_recommend(handle, top))


if __name__ == "__main__":
    app()
