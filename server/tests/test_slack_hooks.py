import pytest
from flask import Flask
from app import db


def setup_test_app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Re-init db with this app for testing context
    db.init_app(app)
    return app


@pytest.fixture()
def test_app():
    app = setup_test_app()
    with app.app_context():
        # Import models here so they bind to the test-configured db
        import models  # noqa: F401
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def sent(monkeypatch):
    """Replaces the background Slack sender with one that records the
    messages instead, and sets TELEDOCS_URL so notifications are enabled."""
    import slack

    messages = []
    monkeypatch.setenv("TELEDOCS_URL", "https://teledocs.example.edu/")
    monkeypatch.setattr(slack, "dispatch", lambda batch: messages.extend(batch))
    return messages


HOOK_URL = "https://hooks.slack.com/services/T000/B000/secretsecret"


def _labels(*names):
    from models import Label
    return [Label.create(name=name) for name in names]


def _hook(name, labels, url=HOOK_URL):
    from models import SlackHook
    hook = SlackHook.create(name=name, url=url, label_ids=[label.pk for label in labels])
    assert hook
    return hook


def _document(labels=(), **kwargs):
    from models import Document
    data = {
        "title": "Optical design",
        "author": "A. Author",
        "creator_email": "author@example.edu",
        "entry_type": "document",
        "change_controlled": "no",
        "number": "",
        "compiled_url": "https://drive.example.com/compiled",
        "source_url": "https://drive.example.com/source",
        "label_ids": [label.pk for label in labels],
    }
    data.update(kwargs)
    doc = Document.create(**data)
    assert doc
    return doc


def test_create_posts_to_hooks_of_assigned_labels(test_app, sent):
    optics, thermal, other = _labels("optics", "thermal", "other")
    _hook("#optics", [optics])
    _hook("#thermal", [thermal])

    doc = _document([optics, other])

    assert len(sent) == 1
    name, url, payload = sent[0]
    assert (name, url) == ("#optics", HOOK_URL)
    text = payload["text"]
    assert "`optics`" in text and "other" not in text
    assert f"<https://teledocs.example.edu/docs/{doc.doc_identifier}|Optical design>" in text
    assert "*Author:* A. Author" in text
    assert "https://drive.example.com/compiled" in text
    assert "https://drive.example.com/source" in text
    assert payload["unfurl_links"] is False and payload["unfurl_media"] is False


def test_one_message_per_hook_listing_all_matching_labels(test_app, sent):
    optics, thermal = _labels("optics", "thermal")
    _hook("#engineering", [optics, thermal])

    _document([optics, thermal])

    assert len(sent) == 1
    assert "`optics`, `thermal`" in sent[0][2]["text"]


def test_update_posts_only_for_added_labels(test_app, sent):
    optics, thermal = _labels("optics", "thermal")
    _hook("#optics", [optics])
    _hook("#thermal", [thermal])
    doc = _document([optics])
    sent.clear()

    doc.update(label_ids=[optics.pk, thermal.pk])

    assert [name for name, _, _ in sent] == ["#thermal"]


def test_update_without_added_labels_posts_nothing(test_app, sent):
    optics, thermal = _labels("optics", "thermal")
    _hook("#optics", [optics])
    doc = _document([optics, thermal])
    sent.clear()

    # Unrelated edit, then removing a label
    doc.update(title="New title")
    doc.update(label_ids=[optics.pk])

    assert sent == []


def test_nothing_posted_without_teledocs_url(test_app, sent, monkeypatch):
    monkeypatch.delenv("TELEDOCS_URL")
    (optics,) = _labels("optics")
    _hook("#optics", [optics])

    _document([optics])

    assert sent == []


def test_failed_notification_does_not_block_save(test_app, sent, monkeypatch):
    import slack
    from models import Document

    def broken(batch):
        raise RuntimeError("Slack is down")

    monkeypatch.setattr(slack, "dispatch", broken)
    (optics,) = _labels("optics")
    _hook("#optics", [optics])

    doc = _document([optics])

    assert Document.get_by_doc_identifier(doc.doc_identifier) is not None


def test_rejects_non_slack_urls(test_app):
    from models import SlackHook

    assert SlackHook.create(name="internal", url="http://169.254.169.254/latest", label_ids=[]) is False
    assert SlackHook.create(name="plain http", url="http://hooks.slack.com/x", label_ids=[]) is False


def test_serialized_hook_hides_url(test_app):
    (optics,) = _labels("optics")
    hook = _hook("#optics", [optics])

    serialized = hook.serialize()

    assert HOOK_URL not in str(serialized)
    assert serialized["url_hint"] == "…cret"
    assert serialized["labels"] == [{"pk": optics.pk, "name": "optics"}]


def test_hook_urls_not_exposed_through_labels(test_app):
    from models import Label

    (optics,) = _labels("optics")
    _hook("#optics", [optics])

    assert HOOK_URL not in str(Label.serialize_list([optics]))


def test_update_keeps_url_when_none_submitted(test_app):
    (optics,) = _labels("optics")
    hook = _hook("#optics", [optics])

    assert hook.update(name="#optics-team", url="", label_ids=[])

    assert hook.name == "#optics-team"
    assert hook.url == HOOK_URL
    assert hook.labels == []


def test_deleting_label_unlinks_it_from_hooks(test_app):
    from sqlalchemy import text
    from models import SlackHook

    # The link rows are removed by the ON DELETE CASCADE, like on Postgres,
    # which SQLite only enforces when asked to
    db.session.execute(text("PRAGMA foreign_keys=ON"))

    optics, thermal = _labels("optics", "thermal")
    hook = _hook("#engineering", [optics, thermal])

    assert optics.delete_label()

    db.session.expire_all()
    assert [label.name for label in SlackHook.get_by_pk(hook.pk).labels] == ["thermal"]


def test_message_escapes_slack_formatting(test_app, monkeypatch):
    import slack

    monkeypatch.setenv("TELEDOCS_URL", "https://teledocs.example.edu")
    payload = slack.build_entry_message("<!channel> & co", "ABC123", "<@U123>",
                                        "https://x.example.com/a|b", "", ["lbl"])

    text = payload["text"]
    assert "<!channel>" not in text and "&lt;!channel&gt; &amp; co" in text
    assert "<@U123>" not in text
    assert "https://x.example.com/a%7Cb" in text
    assert "Source URL" not in text
