r"""
\file utils/lock_manager.py

\brief Lock manager for asynchronous operations

\copyright Copyright (c) 2025, Alma Mater Studiorum, University of Bologna, All rights reserved.
	
\par License

    This file is part of DTG (DTN Testbed GUI).

    DTG is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    
    DTG is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    
    You should have received a copy of the GNU General Public License
    along with DTG.  If not, see <http://www.gnu.org/licenses/>.

\author Matteo Biancofiore <matteo.biancofiore2@studio.unibo.it>
\date 13/11/2025

\par Supervisor
   Carlo Caini <carlo.caini@unibo.it>


\par Revision History:
| Date       |  Author         |   Description
| ---------- | --------------- | -----------------------------------------------
| 13/11/2025 | M. Biancofiore  |  Initial implementation for DTG project.
"""

class OperationLock:
    r"""
    \brief Manager used to handle concurrency and operation locks on containers

    The OperationLock prevents race conditions and conflictual action on containers
    by ensuring that only one operation (start, stop, restart) can be performed 
    at a time on a specific container.
    """
    
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