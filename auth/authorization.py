from enum import StrEnum 

class Permission(StrEnum):
    READ_DOCUMENTS = "read_documents"
    READ_OPERATIONAL_DATA = "read_operational_data"
    CREATE_FOLLOW_UP_TASK = "create_follow_up_task"

    MANAGE_STAFF = "manage_staff"
    MANAGE_ACCESS = "manage_access"
    MANAGE_ROLES = "manage_roles"

    READ_STAFF = "read_staff"

class Role(StrEnum):
    SUPPORT = "SUPPORT"
    OPERATIONS = "OPERATIONS"
    ADMIN = "ADMIN"


ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.SUPPORT: {
        Permission.READ_DOCUMENTS,
        Permission.READ_OPERATIONAL_DATA,
        # Permission.CREATE_FOLLOW_UP_TASK,
    },

    Role.OPERATIONS: {
        Permission.READ_DOCUMENTS,
        Permission.READ_OPERATIONAL_DATA,
        Permission.CREATE_FOLLOW_UP_TASK,
    },

    Role.ADMIN: {
        Permission.READ_DOCUMENTS,
        Permission.READ_OPERATIONAL_DATA,
        Permission.CREATE_FOLLOW_UP_TASK,
        Permission.MANAGE_STAFF,
        Permission.READ_STAFF,
        Permission.MANAGE_ACCESS,
        Permission.MANAGE_ROLES,
    },
}


def has_permission(role: Role | str, permission: Permission) -> bool:
    try:
        role = Role(role)
    except ValueError:
        return False 
    
    return permission in ROLE_PERMISSIONS.get(role, set()) 


def require_permission(role: Role | str, permission: Permission) -> None:
    if not has_permission(role, permission):
        raise PermissionError(f"Role '{role}' does not have permission '{permission.value}'.")