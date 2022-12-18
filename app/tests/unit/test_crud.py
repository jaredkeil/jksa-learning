import pytest
import sqlalchemy.exc

from app import crud
from app.controller.endpoints.attempt import is_correct
from app.models import (StandardCreate, Subject, ResourceCreateInternal,
                        StandardResourceCreate, GoalCreate, UserUpdate,
                        ResourceUpdate, ResourceFormat, GroupCreate, Role,
                        LapCreate, AttemptCreateExternal,
                        AttemptCreateInternal)
from app.tests.tools.mock_data import (create_topics, create_random_user,
                                       create_random_standards,
                                       create_random_resources,
                                       create_random_groups,
                                       create_random_goals,
                                       create_random_cards,
                                       create_random_goals_with_resources,
                                       create_random_laps, pprint_dict)
from app.tests.tools.mock_params import random_email
from app.tests.tools.mock_user import random_password


def test_resource_user_relationship(session):
    user = create_random_user(session)
    resource_in = ResourceCreateInternal(creator_id=user.id, name='new one')
    resource = crud.resource.create(session, obj_in=resource_in)
    assert resource.creator == user


def test_resource_remove(session):
    user = create_random_user(session)
    resource = create_random_resources(session, user)
    crud.resource.remove(session, _id=resource.id)
    assert crud.resource.get(session, resource.id) is None


def test_standard_create(session):
    topic = create_topics(session, 1)
    standard_in = StandardCreate(grade=1, subject=Subject.ela,
                                 topic_id=topic.id, template='test')
    standard = crud.standard.create(session, obj_in=standard_in)
    assert standard.topic == topic
    assert standard.grade == 1
    assert standard.subject == 'ela'
    assert standard.template == 'test'


def test_topic_standards(session):
    topic = create_topics(session, 1)
    assert not topic.standards
    standards = create_random_standards(session, topic, 5)
    assert topic.standards == standards


def test_standard_create_multiple_per_topic(session):
    n_topics = 25
    n_standards_per_topic = 3
    topic_list = create_topics(session, n_topics)

    for i, topic in enumerate(topic_list):
        created_standards = []
        for j in range(n_standards_per_topic):
            standard_in = StandardCreate(grade=5, subject=Subject.ela,
                                         topic_id=topic.id,
                                         template=f'topic {i} - standard {j}')
            standard = crud.standard.create(session, obj_in=standard_in)
            assert standard.topic == topic
            created_standards.append(standard)
        assert topic.standards == created_standards


def test_standard_resources(session):
    topic = create_topics(session, 1)
    standard_in = StandardCreate(grade=4, subject=Subject.math,
                                 topic_id=topic.id, template='standard')
    standard = crud.standard.create(session, obj_in=standard_in)

    user = create_random_user(session)
    resource_in = ResourceCreateInternal(name='1', creator_id=user.id)
    resource = crud.resource.create(session, obj_in=resource_in)

    std_rsc_in = StandardResourceCreate(standard_id=standard.id,
                                        resource_id=resource.id)
    _ = crud.standard_resource.create(session, obj_in=std_rsc_in)

    assert len(standard.resources) == 1
    assert len(resource.standards) == 1
    assert standard.resources[0] == resource
    assert resource.standards == [standard]


def test_standard_resources_multiple(session):
    """
    Test many:many relationship.
    Some Standards have multiple Resources each.
    Some Resources have multiple Standards each.

    Scenario: 1 standard with 2 resources, 1 resource with 2 standards


            |----- R1
            |
    S1 =====|
            |
            |===== R2
            |
    S2 -----|

    """

    n_standards = 2
    n_resources = 2

    topic = create_topics(session, 1)
    standards = create_random_standards(session, topic, n_standards)

    user = create_random_user(session)
    resources = create_random_resources(session, user, n_resources)

    # assign first standard both resources
    for resource in resources:
        crud.standard_resource.create(session, obj_in=StandardResourceCreate(
            standard_id=standards[0].id,
            resource_id=resource.id))

    # assign second standard one resource
    # now that resource will relate to two standards
    crud.standard_resource.create(session, obj_in=StandardResourceCreate(
        standard_id=standards[1].id,
        resource_id=resources[1].id))

    assert len(standards[0].resources) == 2
    assert len(standards[1].resources) == 1

    assert len(resources[0].standards) == 1
    assert len(resources[1].standards) == 2

    assert standards[0].resources == resources
    assert standards[1].resources == [resources[1]]

    assert resources[0].standards == [standards[0]]
    assert resources[1].standards == standards


