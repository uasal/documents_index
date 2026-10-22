import json
import os
import threading
import urllib.error
import urllib.request

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("logger")

# Only Slack incoming webhook URLs are accepted, so an admin can't point the
# server at an arbitrary (possibly internal) address.
SLACK_HOOK_PREFIX = "https://hooks.slack.com/"

# Seconds to wait on Slack before giving up on a post.
POST_TIMEOUT = 10


def base_url():
    """
    Returns the public teledocs URL from the TELEDOCS_URL env var. Slack
    notifications are only sent when it is set, so instances that don't set
    it (local, staging) never post to Slack.

    Returns
    -------
    str
        Public teledocs URL without a trailing slash, or "" if not set.
    """
    return os.environ.get("TELEDOCS_URL", "").strip().rstrip("/")


def _escape(text):
    """
    Escapes the characters Slack's "mrkdwn" treats as control characters.

    Parameters
    ----------
    text : str
        Text to be escaped.

    Returns
    -------
    str
        Escaped text.
    """
    return (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _link(url, text=None):
    """
    Returns a Slack "mrkdwn" link, escaping both the URL and the link text.

    Parameters
    ----------
    url : str
        Link target.
    text : str, optional
        Link text, defaults to the URL itself.

    Returns
    -------
    str
        Slack mrkdwn link.
    """
    # "|" separates the URL from the link text in Slack links
    target = _escape(url).replace("|", "%7C")
    return f"<{target}|{_escape(text or url)}>"


def build_entry_message(title, doc_identifier, author, compiled_url, source_url, label_names):
    """
    Builds the Slack message announcing a new entry with given labels.

    Parameters
    ----------
    title : str
        Title of the entry.
    doc_identifier : str
        doc_identifier of the entry, used to link back to teledocs.
    author : str or None
        Author of the entry.
    compiled_url : str or None
        URL of the entry.
    source_url : str or None
        Source URL of the entry.
    label_names : list
        Names of the labels the entry was given.

    Returns
    -------
    dict
        Message to post to a Slack incoming webhook.
    """
    labels_text = ", ".join(f"`{_escape(name)}`" for name in sorted(label_names))
    entry_link = _link(f"{base_url()}/docs/{doc_identifier}", title)

    lines = [f"Teledocs entry labelled {labels_text}: *{entry_link}*"]
    if author:
        lines.append(f"*Author:* {_escape(author)}")
    if compiled_url:
        lines.append(f"*URL:* {_link(compiled_url)}")
    if source_url:
        lines.append(f"*Source URL:* {_link(source_url)}")

    # Unfurling is turned off so Slack doesn't fetch the linked pages and
    # preview their contents in the channel.
    return {"text": "\n".join(lines), "unfurl_links": False, "unfurl_media": False}


def build_test_message(hook_name):
    """
    Builds the Slack message sent when an admin tests a hook.

    Parameters
    ----------
    hook_name : str
        Name of the hook being tested.

    Returns
    -------
    dict
        Payload to post to a Slack incoming webhook.
    """
    return {"text": f"Test message from teledocs for the hook *{_escape(hook_name)}*."}


def post_message(url, message):
    """
    Posts a message to a Slack incoming webhook.

    Parameters
    ----------
    url : str
        Slack incoming webhook URL.
    message : dict
        Message payload.

    Returns
    -------
    bool
        True if Slack accepted the message, False otherwise.
    """
    request = urllib.request.Request(
        url,
        data=json.dumps(message).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=POST_TIMEOUT) as response:
            return response.status == 200
    except (urllib.error.URLError, TimeoutError, ValueError) as e:
        # Never log the URL itself, it is the hook's secret
        logger.error(f"Slack: Posting message failed. Error: {e}")
        return False


def dispatch(messages):
    """
    Posts messages in a background thread, so a slow or failing Slack never
    holds up or breaks the request that triggered them. Failed posts are
    logged and dropped.

    Parameters
    ----------
    messages : list
        List of (hook name, url, payload) tuples.
    """
    if not messages:
        return

    def send_all():
        for name, url, payload in messages:
            if post_message(url, payload):
                logger.info(f"Slack: Posted message to hook {name}.")
            else:
                logger.error(f"Slack: Message to hook {name} was not delivered.")

    threading.Thread(target=send_all).start()
