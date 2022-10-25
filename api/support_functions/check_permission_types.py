from api.models.permission_type_model import PermissionTypeModel
from common.constants.permissions import PermissionTypes, PermissionType
from services import sql


def check_permission_types():
    permission_type_count = len(PermissionTypes.values())
    permission_type_model_count = sql.session.query(PermissionTypeModel).count()

    if permission_type_count != permission_type_model_count:
        for permission_type in PermissionTypes.values():
            permission_type: PermissionType

            PermissionTypeModel.get_or_create(
                permission_type=permission_type.permission,
                priority=permission_type.priority
            )