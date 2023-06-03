from .models import *
from ninja import Schema
from common.api import *
from oauth2_provider.decorators import protected_resource
from ninja.security import django_auth
from django.contrib.auth.decorators import login_required
from catalog.common.models import *
from typing import List
from ninja.pagination import paginate
from ninja import Field
from datetime import datetime
from django.utils import timezone


class MarkSchema(Schema):
    shelf_type: ShelfType
    visibility: int = Field(ge=0, le=2)
    item: ItemSchema
    created_time: datetime
    comment_text: str | None
    rating_grade: int | None = Field(ge=1, le=10)
    tags: list[str]


class MarkInSchema(Schema):
    shelf_type: ShelfType
    visibility: int = Field(ge=0, le=2)
    comment_text: str | None
    rating_grade: int | None = Field(ge=1, le=10)
    tags: list[str] = []
    created_time: datetime | None
    post_to_fediverse: bool = False


@api.get("/me/shelf", response={200: List[MarkSchema], 403: Result})
@protected_resource()
@paginate(PageNumberPagination)
def list_marks_on_shelf(
    request, type: ShelfType, category: AvailableItemCategory | None = None
):
    """
    Get holding marks on current user's shelf

    Shelf's `type` should be one of `wishlist` / `progress` / `complete`;
    `category` is optional, all marks will be returned if not specified.
    """
    queryset = request.user.shelf_manager.get_latest_members(
        type, category
    ).prefetch_related("item")
    return queryset


@api.get(
    "/me/shelf/item/{item_uuid}",
    response={200: MarkSchema, 403: Result, 404: Result},
    auth=OAuthAccessTokenAuth(),
)
# @protected_resource()
def get_mark_by_item(request, item_uuid: str):
    """
    Get holding mark on current user's shelf by item uuid
    """
    item = Item.get_by_url(item_uuid)
    if not item:
        return 404, {"message": "Item not found"}
    shelfmember = request.user.shelf_manager.locate_item(item)
    if not shelfmember:
        return 404, {"message": "Mark not found"}
    return shelfmember


@api.post(
    "/me/shelf/item/{item_uuid}", response={200: Result, 403: Result, 404: Result}
)
@protected_resource()
def mark_item(request, item_uuid: str, mark: MarkInSchema):
    """
    Create or update a holding mark about an item for current user.

    `shelf_type` and `visibility` are required; `created_time` is optional, default to now.
    if the item is already marked, this will update the mark.

    updating mark without `rating_grade`, `comment_text` or `tags` field will clear them.
    """
    item = Item.get_by_url(item_uuid)
    if not item:
        return 404, {"message": "Item not found"}
    m = Mark(request.user, item)
    try:
        TagManager.tag_item_by_user(item, request.user, mark.tags, mark.visibility)
        m.update(
            mark.shelf_type,
            mark.comment_text,
            mark.rating_grade,
            mark.visibility,
            created_time=mark.created_time,
            share_to_mastodon=mark.post_to_fediverse,
        )
    except ValueError as e:
        pass  # ignore sharing error
    return 200, {"message": "OK"}


@api.delete(
    "/me/shelf/item/{item_uuid}", response={200: Result, 403: Result, 404: Result}
)
@protected_resource()
def delete_mark(request, item_uuid: str):
    """
    Remove a holding mark about an item for current user.
    """
    item = Item.get_by_url(item_uuid)
    if not item:
        return 404, {"message": "Item not found"}
    m = Mark(request.user, item)
    m.delete()
    TagManager.tag_item_by_user(item, request.user, [], 0)
    return 200, {"message": "OK"}


# @api.get("/me/review/")
# @api.get("/me/review/item/{item_uuid}")
# @api.post("/me/review/item/{item_uuid}")
# @api.delete("/me/review/item/{item_uuid}")

# @api.get("/me/collection/")
# @api.get("/me/collection/{uuid}")
# @api.post("/me/collection/{uuid}")
# @api.delete("/me/collection/{uuid}")
# @api.get("/me/collection/{uuid}/items")
# @api.post("/me/collection/{uuid}/items")
# @api.delete("/me/collection/{uuid}/items")
# @api.patch("/me/collection/{uuid}/items")
