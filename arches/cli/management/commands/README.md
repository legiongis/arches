> **This app is a work-in-progress.** Please be aware that some commands may not be fully functional.

# Commands

The management commands herein are generally use the following pattern:

    python manage.py [topic] [operation] [--extra-options]

where the topic may be `maplayer` and an operation may be `list` (list all maplayers).

Where possible, classes from cli.management.managers are imported into the commands and used to perform the operations. This construction allows for manager classes to be easily used across multiple commands, or within each other's methods.

---

For help, use

```
python manage.py [command] --help
```

to learn more about any specific command.