def test_resource_multi_standard_private(session):
    user1 = create_random_user(session)
    user2 = create_random_user(session)
    assert user1.id != user2.id
    # some resources will be private, some public. Generating enough for
    # probability's sake we will pass include_public=False to crud.
    user1_resources = create_random_resources(session, user1, 100,
                                              all_private=False)
    user2_resources = create_random_resources(session, user2, 100,
                                              all_private=False)

    topic = create_topics(session, 1)
    standard1 = create_random_standards(session, topic, 1)
    standard2 = create_random_standards(session, topic, 1)

    # use link table implicitly
    standard1.resources.extend(user1_resources[:60])
    standard1.resources.extend(user2_resources[:60])
    # Now there are 20 added resources in standard1.
    # 10 from user1, 10 from user2. Some of them are private, some are public.
    #
    # Since we are passing a standard_id, we want to make sure our resources
    # on Standard2 aren't returned.
    # Adding some overlap so
    standard2.resources.extend(user1_resources[25:])

    # Some of our resources are private, but since they are ours, we
    # should still get them

    ret_resources = crud.resource.get_multi_by_standard(session,
                                                        user1.id,
                                                        standard1.id,
                                                        include_public=False)

    assert ret_resources == user1_resources[:60]
    assert not all(r.private for r in ret_resources)
    for r in ret_resources:
        assert r.creator_id == user1.id


def test_resource_multi_standard_public(session):
    n_total = 100
    user1 = create_random_user(session)
    user2 = create_random_user(session)

    user1_resources = create_random_resources(session, user1, n_total,
                                              all_private=False)
    assert any(r.private for r in user1_resources)
    assert any(not r.private for r in user1_resources)

    user2_resources = create_random_resources(session, user2, n_total,
                                              all_private=False)
    assert any(r.private for r in user2_resources)
    assert any(not r.private for r in user2_resources)

    topic = create_topics(session, 1)
    standard1 = create_random_standards(session, topic, 1)
    standard2 = create_random_standards(session, topic, 1)

    n_add = 60
    n_other_std = 75
    standard1.resources.extend(user1_resources[:n_add])
    standard1.resources.extend(user2_resources[:n_add])

    # put some of user1's resources on a different standard
    standard2.resources.extend(user1_resources[n_total - n_other_std:])

    ret_resources = crud.resource.get_multi_by_standard(session,
                                                        user1.id,
                                                        standard1.id,
                                                        include_public=True)

    print(ret_resources)

    # these are the public resources that user2 added to the standard
    user2_public_std_resources = [r for r in user2_resources[:n_add] if
                                  not r.private]
    assert all([r in standard1.resources for r in user2_public_std_resources])
    assert all(r in ret_resources for r in user2_public_std_resources)
    assert any(r.creator_id == user2.id for r in ret_resources)

    for r in ret_resources:
        if r.creator_id == user2.id:
            assert not r.private
        if r.private:
            assert r.creator_id == user1.id

    exp_ret_resources = []
    for r in standard1.resources:
        if r.creator_id == user1.id:
            exp_ret_resources.append(r)
        elif not r.private:
            exp_ret_resources.append(r)

    assert exp_ret_resources == ret_resources


def test_get_multi(session):
    user = create_random_user(session)
    resources = create_random_resources(session, user, 5)
    ret_resources = crud.resource.get_multi(session)
    assert ret_resources == resources


def test_get_multi_with_params(session):
    topic = create_topics(session, 1)
    standards = create_random_standards(session, topic, 10)
    ret_standards = crud.standard.get_multi(session, skip=2, limit=5)
    assert ret_standards == standards[2:7]


def test_get_multi_by_ids(session):
    topic = create_topics(session, 1)
    standards = create_random_standards(session, topic, 10)
    ids = set([s.id for s in standards][::2])
    ret_standards = crud.standard.get_mult_by_ids(session, ids)
    assert ret_standards == standards[::2]


def test_create_goal(session):
    teacher = create_random_user(session)
    student = create_random_user(session)
    group = create_random_groups(session, 1)
    group.users.extend([teacher, student])
    topic = create_topics(session, 1)
    standard = create_random_standards(session, topic, 1)
    goal_in = GoalCreate(
        standard_id=standard.id,
        teacher_id=teacher.id,
        student_id=student.id,
        group_id=group.id,
        start_date='2022-08-01',  # type: ignore
        end_date='2199-07-30',  # type: ignore
        accuracy=0.80,  # type: ignore
        n_trials=5  # type: ignore
    )
    goal = crud.goal.create(session, obj_in=goal_in)
    assert goal.teacher == teacher
    assert goal.student == student
    assert goal.standard == standard
    assert goal.standard.topic == topic
    assert goal.teacher.groups == [group]


