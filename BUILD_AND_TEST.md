# Build and Test Instructions

## 1. Install Dependencies
```bash
pip install -r requirements.txt
```

## 2. Run Tests
```bash
pytest
```

## 3. Build the Executable
```bash
pyinstaller WorkJournalMaker.spec
```

## 4. Run and Test the Application
- Navigate to the `dist` directory.
- Launch the `WorkJournalMaker` executable.
- Open a web browser to `http://localhost:8080`.
- Verify that all CSS, JavaScript, and images load correctly.
- Create a new journal entry, edit it, and then delete it.
- Check your user data directory (`%APPDATA%\WorkJournal` on Windows, `~/Library/Application Support/WorkJournal` on macOS) to confirm `journal.db` and `app.log` were created.