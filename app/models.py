import enum
from datetime import date, datetime
from typing import Optional

from pydantic import (
    EmailStr, FutureDate, PositiveFloat, PositiveInt, SecretStr, validator,
    BaseModel
)
from sqlalchemy import (Column, String, TypeDecorator, ForeignKeyConstraint,
                        UniqueConstraint)
from sqlmodel import SQLModel, Field, Relationship

"""
Junction Standard<>Resource
"""


class StandardResourceBase(SQLModel):
    standard_id: int = Field(foreign_key='standard.id', primary_key=True)
    resource_id: int = Field(foreign_key='resource.id', primary_key=True)


class StandardResource(StandardResourceBase, table=True):
    __tablename__ = 'standard_resource'


class StandardResourceCreate(StandardResourceBase):
    pass


class ResourceStandardsMultiCreate(SQLModel):
    resource_id: int
    standard_ids: list[int]


class StandardResourceUpdate(StandardResourceBase):
    pass


"""
Junction Goal<>Resource

A goal can have many resources associated, and a resource can be associated
to different goals.
"""


class GoalResourceBase(SQLModel):
    goal_id: int = Field(foreign_key='goal.id', primary_key=True)
    resource_id: int = Field(foreign_key='resource.id', primary_key=True, nullable=False)


class GoalResource(GoalResourceBase, table=True):
    __tablename__ = 'goal_resource'
    laps: list['Lap'] = Relationship(back_populates='goal_resource')


class GoalResourceCreate(GoalResourceBase):
    pass


class GoalResourceUpdate(GoalResourceBase):
    pass


class GoalResourceMultiCreate(SQLModel):
    goal_id: int
    resource_ids: list[int]


"""
Junction User<>Group

A Group can have many users associated, and a user can belong to different
Groups (e.g. a student who takes multiple classes, a teacher who teaches
multiple classes/groups of students)
"""


class UserGroupBase(SQLModel):
    user_id: int = Field(foreign_key='users.id', primary_key=True)
    group_id: int = Field(foreign_key='group.id', primary_key=True)


class UserGroup(UserGroupBase, table=True):
    __tablename__ = 'user_group'


class UserGroupCreate(UserGroupBase):
    pass


"""
Group
"""


class GroupBase(SQLModel):
    label: str


