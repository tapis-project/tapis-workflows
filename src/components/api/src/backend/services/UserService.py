from django.contrib.auth.models import User

from backend.models import Account


class UserService:
    def create_if_not_exists(self, username):
        # The Account is an extension of the User model (known as a profile model)
        # that allows for custom attributes. If an account exists, a django user
        # also exists
        account = Account.objects.filter(owner=username)[0]

        # Create the user and account if no account/user exists
        if account is None:
            user = User(username=username)
            user.set_unusable_password()
            user.save()

            account = Account(owner=username, user=user)
            account.save()

        return account

    def get_or_create(self, username):
        return self.create_if_not_exists(username)


user_service = UserService()