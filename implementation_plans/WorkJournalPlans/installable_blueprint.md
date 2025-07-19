Here is the detailed implementation blueprint and the corresponding LLM prompts for creating the installable Work Journal application.

### 1. Implementation Blueprint

This blueprint breaks down the project into small, iterative steps. Each step is designed to be implemented and tested safely, ensuring meaningful and verifiable progress.

**Phase 1: Application Preparation**

*   **Step 1: Add Dependencies**
    *   **Task:** Add `PyInstaller`, `waitress`, and `appdirs` to the project's `requirements.txt` file.
    *   **Rationale:** These packages are essential for bundling the application, running it with a production server, and managing user-specific data directories.

*   **Step 2: Implement Server-Switching Logic**
    *   **Task:** Modify the main application entry point (`main.py` or equivalent) to use `waitress` as the server when running as a bundled executable and `uvicorn` during development.
    *   **Rationale:** `uvicorn` is a development server and is not suitable for production. `waitress` is a production-ready WSGI server. The application needs to differentiate between the development and bundled environments.

*   **Step 3: Implement Dynamic Path Resolution for Assets**
    *   **Task:** Create a `resource_path(relative_path)` helper function to correctly resolve paths to the `templates` and `static` directories, whether the app is running from source or as a bundled executable.
    *   **Rationale:** When `PyInstaller` bundles the application, it places assets in a temporary directory (`sys._MEIPASS`). The application must be able to find these assets at runtime.

*   **Step 4: Integrate the Path Helper Function**
    *   **Task:** Update all code that references `templates` and `static` files (e.g., `Jinja2Templates`, `StaticFiles`) to use the new `resource_path()` helper function.
    *   **Rationale:** This ensures that all assets are loaded correctly in both development and bundled modes.

*   **Step 5: Implement User-Specific Data Storage**
    *   **Task:** Use the `appdirs` library to determine the appropriate user data directory based on the operating system. Modify the database connection logic to create and use the `journal.db` SQLite file in this directory.
    *   **Rationale:** Storing user data in the standard application data directory is a best practice for desktop applications, ensuring data persistence and separation from the application code.

*   **Step 6: Implement Startup Error Handling and Logging**
    *   **Task:** Add error handling for application startup. If the data directory or database cannot be created, the application should log the error to a file (`app.log`) in the user data directory and show a user-friendly error message.
    *   **Rationale:** Robust error handling is crucial for a good user experience, especially when dealing with file system permissions and other environment-related issues.

**Phase 2: Build and Test**

*   **Step 7: Create the PyInstaller Spec File**
    *   **Task:** Generate a `WorkJournalMaker.spec` file and configure it to:
        *   Create a single-file executable (`--onefile`).
        *   Bundle the `web/templates` and `web/static` directories.
        *   Include hidden imports like `waitress` and `appdirs`.
        *   Name the executable `WorkJournalMaker`.
    *   **Rationale:** A spec file provides a repeatable and version-controllable build configuration for `PyInstaller`.

*   **Step 8: Perform Initial Build and Functional Test**
    *   **Task:** Run the `pyinstaller WorkJournalMaker.spec` command to build the executable. Launch the application and perform a basic functional test:
        1.  Verify the UI loads correctly (CSS, JS).
        2.  Create, edit, and delete a journal entry.
        3.  Confirm the `journal.db` file is created in the correct user data directory.
    *   **Rationale:** This step validates that all the previous implementation steps work together correctly in the final bundled application.

### 2. LLM Prompts for Code Generation

These prompts are designed for a code-generation LLM to implement the blueprint in a test-driven manner.

```markdown
**Prompt 1: Add Dependencies**

Update the `requirements.txt` file to include the necessary libraries for building the executable. Add the following packages:
*   `pyinstaller`
*   `waitress`
*   `appdirs`

Ensure the versions are not strictly pinned unless necessary for compatibility.
```

