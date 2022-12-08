from dataclasses import dataclass

from common.constants.base_constant import BaseConstant


@dataclass(slots=True)
class Permission:
    permission_type: str
    permission_actions: list[str]


class PermissionTypes(BaseConstant):
    CLIENT = 'client'
    MODERATOR = 'moderator'
    ADMINISTRATOR = 'administrator'


class PermissionActions(BaseConstant):
    VIEW_PROFILE = 'view profile'
    VIEW_ALL_PROFILES = 'view all profiles'
    ASSIGN_ADMINISTRATOR = 'assign administrator'
    CREATE_TRANSFER = 'create transfer'
    CREATE_ACCOUNT = 'create account'


class Permissions(BaseConstant):
    CLIENT = Permission(
        PermissionTypes.CLIENT,
        [
            PermissionActions.CREATE_TRANSFER,
            PermissionActions.CREATE_ACCOUNT,
            PermissionActions.VIEW_PROFILE
        ]
    )

    MODERATOR = Permission(
        PermissionTypes.MODERATOR,
        [
            PermissionActions.VIEW_ALL_PROFILES,
            PermissionActions.VIEW_PROFILE
        ]
    )

    ADMINISTRATOR = Permission(
        PermissionTypes.ADMINISTRATOR,
        [
            PermissionActions.VIEW_ALL_PROFILES,
            PermissionActions.ASSIGN_ADMINISTRATOR,
            PermissionActions.VIEW_PROFILE
        ]
    )

    @classmethod
    def get_permission(cls, permission_type_str: str) -> Permission:
        for permission in cls.values():
            permission: Permission
            if permission.permission_type == permission_type_str:
                return permission
