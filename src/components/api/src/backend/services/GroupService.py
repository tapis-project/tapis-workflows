from typing import Union

from backend.models import Group, GroupUser


class GroupService:
    def user_in_group(self, username, group_id, is_admin: Union[bool, None]=None):
        kwargs = {}
        if is_admin is not None:
            kwargs["is_admin"] = is_admin

        # Get all the group user object for this user
        return GroupUser.objects.filter(
            username=username, group_id=group_id, **kwargs).exists()

    def user_owns_group(self, username, group_id):
        return Group.objects.filter(id=group_id, owner=username).exists()

    def get(self, group_id):
        return Group.objects.filter(id=group_id).first()

service = GroupService()