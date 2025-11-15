r"""
\file gui/assets.py

\brief Asset management utility functions for DTG GUI

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
import sys
from pathlib import Path
from PIL import Image, ImageTk

# Determine the base directory depending on whether the script is frozen or not
if getattr(sys, 'frozen', False):
    # if frozen (e.g., PyInstaller) the base dir is the temp folder created by PyInstaller
    BASE_DIR = Path(sys._MEIPASS)
else:
    # if not frozen, use the script's directory
    BASE_DIR = Path(__file__).parent.parent

# Images directory
IMAGE_DIR = BASE_DIR / "images"


def load_image(path, size=(20, 20)):
    try:
        img = Image.open(path)
        img = img.resize(size)
        return ImageTk.PhotoImage(img)
    except (FileNotFoundError, OSError):
        return None
