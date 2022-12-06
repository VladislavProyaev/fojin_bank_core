from api.models.permission_type_model import PermissionTypeModel
from common.constants.permissions import PermissionTypes
from common.transaction import Transaction
from services import sql


def initialize_permission_types():
    permission_type_count = len(PermissionTypes.values())
    permission_type_model_count = sql.session.query(PermissionTypeModel).count()

    if permission_type_count != permission_type_model_count:
        with Transaction(sql) as transaction:
            for permission_type in PermissionTypes.values():
                PermissionTypeModel.get_or_create(
                    transaction.sql, permission_type=permission_type
                )
