import logging
from typing import Any, Union, Optional

from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlmodel import Session

from app import crud
from app.deps import get_session, get_current_user, BatchQueryParams
from app.models import (
    Resource, ResourceRead, ResourceReadWithCreator, ResourceCreateExternal, User,
    ResourceUpdate, StandardResourceCreate, ResourceReadWithStandards,
    ResourceReadMultiWithCreator, ResourceStandardsMultiCreate,
    ResourceCreateInternal
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post('/', status_code=201, response_model=ResourceReadWithCreator)
def create_resource(
        *,
        resource_in: ResourceCreateExternal,
        current_user: User = Depends(get_current_user),
        session: Session = Depends(get_session)
) -> Any:
    """
    Create a Resource, for the current logged-in User
    """
    resource_in = ResourceCreateInternal.from_orm(resource_in)
    resource_in.creator_id = current_user.id
    return crud.resource.create(session, obj_in=resource_in)


@router.post('/standard-link/', response_model=ResourceReadWithStandards)
def add_standard_link(
        *,
        std_rsc_in: StandardResourceCreate,
        current_user: User = Depends(get_current_user),
        session: Session = Depends(get_session)
) -> Any:
    """
    Relate a single Resource to a single Standard by id. User can only link
    their own resources (public or private) to a standard.
    """
    std_id, rsc_id = std_rsc_in.standard_id, std_rsc_in.resource_id
    resource = crud.resource.get(session, rsc_id)
    if not resource:
        raise HTTPException(404, f'Resource with ID {rsc_id} not found')
    standard = crud.standard.get(session, std_id)
    if not standard:
        raise HTTPException(404, f'Standard with ID {std_id} not found')
    if resource.creator_id != current_user.id:
        raise HTTPException(401,
                            f'Not creator of Resource with ID {resource.id}.')

    resource.standards.append(standard)
    return crud.resource.refresh(session, resource)


@router.post('/standard-link/multi', response_model=ResourceReadWithStandards)
def add_multi_standard_link(
        *,
        rsc_stds_in: ResourceStandardsMultiCreate,
        ignore_non_exist_stds: bool = False,
        current_user: User = Depends(get_current_user),
        session: Session = Depends(get_session)
):
    """
    Relate a single Resource to multiple Standards at once. User can only link
    own resources (public or private) to the standards. If some provided
    standard IDs do not exist, no linking will occur and endpoint will return
    404, unless user explicitly defines 'ignore_non_exist_stds=true'. In that
    case resources will be linked to any provided standards which exist. If
    NO standards exist with the provided IDs, returns 404.
    """
    rsc_id, std_ids = rsc_stds_in.resource_id, set(rsc_stds_in.standard_ids)
    resource = crud.resource.get(session, rsc_id)
    standards = crud.standard.get_mult_by_ids(session, std_ids)

    if not resource:
        raise HTTPException(404, f'Resource with ID {rsc_id} not found')
    if not standards:
        raise HTTPException(404, f'Any Standards with IDs {std_ids} not found')
    if not ignore_non_exist_stds and len(standards) < len(std_ids):
        std_ids_not_found = list(std_ids - set(s.id for s in standards))
        raise HTTPException(
            404, f'Some Standard IDs found, but {std_ids_not_found} not found.'
                 f' Provide ignore_non_exist_stds=true to force link creation'
                 f' to standards that exist in standard_ids list.')
    if resource.creator != current_user:
        raise HTTPException(401,
                            f'Not creator of Resource with ID {resource.id}.')
    resource.standards.extend(standards)
    return crud.resource.refresh(session, resource)


@router.get('/{resource_id}', status_code=200,
            response_model=ResourceReadWithCreator)
def fetch_resource(
        *,
        resource_id: int,
        current_user: User = Depends(get_current_user),
        session: Session = Depends(get_session)
) -> Any:
    """
    Get a single Resource by ID. Current user must be the creator of the
    resource, or the resource must be public. If resource is accessible but
    not created by the current user, does not return creator info.
    """
    logger.debug(f'fetch_resource({resource_id=}, {current_user=})')
    resource = crud.resource.get(session, resource_id)
    if (resource and
            resource.private and
            resource.creator != current_user):
        raise HTTPException(401,
                            f'Not creator of Resource with ID {resource_id}.')
    elif not resource:
        raise HTTPException(404, f'Resource with ID {resource_id} not found')
    if resource.creator != current_user:
        return resource.dict(exclude={'creator'})
    return resource


@router.get('/', status_code=200, response_model=list[ResourceRead])
def fetch_all_resources(
        standard_id: Optional[int] = None,
        include_public: Optional[bool] = False,
        batch: BatchQueryParams = Depends(),
        current_user: User = Depends(get_current_user),
        session: Session = Depends(get_session)) -> Any:
    """
    Get all resources created by current logged-in user. Can be filtered by
    adding standard_id query string. If standard_id is included, user may
    also choose to include_public resources that apply to that standard. If
    'include_public' is marked as True but no standard id is given, it will
    have no effect and simply all resources created by the user will still be
    returned. Creator info (your info) is only returned if no public resources
    are requested.
    """
    if not standard_id:
        resources = current_user.resources
    else:
        standard = crud.standard.get(session, standard_id)
        if not standard:
            raise HTTPException(404,
                                f'Standard with ID {standard_id} not found')
        resources = [r for r in standard.resources
                     if r.creator == current_user or
                     (include_public and not r.private)]

    return resources[batch.skip: batch.limit + batch.skip]


@router.patch('/{resource_id}', status_code=200, response_model=ResourceRead)
def update_resource(
        *,
        resource_id: int,
        resource_in: ResourceUpdate,
        current_user: User = Depends(get_current_user),
        session: Session = Depends(get_session)
) -> Any:
    """Update a resource that belongs to logged-in user"""
    db_resource = session.get(Resource, resource_id)
    if db_resource.creator != current_user:
        raise HTTPException(401,
                            f'Not creator of Resource with ID {resource_id}.')
    return crud.resource.update(
        session, db_obj=db_resource, obj_in=resource_in
    )
