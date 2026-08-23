from enum import StrEnum 

class Permission(StrEnum):
    READ_DOCUMENTS = "read_documents"
    READ_OPERATIONAL_DATA = "read_operational_data"
    WRITE_OPERATIONAL_DATA = "write_operational_data"
    MANAGE_FOLLOW_UP_TASKS = "manage_follow_up_tasks"

    READ_STAFF = "read_staff"
    MANAGE_STAFF = "manage_staff"

class Role(StrEnum):
    SUPPORT = "SUPPORT"
    OPERATIONS = "OPERATIONS"
    ADMIN = "ADMIN"


ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.SUPPORT: {
        Permission.READ_DOCUMENTS,
        Permission.READ_OPERATIONAL_DATA,
        # Permission.WRITE_OPERATIONAL_DATA,
        Permission.MANAGE_FOLLOW_UP_TASKS,
    },

    Role.OPERATIONS: {
        Permission.READ_DOCUMENTS,
        Permission.READ_OPERATIONAL_DATA,
        Permission.MANAGE_FOLLOW_UP_TASKS,       
        Permission.WRITE_OPERATIONAL_DATA,
    },

    Role.ADMIN: {
        Permission.READ_DOCUMENTS,
        Permission.READ_OPERATIONAL_DATA,
        Permission.WRITE_OPERATIONAL_DATA,
        Permission.MANAGE_FOLLOW_UP_TASKS,
        Permission.MANAGE_STAFF,
        Permission.READ_STAFF,
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