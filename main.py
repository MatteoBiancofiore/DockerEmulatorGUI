r"""
\file main.py

\brief Entry point of DTG project. It creates the main window and starts the application.

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

import tkinter as tk
import sys

 # Import application class
from app import DTGApp

if __name__ == "__main__": # main entry point
    try:
        root = tk.Tk()
        app = DTGApp(root) # CREATE app istance
        app.run()                     # execute
    
    except Exception as e:
        print(f"Error {e}", file=sys.stderr)
        try:
            root.withdraw() # Hide window if it exists
            tk.messagebox.showerror("Fatal Error", f"Application will close.\n\n{e}")
        except:
            pass
        sys.exit(1)