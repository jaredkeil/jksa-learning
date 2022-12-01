import random

from sqlmodel import Session

from app import crud
from app.models import (Topic, Standard, StandardCreate, User, UserCreate,
                        Resource, ResourceCreateInternal, ResourceFormat, Card,
                        CardCreate, GoalCreate, Goal, Role, UserUpdate, Group,
                        GroupCreate, Lap, LapCreate, Attempt,
                        AttemptCreateExternal, AttemptCreateInternal)
from app.tests.utils import (random_int, random_email, random_lower_string,
                             random_subject, random_future_date, utc_now,
                             random_accuracy, random_password)


def create_random_user(session: Session, role: Role = None) -> User:
    """
    Creates a user with random email and password and adds to database
    """
    user_in = UserCreate(email=random_email(),
                         password=random_password(),
                         role=role)
    return crud.user.create(session, obj_in=user_in)


def update_user(session: Session, user: User, in_dict: dict) -> User:
    """
    Creates a user as a teacher role
    """
    user_db = crud.user.get(session, user.id)
    merge_kwargs = dict(user_db.dict(), **in_dict)
    user_in = UserUpdate(**merge_kwargs)
    return crud.user.update(session, db_obj=user_db, obj_in=user_in)


def create_random_resource(session: Session, user: User) -> Resource:
    """
    Creates a resource with random name and adds to database
    """
    resource_in = ResourceCreateInternal(name=random_lower_string(),
                                 creator_id=user.id)
    return crud.resource.create(session, obj_in=resource_in)


def create_topics(session: Session, n: int = 1) -> list[Topic] | Topic:
    """
    Creates one or more topics and adds to database.
    If n >= 1 or n == 0, then Topic objects returned in list,
    If n == 1 (default) a single Topic object will be returned.
    """
    topics = []
    for i in range(n):
        topic = Topic(description=f'Test Topic Number {i}')
        session.add(topic)
        session.commit()
        session.refresh(topic)
        topics.append(topic)

    return topics[0] if n == 1 else topics


def create_random_standards(session: Session, topic: Topic, n: int = 1
                            ) -> list[Standard] | Standard:
    """
    For a given Topic in DB, creates one or more Standards with a random grade
     (between 1-12), random subject(Subject Enum), and random template
     (a random string), and adds to database.
    """

    standards = []
    for i in range(n):
        standard_in = StandardCreate(
            grade=random_int(1, 12),
            subject=random_subject(),
            template=random_lower_string(),
            topic_id=topic.id
        )
        standard = crud.standard.create(session, obj_in=standard_in)
        standards.append(standard)

    return standards[0] if n == 1 else standards


def create_random_resources(session: Session, user: User, n: int = 1,
                            all_private: bool = False, all_public: bool = False
                            ) -> list[Resource] | Resource:
    """
    For a given User in DB, creates one or more Resources.
    """
    private_choices = [True, False]
    if all_private:
        private_choices.remove(False)
    if all_public:
        private_choices.remove(True)
    if not private_choices:
        raise ValueError("Cannot create resources all_private AND all_public")

    resources = []
    for i in range(n):
        resource_in = ResourceCreateInternal(
            name=random_lower_string(16),
            private=random.choice(private_choices),
            format=random.choice(list(ResourceFormat)),
            creator_id=user.id
        )
        resource = crud.resource.create(session, obj_in=resource_in)
        resources.append(resource)

    return resources[0] if n == 1 else resources


def create_random_cards(session: Session, resource: Resource, n: int = 1
                        ) -> list[Card] | Card:
    cards = []
    for i in range(n):
        card_in = CardCreate(
            question=random_lower_string(12),
            answer=random_lower_string(12),
            resource_id=resource.id
        )
        card = crud.card.create(session, obj_in=card_in)
        cards.append(card)
    return cards[0] if n == 1 else cards


def create_random_goals(
        session: Session,
        teacher: User,
        student: User,
        group: Group,
        standard: Standard,
        n: int = 1) -> list[Goal] | Goal:
    """Create random goals"""
    goals = []
    for _ in range(n):
        goal_in = GoalCreate(
            teacher_id=teacher.id,
            student_id=student.id,
            standard_id=standard.id,
            group_id=group.id,
            start_date=utc_now(),
            end_date=random_future_date(),  # type: ignore
            accuracy=random_accuracy(),  # type: ignore
            n_trials=random_int(1, 8)  # type: ignore
        )
        goal = crud.goal.create(session, obj_in=goal_in)
        goals.append(goal)

    return goals[0] if n == 1 else goals


def create_random_goals_with_resources(session, n: int = 1, n_rsc_per: int = 2,
                                       n_cards_per: int = 3
                                       ) -> list[Goal] | Goal:
    goals = []
    for _ in range(n):
        teacher = create_random_user(session, Role.teacher)
        student = create_random_user(session, Role.student)
        group = create_random_groups(session)
        group.users.extend([teacher, student])
        topic = create_topics(session)
        standard = create_random_standards(session, topic)
        goal = create_random_goals(
            session, teacher, student, group, standard, n=1)
        resources = create_random_resources(session, teacher, n_rsc_per)
        if n_rsc_per == 1:
            resources = [resources]
        for r in resources:
            create_random_cards(session, r, n_cards_per)
        goal.resources.extend(resources)
        goals.append(goal)

    return goals[0] if n == 1 else goals


def create_random_groups(session: Session, n: int = 1) -> list[Group] | Group:
    """Create random groups"""
    groups = []
    for _ in range(n):
        group_in = GroupCreate(label=random_lower_string())
        group = crud.group.create(session, obj_in=group_in)
        groups.append(group)
    return groups[0] if n == 1 else groups


def create_random_laps(session: Session, goal: Goal, resource: Resource,
                       n: int = 1) -> list[Lap] | Lap:
    """Create random laps"""
    laps = []
    for _ in range(n):
        lap_in = LapCreate(goal_id=goal.id,
                           resource_id=resource.id)

        lap = crud.lap.create(session, obj_in=lap_in)
        laps.append(lap)
    return laps[0] if n == 1 else laps


def create_random_attempts(session: Session, lap: Lap) -> list[Attempt]:
    """
    Create random attempts for every card for the Lap's resource.
    """
    attempts = []
    for card in lap.resource.cards:
        attempt_in = AttemptCreateInternal(submission=random_lower_string(8),
                                           lap_id=lap.id,
                                           card_id=card.id,
                                           correct=random.choice([True, False]))
        attempt = crud.attempt.create(session, obj_in=attempt_in)
        attempts.append(attempt)
    return attempts

