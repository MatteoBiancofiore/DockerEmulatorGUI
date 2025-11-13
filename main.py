# main.py
import tkinter as tk
import sys
from app import DTGApp # Import application class

if __name__ == "__main__":
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