def test_update(session):
    # for object that directly inherits from CRUDBase
    user = create_random_user(session)
    resource_in1 = ResourceCreateInternal(name='og', private=True,
                                          creator_id=user.id,
                                          format=ResourceFormat.flashcard)
    resource_db = crud.resource.create(session, obj_in=resource_in1)
    og_id = resource_db.id
    og_creator_id = resource_db.creator.id
    resource_in = ResourceUpdate(name='new', private=False,
                                 format=ResourceFormat.pdf)
    resource_updated_db = crud.resource.update(
        session, db_obj=resource_db, obj_in=resource_in
    )
    assert resource_updated_db == resource_db
    assert resource_updated_db.id == og_id
    assert resource_updated_db.name == 'new'
    assert not resource_updated_db.private
    assert resource_updated_db.format == ResourceFormat.pdf
    assert resource_updated_db.creator.id == og_creator_id
    assert user.resources[0] == resource_updated_db


def test_base_update_with_dict(session):
    user = create_random_user(session)
    resource_in1 = ResourceCreateInternal(name='og', private=True,
                                          creator_id=user.id,
                                          format=ResourceFormat.flashcard)
    resource_db = crud.resource.create(session, obj_in=resource_in1)
    og_id = resource_db.id
    og_creator_id = resource_db.creator.id
    resource_in = {'name': 'new', 'private': False, 'format': 'pdf'}
    resource_updated_db = crud.resource.update(
        session, db_obj=resource_db, obj_in=resource_in
    )
    assert resource_updated_db == resource_db
    assert resource_updated_db.id == og_id
    assert resource_updated_db.name == 'new'
    assert not resource_updated_db.private
    assert resource_updated_db.format == ResourceFormat.pdf
    assert resource_updated_db.creator.id == og_creator_id
    assert user.resources[0] == resource_updated_db


def test_user_update_with_obj(session):
    user_db = create_random_user(session)
    og_id = user_db.id
    og_hash_pw = user_db.hashed_password
    user_in = UserUpdate(email=random_email(), password=random_password())
    user_updated_db = crud.user.update(session, db_obj=user_db, obj_in=user_in)
    assert user_updated_db == user_db  # session should refresh db obj
    assert user_updated_db.id == og_id
    assert user_updated_db.hashed_password != og_hash_pw
    assert user_updated_db.email == user_in.email


def test_user_update_with_dict(session):
    user_db = create_random_user(session)
    og_id = user_db.id
    og_hash_pw = user_db.hashed_password
    user_in = {'email': 'new@def.com', 'password': '456'}
    user_updated_db = crud.user.update(session, db_obj=user_db, obj_in=user_in)
    assert user_updated_db == user_db  # session should refresh db obj
    assert user_updated_db.id == og_id
    assert user_updated_db.hashed_password != og_hash_pw
    assert user_updated_db.email == 'new@def.com'


def test_user_update_without_password(session):
    user_db = create_random_user(session)
    og_id = user_db.id
    og_hash_pw = user_db.hashed_password
    user_in = UserUpdate(email='new@def.com')  # type: ignore
    user_updated_db = crud.user.update(session, db_obj=user_db, obj_in=user_in)
    assert user_updated_db == user_db  # session should refresh db obj
    assert user_updated_db.id == og_id
    assert user_updated_db.hashed_password == og_hash_pw
    assert user_updated_db.email == 'new@def.com'


def test_goal_resource_link(session):
    teacher = create_random_user(session)
    student = create_random_user(session)
    group = create_random_groups(session, 1)
    group.users.extend([teacher, student])
    topic = create_topics(session, 1)
    standard = create_random_standards(session, topic, 1)
    goal_in = GoalCreate(
        standard_id=standard.id,
        teacher_id=teacher.id,
        student_id=student.id,
        group_id=group.id,
        start_date='2022-08-01',  # type: ignore
        end_date='2199-07-30',  # type: ignore
        accuracy=0.80,  # type: ignore
        n_trials=5  # type: ignore
    )
    goal = crud.goal.create(session, obj_in=goal_in)

    # "happy path", the teacher creates the resources
    resources = create_random_resources(session, teacher, 3, all_public=True)
    goal.resources.extend(resources)
    assert goal.resources == resources
    assert all(r.goals == [goal] for r in resources)


