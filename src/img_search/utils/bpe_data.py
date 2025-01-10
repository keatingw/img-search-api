"""Module for BPE data."""

import re

import datasets


def load_wikitext2() -> tuple[list[str], list[str], list[str]]:
    """Gets wikitext2 from huggingface and gives train, val, test."""
    data = datasets.load_dataset("wikitext", "wikitext-2-raw-v1")
    return data["train"]["text"], data["validation"]["text"], data["test"]["text"]


def process_wikitext(text: list[str]) -> list[str]:
    """Converts raw wikitext into article-level strings."""
    joined = "\n".join([i for i in text if i != ""])
    split_articles = re.sub(
        r"\s=\s([\w\s]+)\s=\s",
        r"<NEW_ARTICLE_MARKER>\1",
        joined,
    ).split("<NEW_ARTICLE_MARKER>")
    return split_articles  # noqa: RET504
