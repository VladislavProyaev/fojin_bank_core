from dataclasses import dataclass

from common.constants.base_constant import BaseConstant


@dataclass(slots=True)
class Permission:
    permission_type: str
    permission_actions: list[str]


@dataclass
class PermissionType(BaseConstant):
    permission: str
    priority: int


class PermissionTypes(BaseConstant):
    CLIENT = PermissionType('client', 0)
    MODERATOR = PermissionType('moderator', 1)
    ADMINISTRATOR = PermissionType('administrator', 2)


class PermissionActions(BaseConstant):
    VIEW_PROFILE = 'view profile'
    VIEW_ALL_PROFILES = 'view all profiles'
    ASSIGN_ADMINISTRATOR = 'assign administrator'
    CREATE_TRANSFER = 'create transfer'
    CREATE_ACCOUNT = 'create account'


class Permissions(BaseConstant):
    CLIENT = Permission(
        PermissionTypes.CLIENT.permission,
        [
            PermissionActions.CREATE_TRANSFER,
            PermissionActions.CREATE_ACCOUNT,
            PermissionActions.VIEW_PROFILE
        ]
    )

    MODERATOR = Permission(
        PermissionTypes.MODERATOR.permission,
        [
            PermissionActions.CREATE_TRANSFER,
            PermissionActions.CREATE_ACCOUNT,
            PermissionActions.VIEW_PROFILE,
            PermissionActions.VIEW_ALL_PROFILES
        ]
    )

    ADMINISTRATOR = Permission(
        PermissionTypes.ADMINISTRATOR.permission,
        [
            PermissionActions.CREATE_TRANSFER,
            PermissionActions.CREATE_ACCOUNT,
            PermissionActions.VIEW_PROFILE,
            PermissionActions.VIEW_ALL_PROFILES,
            PermissionActions.ASSIGN_ADMINISTRATOR
        ]
    )

    @classmethod
    def get_permission(cls, permission_type_str: str) -> Permission:
        for permission in cls.values():
            permission: Permission
            if permission.permission_type == permission_type_str:
                return permission