def test_create_group(session):
    group_in = GroupCreate(label="Tester's classroom")
    group = crud.group.create(session, obj_in=group_in)
    assert group.id is not None
    assert group.users == []


def test_user_group_link(session):
    group1, group2 = create_random_groups(session, 2)
    user1, user2 = create_random_user(session), create_random_user(session)
    group1.users.extend([user1, user2])
    group2.users.extend([user1])
    assert user1.groups == [group1, group2]
    assert user2.groups == [group1]
    assert group1.users == [user1, user2]
    assert group2.users == [user1]


def test_create_lap(session):
    teacher = create_random_user(session, Role.teacher)
    student = create_random_user(session, Role.student)
    group = create_random_groups(session)
    group.users.extend([teacher, student])

    topic = create_topics(session)
    standard = create_random_standards(session, topic)

    goal = create_random_goals(session, teacher, student, group, standard)

    resource = create_random_resources(session, teacher)
    create_random_cards(session, resource)
    goal.resources.append(resource)

    lap_in = LapCreate(goal_id=goal.id, resource_id=resource.id)
    lap = crud.lap.create(session, obj_in=lap_in)

    pprint_dict(lap.dict())
    assert lap.goal == goal
    assert lap.resource == resource
    assert lap.start_ts


def test_create_attempts(session):
    goal = create_random_goals_with_resources(
        session, n=1, n_rsc_per=2, n_cards_per=3
    )
    for resource in goal.resources:
        lap = create_random_laps(session, goal, resource)
        for card in resource.cards:
            attempt_in = AttemptCreateExternal(lap_id=lap.id,
                                               card_id=card.id,
                                               submission='00 not correct 00')
            attempt_in = AttemptCreateInternal.from_orm(attempt_in)
            attempt_in.correct = is_correct(attempt_in.submission, card.answer)
            attempt = crud.attempt.create(session, obj_in=attempt_in)
            assert attempt.lap.goal == goal
            assert attempt.lap.resource == resource
            assert not attempt.correct
            assert attempt in lap.attempts
        assert lap.goal_resource
        assert lap in lap.goal_resource.laps
        assert len(lap.attempts) == 3


def test_remove_resource_associated_with_standard(session):
    user = create_random_user(session, role=None)
    resource = create_random_resources(session, user, 1)
    topic = create_topics(session, 1)
    standard = create_random_standards(session, topic, 1)
    standard.resources.append(resource)
    removed_resource = crud.resource.remove(session, _id=resource.id)
    assert resource not in session
    assert removed_resource not in session
    assert standard in session


def test_remove_resource_associated_with_goal(session):
    # if a resource is associated with a goal, it cannot be deleted.
    goal = create_random_goals_with_resources(session, n=1, n_rsc_per=1,
                                              n_cards_per=1)
    resource = goal.resources[0]
    print(goal.resources)
    # with pytest.raises(sqlalchemy.exc.IntegrityError):
    rem_resource = crud.resource.remove(session, _id=resource.id)
    print(rem_resource)
    print(rem_resource.goals)
    assert resource not in session
    assert goal in session
    print(goal.resources)


def test_remove_resource_cascade_delete_cards(session):
    pass


def test_remove_resource_associated_with_lap(session):
    goal = create_random_goals_with_resources(session, n=1, n_rsc_per=1,
                                              n_cards_per=1)
    resource = goal.resources[0]
    create_random_laps(session, goal, resource, 1)
    with pytest.raises(sqlalchemy.exc.IntegrityError):
        crud.resource.remove(session, _id=resource.id)
    assert resource in session


def test_remove_resource_after_goal_deletion(session):
    pass


def test_remove_goal_associated_with_lap(session):
    goal = create_random_goals_with_resources(session, n=1, n_rsc_per=1,
                                              n_cards_per=1)
    resource = goal.resources[0]
    create_random_laps(session, goal, resource, 1)
    with pytest.raises(sqlalchemy.exc.IntegrityError):
        crud.goal.remove(session, _id=goal.id)
    assert goal in session
    assert resource in session


def test_remove_resource_after_lap_deletion(session):
    goal = create_random_goals_with_resources(session, n=1, n_rsc_per=1,
                                              n_cards_per=1)
    assert len(goal.resources) == 1
    resource = goal.resources[0]
    lap = create_random_laps(session, goal, resource, 1)
    crud.lap.remove(session, _id=lap.id)
    crud.resource.remove(session, _id=resource.id)
    # crud.goal.remove(session, _id=resource.id)
    assert lap not in session
    assert resource not in session
    assert goal in session
    assert len(goal.resources) == 0
