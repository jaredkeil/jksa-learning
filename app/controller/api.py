from fastapi import APIRouter

from .endpoints import (auth, user, resource, standard, topic, card, goal,
                        lap, attempt)

api_router = APIRouter()

api_router.include_router(auth.router,
                          prefix='/auth',
                          tags=['login, signup'])

api_router.include_router(user.router,
                          prefix='/user',
                          tags=['user'])

api_router.include_router(resource.router,
                          prefix='/resource',
                          tags=['resource'])

api_router.include_router(standard.router,
                          prefix='/standard',
                          tags=['standard'])

api_router.include_router(topic.router,
                          prefix='/topic',
                          tags=['topic'])

api_router.include_router(card.router,
                          prefix='/card',
                          tags=['card'])

api_router.include_router(goal.router,
                          prefix='/goal',
                          tags=['goal'])

api_router.include_router(lap.router,
                          prefix='/lap',
                          tags=['lap'])

api_router.include_router(attempt.router,
                          prefix='/attempt',
                          tags=['attempt'])
