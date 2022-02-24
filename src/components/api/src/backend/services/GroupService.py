from backend.models import Group, GroupUser


class GroupService:
    def user_in_group(self, username, group_id):
        # Get all the groups the user belongs to
        group_users = GroupUser.objects.filter(username=username)
        group_ids = [ group_user.group_id for group_user in group_users ]

        if group_id in group_ids:
            return True

        return False

    def user_owns_group(self, username, group_id):
        return Group.objects.filter(id=group_id, owner=username).exists()

    def get(self, group_id):
        return Group.objects.filter(id=group_id).first()

service = GroupService()