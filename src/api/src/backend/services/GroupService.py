from typing import Union

from backend.models import Group, GroupUser
from backend.conf.constants import PERMITTED_SERVICES


class GroupService:
    def user_in_group(self, username, group_id, tenant_id, is_admin: Union[bool, None]=None):
        # Grant access to all Group-level objects to all services
        if username in PERMITTED_SERVICES: return True
        
        kwargs = {}
        if is_admin is not None:
            kwargs["is_admin"] = is_admin

        # Get the group
        group = self.get(group_id, tenant_id)
        
        # Group does not exist, return false
        if group == None: return False

        # Get all the group user object for this user
        return GroupUser.objects.filter(
            username=username,
            group=group,
            **kwargs
        ).exists()

    def user_owns_group(self, username, group_id, tenant_id):
        return Group.objects.filter(
            id=group_id,
            owner=username,
            tenant_id=tenant_id
        ).exists()

    def get(self, group_id, tenant_id):
        return Group.objects.filter(
            id=group_id, tenant_id=tenant_id).first()

service = GroupService()