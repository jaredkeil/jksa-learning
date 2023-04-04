import logging
from itertools import cycle
from string import ascii_uppercase

from sqlmodel import Session

from app import crud
from app.core.config import Settings
from app.database import engine
from app.models import (
    UserCreate,
    UserRead,
    TopicCreate,
    Topic,
    Subject,
    StandardCreate,
    Standard,
    Resource,
    ResourceCreateInternal,
    User,
    CardCreate,
    Card,
)

settings = Settings()
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def create_first_superuser():
    with Session(engine) as session:
        user = crud.user.get_by_email(session, email=settings.FIRST_SUPERUSER)
        if not user:
            logger.info("Superuser not found. Trying to create...")
            user_in = UserCreate(
                email=settings.FIRST_SUPERUSER,
                password=settings.FIRST_SUPERUSER_PW,
            )
            user = crud.user.create(session, obj_in=user_in)
            crud.user.make_superuser(session, db_obj=user)
            logger.info(f"Created superuser: {UserRead.from_orm(user)}")
        else:
            logger.info(f"Superuser already exists: {UserRead.from_orm(user)}")
        return user


def dummy_data(superuser: User):
    with Session(engine) as session:
        topics = dummy_topics(session)
        standards = dummy_standards(session, topics)
        resources = dummy_resources(session, superuser)
        resources_cards = dummy_cards(session, resources)  # 3 cards per resource


def dummy_topics(session: Session, n_per_subject: int = 4) -> list[Topic]:
    """Create a number of basic topics for each Subject enum"""
    topics = []
    # ex. n = 30, and there are 3 Subjects, create 10 topics for each Subject
    for i in range(1, n_per_subject + 1):
        for s in Subject:
            name = f"{s[0].upper()}{i}"
            topic_in = TopicCreate(description=name)
            topic = crud.topic.create(session, obj_in=topic_in)
            topics.append(topic)
    logger.info(f"Generated {len(topics)} dummy Topics")
    return topics


def dummy_standards(
    session: Session, topics: list[Topic], n_per_topic: int = 3, n_grades: int = 5
) -> list[Standard]:
    """Create a certain number of standards for each topic"""
    standards = []

    base_template = (
        "standard {code}: " "[Subject={subject}, Topic={topic}, Grade={grade}]"
    )

    i = 1
    for std_i in range(1, n_per_topic + 1):
        for grade in range(1, n_grades + 1):
            for j, (topic, subject) in enumerate(zip(topics, cycle(Subject)), start=1):
                subj_prefix = subject.value[0].upper()
                alpha = ascii_uppercase[std_i - 1]

                t = len(topics) // len(Subject) + 1

                template = base_template.format(
                    code=f"{topic.description}:S{alpha}:G{grade}",
                    subject=subject.value,
                    topic=topic.description,
                    grade=grade,
                )
                standard_in = StandardCreate(
                    grade=grade, subject=subject, template=template, topic_id=topic.id
                )

                standard = crud.standard.create(session, obj_in=standard_in)
                standards.append(standard)
                i += 1
    logger.info(
        f"Generated {len(standards)} dummy Standards"
        f" ({n_per_topic} for each Topic [{len(topics)} topics]"
        f", for {n_grades} grades)"
    )
    return standards


def dummy_resources(session: Session, user: User) -> list[Resource]:
    """Generate 2 dummy resources -- 1 private, 1 public"""
    resource_in1 = ResourceCreateInternal(
        name=f"{user.email}'s private resource", creator_id=user.id
    )
    resource1 = crud.resource.create(session, obj_in=resource_in1)
    resource_in2 = ResourceCreateInternal(
        name=f"{user.email}'s public resource", private=False, creator_id=user.id
    )
    resource2 = crud.resource.create(session, obj_in=resource_in2)
    logger.info(f"Generated 2 dummy Resources")
    return [resource1, resource2]


def dummy_cards(session: Session, resources: list[Resource]) -> list[list[Card]]:
    resources_cards = []
    for r in resources:
        card_in1 = CardCreate(
            question=f"{r.id}:Q 1", answer=f"{r.id}A 1", resource_id=r.id
        )
        card_in2 = CardCreate(
            question=f"{r.id}:Q 2", answer=f"{r.id}A 2", resource_id=r.id
        )
        card_in3 = CardCreate(
            question=f"{r.id}:Q 3", answer=f"{r.id}A 3", resource_id=r.id
        )
        card1 = crud.card.create(session, obj_in=card_in1)
        card2 = crud.card.create(session, obj_in=card_in2)
        card3 = crud.card.create(session, obj_in=card_in3)
        resources_cards.append([card1, card2, card3])
    return resources_cards


if __name__ == "__main__":
    superuser = create_first_superuser()
    if settings.API_ENV == "DEV":
        dummy_data(superuser)
