from django.contrib.auth.models import User

from backend.models import Account


class UserService:
    def create(self, username):
        # Create the user and account if no account/user exists
        user = self.get_user(username)
        if user is None:
            user = User(username=username)
            user.set_unusable_password()
            user.save()

        # The Account is an extension of the User model (known as a profile model)
        # that allows for custom attributes. If an account exists, a django user
        # also exists
        account = self.get(username)
        if account is None:
            account = Account(owner=username, user=user)
            account.save()

        return account

    def get(self, username):
        if Account.objects.filter(owner=username).exists() == True:
            return Account.objects.filter(owner=username)[0]

    def get_or_create(self, username):
        return self.create(username)

    def get_user(self, username):
        if User.object.filter(username=username).exists == True:
            return User.objects.filter(username=username)[0]


user_service = UserService()