from django.forms.models import model_to_dict

from backend.views.RestrictedAPIView import RestrictedAPIView


class Pipelines(RestrictedAPIView):
    def get(self, _, name):
        pass
        # # Get a list of the groups if name is not set
        # if name is None:
        #     # Geet all the objects
        #     query_set = Group.objects.all()

        #     groups = []
        #     for group in query_set:
        #         groups.append(model_to_dict(group))

        #     return BaseResponse(result=groups)

        # # Return the group by the name provided in the path params
        # group = Group.objects.filter(name=name).first()
        # if group is None:
        #     return NotFound(f"Group does not exist with name '{name}'")

        # return BaseResponse(result=model_to_dict(group))