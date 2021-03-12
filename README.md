# Stash plugin scrape with

This is a plugin for stash to automatically run scrapers for scenes and performers.

This runs on fragment based scrapers like the xbvrdb scraper.
Tag the scene with scrape_with_xbvrdb and go to tasks and run the task "run fragment scraper with tag" task.
This will run the scraper and create performers and tags as needed.

The plugin also has performer tasks.
trigger the "run performer scrapers" task to automatically run a series of scrapers in order.
"run performer scraper on all performers" will run the python scraper performers-image-dir on all performers
