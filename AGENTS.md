# Organizador de Archivos - Agent Instructions

## Project Overview

**Purpose:** A Python file organization tool with a tkinter GUI that automatically categorizes and organizes files into folders based on file extension types or AI analysis.

**Language:** Python 3.x | **GUI Framework:** Tkinter | **AI Backend:** Google Gemini API

## Architecture

### Core Modules

- **organizador_archivos.py** - Main GUI application with file organization logic
  - Core functions: file listing, classification, organization, duplicate detection
  - GUI implementation using tkinter with text logging and progress bar
  - Undo functionality through movement tracking
  
- **categorias.py** - Comprehensive file extension-to-category mapping
  - 100+ file extensions organized by type (Images, Documents, Audio, Video, 3D, CAD, etc.)
  - Used as fallback classification when AI is unavailable
  
- **ia_clasificador.py** - AI-based file classification module
  - Uses Google Gemini 2.0 Flash API for intelligent file naming analysis
  - Requires GEMINI_API_KEY in .env file
  - Returns category topic (e.g., "technology", "music", "legal") or empty string on failure

## Setup & Dependencies

### Python Environment
- Uses virtual environment in `newvenv/`
- Activate before running: `newvenv\Scripts\Activate.ps1` (Windows PowerShell)

### Required Packages
```
tkinter (built-in)
pathlib (built-in)
hashlib (built-in)
send2trash >= 2.1.0  (safe file deletion)
google-generativeai  (for Gemini API)
python-dotenv        (for .env configuration)
```

### Configuration
Create a `.env` file in the project root with:
```
GEMINI_API_KEY=your_api_key_here
```

## Key Implementation Details

### File Organization Flow
1. **Classify** - Each file extension is mapped to a category via `categorias` dict
2. **Categorize** - Files are organized into category-named subdirectories
3. **Handle conflicts** - Files with name collisions get numbered (file_1.pdf, file_2.pdf, etc.)
4. **Track movements** - All file movements are logged for undo functionality

### Duplicate Detection Algorithm
1. **Group by size** - Performance optimization (avoid unnecessary hashing)
2. **Hash verification** - MD5 hashing to confirm true duplicates
3. **User action** - Move to "Duplicados" folder or delete to trash

### GUI Features
- **Simulation mode** - Preview operations without executing
- **Progress tracking** - Visual feedback during file processing
- **Logging** - All actions logged to text widget with auto-scroll
- **Undo support** - Reverses last batch of file movements

## Common Patterns & Conventions

### Callback-Based Logging
Functions accept optional `registro` (logging callback) parameter:
```python
def organizar_archivos(ruta, simulacion=False, registro=None, progreso=None):
    if registro:
        registro(f"Processing: {archivo.name}")
```

### Path Handling
- Always use `pathlib.Path` for cross-platform compatibility
- Check file existence with `.exists()` before operations
- Use `.suffix.lower()` for consistent extension matching

### Error Handling
- Gracefully handle missing files and permission errors
- Collect errors in a list and return alongside success count
- Wrap file I/O in try-except blocks

### UI/UX Conventions
- Messages prefixed with emoji for visual clarity (✅, ❌, 🔄, 📂, etc.)
- Spanish language throughout (user's preference)
- Include file/folder names in all user-facing messages

## Important Considerations

### Performance
- Large file operations can block GUI; consider threading for big directories
- MD5 hashing on large files may be slow; current size-grouping is a good optimization
- Monitor memory usage during recursive directory scanning

### Error Cases
- Files locked by other processes
- Permission denied when moving files
- Special characters in file names (especially on Windows)
- Missing or malformed .env file (API unavailable gracefully)

### API Rate Limiting
- Gemini API has rate limits; handle gracefully
- Falls back to extension-based classification if API fails
- Each filename analysis makes an API call (optimize if processing many files)

## Development Workflow

### Running the Application
```bash
# Activate virtual environment
newvenv\Scripts\Activate.ps1

# Run GUI
python organizador_archivos.py
```

### Adding New Categories
1. Edit `categorias.py` dictionary
2. Add extension → category mappings
3. Category folders are created automatically during organization

### Testing Strategies
- Test with dummy files before processing real directories
- Always use simulation mode first to preview operations
- Verify undo functionality works correctly
- Test edge cases: empty files, special chars, permission issues

## File Structure Expectations

```
d:\Trabajos\organizador_archivos/
├── organizador_archivos.py  (main application)
├── categorias.py            (extension mappings)
├── ia_clasificador.py       (AI classification)
├── .env                     (API configuration)
├── newvenv/                 (Python virtual environment)
└── __pycache__/             (Python cache)
```

## When Enhancing This Project

- **New classification method?** Add to `ia_clasificador.py` and integrate with classification logic
- **GUI improvements?** Modify tkinter widgets in `organizador_archivos.py` main section
- **New file types?** Extend the `categorias` dictionary in `categorias.py`
- **Performance issues?** Consider threading for heavy I/O; profile with large datasets
- **Platform-specific bugs?** Use pathlib and test on target OS before deployment