```markdown
**Prompt 2: Test-Driven Server-Switching Logic**

We need to use the `waitress` server in the bundled application and `uvicorn` for development.

First, write a unit test in a new test file, `tests/test_server_runner.py`, that mocks `sys.frozen` to be `True` and asserts that `waitress.serve` is called. Then, write another test that mocks `sys.frozen` to be `False` (or absent) and asserts that `uvicorn.run` is called.

Next, create a new module, `server_runner.py`, and implement a `run()` function that contains the logic to satisfy these tests. The function should check `getattr(sys, 'frozen', False)` to determine which server to start. Modify the main application entry point to call this `run()` function.
```

```markdown
**Prompt 3: Test-Driven Dynamic Path Resolution**

The application needs to find assets in a temporary folder when running as a bundled executable.

First, in a new test file `tests/test_utils.py`, write a test for a `resource_path` function. The test should mock `sys.frozen` to be `True` and `sys._MEIPASS` to a dummy path (e.g., `/tmp/test_path`). It should assert that `resource_path('assets/style.css')` returns the correctly joined path: `/tmp/test_path/assets/style.css`. Write a second test where `sys.frozen` is `False` and assert that `resource_path('assets/style.css')` returns the original relative path.

Next, create a `utils.py` module and implement the `resource_path(relative_path)` function to make the tests pass.
```

```markdown
**Prompt 4: Integrate the Path Helper Function**

Now, we need to use the `resource_path` helper function to load templates and static files.

Refactor the main application file (e.g., `main.py`). Import the `resource_path` function from `utils.py`. Update the `StaticFiles` and `Jinja2Templates` instantiations to wrap the directory paths with `resource_path()`. For example:

`StaticFiles(directory=resource_path("web/static"))`
`Jinja2Templates(directory=resource_path("web/templates"))`
```

```markdown
**Prompt 5: Test-Driven User Data Storage**

User data must be stored in the standard OS-specific application data directory.

First, in `tests/test_utils.py`, write a test for a new function `get_user_data_dir()`. The test should mock `appdirs.user_data_dir` and assert that the function returns the correct path and that `os.makedirs` is called if the directory doesn't exist.

Next, implement the `get_user_data_dir()` function in `utils.py`. This function should use `appdirs.user_data_dir('WorkJournal', 'YourAppName')` to get the path and create it if it doesn't exist.

Finally, modify the database connection logic to call `get_user_data_dir()` and construct the full path to the SQLite database file (e.g., `os.path.join(get_user_data_dir(), 'journal.db')`).
```

```markdown
**Prompt 6: Test-Driven Startup Logging**

We need to implement logging to a file for better error diagnosis.

First, in `tests/test_utils.py`, write a test for a `setup_logging` function. The test should verify that after calling the function, a logger is configured to write to a file at a specific path (e.g., inside a mocked user data directory).

Next, implement the `setup_logging` function in `utils.py`. It should configure the root logger to write to `app.log` inside the directory returned by `get_user_data_dir()`.

Finally, call `setup_logging()` at the beginning of the application's startup sequence. Add a `try...except` block around the database initialization logic that logs any exceptions that occur.
```

```markdown
**Prompt 7: Create the PyInstaller Spec File**

Generate a `WorkJournalMaker.spec` file for `PyInstaller`. The spec file should be configured as follows:

*   The `datas` list must include the `web/templates` and `web/static` directories. The format should be `('web/templates', 'web/templates')` and `('web/static', 'web/static')`.
*   The `hiddenimports` list must include `waitress` and `appdirs`.
*   The `exe` object should configure the output executable name to `WorkJournalMaker`.
*   The analysis should be configured for a one-file build (`--onefile`).
```

```markdown
**Prompt 8: Final Build and Test Plan**

This is a manual step. Create a markdown file named `BUILD_AND_TEST.md` with the following instructions:

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run Tests:**
    ```bash
    pytest
    ```

3.  **Build the Executable:**
    ```bash
    pyinstaller WorkJournalMaker.spec
    ```

4.  **Run and Test the Application:**
    *   Navigate to the `dist` directory.
    *   Launch the `WorkJournalMaker` executable.
    *   Open a web browser to `http://localhost:8080`.
    *   Verify that all CSS, JavaScript, and images load correctly.
    *   Create a new journal entry, edit it, and then delete it.
    *   Check your user data directory (`%APPDATA%\WorkJournal` on Windows, `~/Library/Application Support/WorkJournal` on macOS) to confirm `journal.db` and `app.log` were created.
```