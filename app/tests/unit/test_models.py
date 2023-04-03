from app.models import Standard, Subject
from app.tests.tools.mock_data import create_topics


def test_standard_model(session):
    topic = create_topics(session, 1)

    standard = Standard(
        grade=5, subject=Subject.math, topic_id=topic.id, template="Will {} by {}"
    )

    session.add(standard)
    session.commit()
    session.refresh(standard)

    assert standard.topic == topic
    assert topic.standards[0] == standard
    assert standard.grade == 5
    assert standard.subject == "math"
    assert standard.template == "Will {} by {}"
