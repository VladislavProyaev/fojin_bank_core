from api import UserModel
from api.models.permission_type_model import PermissionTypeModel
from api.models.permission_user_model import PermissionUserModel
from common.constants.permissions import Permissions


def check_permission(user_id: int, action: str) -> bool:
    user_model = UserModel.get(user_id=user_id)
    permission_type_model = get_high_user_permission(user_model)

    permission_user_model = PermissionUserModel.get(
        user=user_model, permission_type=permission_type_model
    )
    if permission_user_model is None:
        return False

    permission_type = Permissions.get_permission(
        permission_type_model.permission_type
    )
    if action in permission_type.permission_actions:
        return True

    return False


def get_high_user_permission(user_model: UserModel) -> PermissionTypeModel:
    user_permissions: list[PermissionTypeModel] = user_model.permissions
    user_permissions.sort(key=lambda perm: perm.priority, reverse=True)

    return user_permissions[0]