class Group(GroupBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    users: list['User'] = Relationship(
        back_populates='groups', link_model=UserGroup
    )


class GroupCreate(GroupBase):
    pass


class GroupUpdate(GroupBase):
    pass


class GroupRead(GroupBase):
    id: int


"""
Users
"""


class SecretStrSqL(TypeDecorator):
    """
    Get string value of SecretStr on the way in to db, and put value back
    into SecretStr on the way out. Useful for hashed passwords.
    """
    impl = String
    cache_ok = True

    def process_bind_param(self, value: SecretStr, dialect) -> str:
        return value.get_secret_value()

    def process_result_value(self, value: str, dialect) -> SecretStr:
        return SecretStr(value)

    def copy(self, **kw):
        return SecretStrSqL(self.impl.length)


def password_check(pw: SecretStr) -> SecretStr | None:
    if pw is None:  # this can happen in UserUpdate body
        return pw
    errors: list[str] = []
    if (min_len := 8) > len(pw):
        errors.append(f'Password shorter than {min_len} characters.')
    if not any(c.isdigit() for c in pw.get_secret_value()):
        errors.append('Password needs at least one digit.')
    if not any(c.isalpha() for c in pw.get_secret_value()):
        errors.append('Password needs at least one letter.')
    if errors:
        raise ValueError(' '.join(errors))
    return pw


class Role(str, enum.Enum):
    teacher = 'teacher'
    student = 'student'


class UserBase(SQLModel):
    email: Optional[EmailStr] = Field(
        default=None,
        sa_column=Column("email", String, unique=True, index=True)
    )
    first_name: Optional[str]
    last_name: Optional[str]
    display_name: Optional[str]
    role: Optional[Role]


class UserDBBase(UserBase):
    # Users can't control these attributes from UserUpdate
    is_active: Optional[bool] = True
    is_superuser: bool = False
    address: Optional[str]


class User(UserDBBase, table=True):
    __tablename__ = 'users'
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: Optional[SecretStr] = Field(
        sa_column=Column(SecretStrSqL))
    resources: list['Resource'] = Relationship(back_populates='creator')
    groups: list[Group] = Relationship(
        back_populates='users', link_model=UserGroup
    )


class UserCreate(UserBase):
    password: SecretStr
    _password_check = validator('password', allow_reuse=True)(password_check)


class UserUpdateBase(BaseModel):
    """
    This is a "pydantic-only" model, to get around issue with SQLModel.
    SQLModel.dict(exclude_unset=True) is basically broken.
    https://github.com/tiangolo/sqlmodel/issues/87#issuecomment-965138135
    """
    email: Optional[EmailStr]
    first_name: Optional[str] = Field(default=None)
    last_name: Optional[str]
    display_name: Optional[str]
    role: Optional[Role]
    password: Optional[SecretStr]


class UserUpdate(UserUpdateBase):
    _password_check = validator('password', allow_reuse=True)(password_check)


class UserRead(UserBase):
    id: int
    is_superuser: bool


"""
Resources
"""


class ResourceFormat(str, enum.Enum):
    flashcard = 'flashcard'
    pdf = 'pdf'


class ResourceBase(SQLModel):
    name: str
    private: bool = True
    format: ResourceFormat = ResourceFormat.flashcard


class Resource(ResourceBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    creator_id: Optional[int] = Field(default=None, foreign_key='users.id')
    creator: Optional[User] = Relationship(back_populates='resources')
    standards: list['Standard'] = Relationship(
        back_populates='resources',link_model=StandardResource,
    )
    cards: list['Card'] = Relationship(back_populates='resource')
    goals: list['Goal'] = Relationship(
        back_populates='resources', link_model=GoalResource
    )


class ResourceCreateExternal(ResourceBase):
    pass


class ResourceCreateInternal(ResourceCreateExternal):
    creator_id: Optional[int]  # depends on get_current_user()


class ResourceUpdate(ResourceBase):
    pass


class ResourceRead(ResourceBase):
    id: int


class ResourceReadWithCreator(ResourceRead):
    creator: Optional[UserRead]


class ResourceReadMultiWithCreator(SQLModel):
    resources: list[ResourceRead] = Field(
        default=[], exclude={'__all__': {'creator_id'}}
    )
    creator: Optional[UserRead]


class UserReadWithResources(UserRead):
    resources: list[ResourceRead] = []


"""
Cards
"""


class CardBase(SQLModel):
    question: str
    answer: str


class Card(CardBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True,
                              sa_column_kwargs=dict(autoincrement=True))
    resource_id: Optional[int] = Field(default=None, foreign_key='resource.id')
    resource: Resource = Relationship(back_populates='cards')
    # attempts: list['Attempt'] = Relationship(back_populates='card')
    __table_args__ = (UniqueConstraint('id', 'resource_id'),)


class CardCreate(CardBase):
    resource_id: Optional[int]


class CardUpdate(CardBase):
    pass


class CardRead(CardBase):
    id: int


class CardReadWithResource(CardRead):
    resource: ResourceRead


class ResourceReadWithCards(ResourceRead):
    cards: list[CardRead] = []


"""
Standards
"""


class Subject(str, enum.Enum):
    math = 'math'
    ela = 'ela'


class TopicBase(SQLModel):
    description: str


class Topic(TopicBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    standards: list['Standard'] = Relationship(back_populates='topic')


class TopicCreate(TopicBase):
    pass


class TopicUpdate(TopicBase):
    pass


class TopicRead(TopicBase):
    pass


class StandardBase(SQLModel):
    template: str
    grade: int
    subject: Subject


class Standard(StandardBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    topic_id: int = Field(foreign_key='topic.id')
    topic: Topic = Relationship(back_populates='standards')
    resources: list['Resource'] = Relationship(
        back_populates='standards', link_model=StandardResource
    )
    goals: list['Goal'] = Relationship(back_populates='standard')


class StandardCreate(StandardBase):
    topic_id: int


class StandardUpdate(StandardBase):
    pass


class StandardRead(StandardBase):
    topic: Topic


class ResourceReadWithStandards(ResourceRead):
    standards: list[StandardRead] = []


"""
Goals
"""


class GoalBase(SQLModel):
    start_date: date = None
    end_date: FutureDate
    accuracy: Optional[PositiveFloat]
    n_trials: Optional[PositiveInt]

    @validator('accuracy')
    def accuracy_le_100(cls, v):
        if v and v > 100:
            raise ValueError('accuracy cannot be great than 100.')
        return v


class Goal(GoalBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    teacher_id: Optional[int] = Field(foreign_key='users.id')
    student_id: Optional[int] = Field(foreign_key='users.id')
    standard_id: Optional[int] = Field(foreign_key='standard.id')
    teacher: User = Relationship(
        sa_relationship_kwargs=dict(foreign_keys='[Goal.teacher_id]')
    )
    student: User = Relationship(
        sa_relationship_kwargs=dict(foreign_keys='[Goal.student_id]')
    )
    standard: Standard = Relationship(back_populates='goals')
    resources: list[Resource] = Relationship(
        back_populates='goals', link_model=GoalResource,
        # sa_relationship_kwargs=dict(passive_deletes='all')
    )


class GoalCreate(GoalBase):
    teacher_id: Optional[int]  # Depends on current user, should be teacher.
    student_id: int
    standard_id: int
    group_id: int


class GoalUpdate(GoalBase):
    pass


class GoalRead(GoalBase):
    id: int
    teacher: UserRead
    student: UserRead
    standard: StandardRead


class GoalReadWithResources(GoalRead):
    resources: list[ResourceReadWithCards]


"""
Laps
"""


class LapBase(SQLModel):
    start_ts: Optional[datetime] = Field(default_factory=datetime.utcnow)
    end_ts: Optional[datetime] = None
    score: Optional[float] = None


class Lap(LapBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True,
                              sa_column_kwargs=dict(autoincrement=True))
    goal_id: Optional[int] = Field(default=None)  # part of composite FK
    resource_id: Optional[int] = Field(default=None)  # part of composite FK
    goal_resource: GoalResource = Relationship(back_populates='laps')
    goal: Goal = Relationship(
        sa_relationship_kwargs=dict(
            primaryjoin='foreign(Lap.goal_id)==Goal.id',
            viewonly=True
        )
    )
    resource: Resource = Relationship(
        sa_relationship_kwargs=dict(
            primaryjoin='foreign(Lap.resource_id)==Resource.id',
            viewonly=True
        )
    )
    attempts: list['Attempt'] = Relationship(back_populates='lap')

    __table_args__ = (ForeignKeyConstraint(
        ['goal_id', 'resource_id'],
        ['goal_resource.goal_id', 'goal_resource.resource_id']),
    )  # makes a goal resource un-deletable unless not in use on lap.


class LapCreate(LapBase):
    goal_id: int
    resource_id: int


class LapUpdate(LapBase):
    pass


class LapRead(LapBase):
    id: int
    goal: GoalRead
    resource: ResourceReadWithCards


class LapReadMinimal(LapBase):
    id: int
    goal_id: int
    resource_id: int


"""
Attempts
"""


class AttemptBase(SQLModel):
    submission: str  # The student's response


class Attempt(AttemptBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True,
                              sa_column_kwargs=dict(autoincrement=True))
    lap_id: Optional[int] = Field(default=None, primary_key=True,
                                  foreign_key='lap.id')
    card_id: Optional[int] = Field(default=None, primary_key=True,
                                   foreign_key='card.id')
    correct: Optional[bool]  # validated on attempt post
    lap: 'Lap' = Relationship(back_populates='attempts')
    card: 'Card' = Relationship(
        sa_relationship_kwargs=dict(primaryjoin='Attempt.card_id==Card.id')
    )


class AttemptCreateExternal(AttemptBase):
    lap_id: int
    card_id: int


class AttemptCreateInternal(AttemptCreateExternal):
    correct: Optional[bool]


class AttemptUpdate(AttemptBase):
    pass


class AttemptRead(AttemptBase):
    correct: bool
    card: CardRead


class AttemptReadWithLap(AttemptRead):
    lap: LapReadMinimal


class LapReadWithAttempts(LapRead):
    attempts: list[AttemptRead] = []
