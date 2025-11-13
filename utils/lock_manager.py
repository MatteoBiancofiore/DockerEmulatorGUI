# utils/lock_manager.py

# class to lock operations on containers
class OperationLock:
    def __init__(self):
        self._locks = {}

    def lock(self, container_id, op):
        if self._locks.get(container_id, {}).get("running", False):
            return False # already locked
        
        self._locks[container_id] = {"running": True, "operation": op}
        return True

    def unlock(self, container_id):
        self._locks[container_id] = {"running": False, "operation": None}

    def is_locked(self, container_id):
        return self._locks.get(container_id, {}).get("running", False)
    
    # return true if any lock is active
    def has_active_locks(self):
        return any(v.get("running", False) for v in self._locks.values())