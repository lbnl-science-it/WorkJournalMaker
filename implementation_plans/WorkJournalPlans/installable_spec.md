# Developer-Ready Specification: Cross-Platform Executable for Work Journal

## 1. Overview

The goal is to package the existing FastAPI web application into a standalone, installable executable that runs on Windows, macOS, and Linux. This will allow users to run the application locally without needing to install Python or any dependencies manually. The final output should be a single, self-contained executable file for each target platform.

## 2. Core Technologies

*   **Application Packager:** `PyInstaller` will be used to bundle the Python application and all its dependencies into a single executable.
*   **Production Web Server:** `Waitress` will be used as the production-ready WSGI server, replacing the `uvicorn` development server for the packaged application.

## 3. Application Modifications

### 3.1. Replace Development Server with Production Server

The main application entry point must be modified to use `Waitress` when running as a bundled executable. The development server (`uvicorn`) should only be used for local development.

**Action:**
*   Implement a check (e.g., `getattr(sys, 'frozen', False)`) to determine if the app is running in a bundled environment.
*   If bundled, start the application using `waitress.serve()`.
*   If not bundled, retain the existing `uvicorn` setup for development.

### 3.2. Dynamic Asset and Resource Path Resolution

A helper function is required to ensure the application can find the `templates` and `static` directories at runtime. When bundled with `PyInstaller`, these assets are extracted to a temporary directory, and paths must be resolved dynamically.

**Action:**
*   Create a `resource_path(relative_path)` function that uses `sys._MEIPASS` to construct the correct absolute path to assets when running in a bundled app.
*   Update all parts of the application that reference file paths (e.g., `Jinja2Templates`, `StaticFiles`, and any other file I/O) to use this helper function.

### 3.3. User-Specific Data Storage

To ensure data persistence and proper file system etiquette, user-specific data (like the SQLite database) must be stored in the standard application data directory for each operating system.

**Action:**
*   Integrate the `appdirs` library to determine the correct user data directory (`user_data_dir`).
*   On application startup, check if the directory exists and create it if it doesn't.
*   Modify the database connection logic to create and access the SQLite database file within this directory.
*   **Target Directories:**
    *   **Windows:** `C:\Users\<Username>\AppData\Roaming\WorkJournal`
    *   **macOS:** `/Users/<Username>/Library/Application Support/WorkJournal`
    *   **Linux:** `/home/<Username>/.config/WorkJournal`

## 4. Build Process

### 4.1. PyInstaller Spec File

A `WorkJournalMaker.spec` file will be created and used to provide a consistent and version-controllable build configuration.

**Action:**
*   Generate a base spec file using `pyi-makespec`.
*   Modify the spec file with the following configurations.

### 4.2. Build Configuration

*   **Single-File Executable:** The build must produce a single file using the `--onefile` flag.
*   **Asset Bundling:** The `datas` section of the spec file must be configured to include the `web/templates` and `web/static` directories.
*   **Hidden Imports:** The `hiddenimports` list in the spec file must be populated with any libraries that `PyInstaller` fails to detect automatically (e.g., `waitress`, `appdirs`, database drivers).
*   **Executable Name:** The executable should be named `WorkJournalMaker`.

## 5. Error Handling

The application must gracefully handle errors that may occur, especially related to file system operations and the bundled environment.

*   **Startup Errors:** Implement robust error handling during application startup. If the data directory or database cannot be created, log the error and display a user-friendly message.
*   **File Permissions:** The application should handle `PermissionError` exceptions when attempting to write to the data directory and guide the user on how to resolve them.
*   **Logging:** Configure logging to write to a file within the user data directory. This will help diagnose issues on user machines.

## 6. Testing Plan

A multi-faceted testing approach is required to ensure the bundled application is reliable across all target platforms.

### 6.1. Unit & Integration Tests
*   All existing unit and integration tests must pass before proceeding with packaging.
*   New tests should be added to cover the new code for server selection, path resolution, and data directory logic.

### 6.2. Manual Build & Run Tests
*   **Objective:** Verify that the build process completes successfully and the application launches on each target OS.
*   **Process:**
    1.  Manually run the `pyinstaller WorkJournalMaker.spec` command on Windows, macOS, and Linux.
    2.  Launch the generated executable on each platform.
    3.  Confirm that the application starts, the web interface is accessible in a browser, and there are no immediate errors in the console or logs.

### 6.3. Functional Testing
*   **Objective:** Ensure all application features work as expected in the packaged version.
*   **Process:** On each OS, perform the following checks:
    1.  **Asset Loading:** Verify that all CSS, JavaScript, and images load correctly.
    2.  **Database Operations:** Create, edit, and delete a journal entry to confirm the database is being written to and read from the correct application data directory.
    3.  **Core Features:** Test all major features of the application.

## 7. Distribution Strategy

*   **Initial Phase:** Manual builds will be performed on dedicated or virtualized machines for each target OS (Windows, macOS, Linux). The resulting executables will be made available for download.
*   **Future Enhancement:** A CI/CD pipeline (e.g., GitHub Actions) is recommended for future development. This will automate the build, test, and release process for all three platforms, ensuring consistency and reducing manual effort.