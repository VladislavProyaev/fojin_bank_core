from api.models.permission_type_model import PermissionTypeModel
from common.constants.permissions import PermissionTypes
from services import sql


def initialize_permission_types():
    permission_type_count = len(PermissionTypes.values())
    permission_type_model_count = sql.session.query(PermissionTypeModel).count()

    if permission_type_count != permission_type_model_count:
        with sql.client.begin():
            for permission_type in PermissionTypes.values():
                PermissionTypeModel.get_or_create(
                    sql, permission_type=permission_type
                )
