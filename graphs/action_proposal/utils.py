from enum import StrEnum

class ActionType(StrEnum):
    CREATE_FOLLOW_UP_TASK = "create_follow_up_task"
    CREATE_STAFF = "create_staff"
    UPDATE_STAFF = "update_staff" 
    DELETE_STAFF = "delete_staff"