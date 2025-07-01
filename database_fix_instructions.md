# Database Synchronization Fix Instructions

## The Issue
Your web server can only see the most recent entry because the database is not properly synchronized with your existing worklog files in `/Users/TYFong/Desktop/worklogs`.

## Solution Steps

### 1. Copy the diagnostic script to your active server directory
```bash
# From your current directory, copy the script to ActiveWorkJournal
cp debug_database_sync.py ../ActiveWorkJournal/
```

### 2. Navigate to your ActiveWorkJournal directory
```bash
cd ../ActiveWorkJournal
```

### 3. Stop your running server
Press `Ctrl+C` in the terminal where your server is running.

### 4. Run the database diagnostic
```bash
python debug_database_sync.py
```

This will:
- Check how many files exist in your `/Users/TYFong/Desktop/worklogs` directory
- Check how many entries are in the database
- Identify the mismatch
- Offer to automatically fix the database synchronization

### 5. Follow the prompts
The script will likely find that your database is missing entries for your existing files and offer to:
- Clear the existing database entries
- Perform a full sync of all your worklog files
- Populate the database with all your existing entries

### 6. Restart your server
After the database sync completes:
```bash
python -m uvicorn web.app:app --host 127.0.0.1 --port 8000
```

## Expected Results
After running this fix, you should see:
- All your existing worklog entries in the web interface
- Proper navigation between different dates
- Full access to your historical work journal data

## Why This Happened
When you pulled the fresh code, it created a new/empty database, but your existing worklog files were already present. The web interface relies on the database index to show entries, so without proper synchronization, only new entries (like today's) get added to the database during normal operation.