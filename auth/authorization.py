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
    """
    Return whether a role is allowed to use a permission.

    Unknown role values are treated as unauthorized.

    Args:
        role: Staff role, as a `Role` or its string value.
        permission: Permission to check.

    Returns:
        `True` if the role includes the permission, otherwise `False`.
    """
    try:
        role = Role(role)
    except ValueError:
        return False 
    
    return permission in ROLE_PERMISSIONS.get(role, set()) 


def require_permission(role: Role | str, permission: Permission) -> None:
    """
    Raise if a role does not have the given permission.

    Args:
        role: Staff role, as a `Role` or its string value.
        permission: Permission that must be granted.

    Raises:
        PermissionError: If the role is missing the permission.
    """
    if not has_permission(role, permission):
        raise PermissionError(f"Role '{role}' does not have permission '{permission.value}'.")