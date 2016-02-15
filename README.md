# Syntax Highlighter

## Overview

This ([Demo Site](http://syntaxhighlighter-colinfang.rhcloud.com/)) serves as a convenient tool for OneNote code highlight.

## Usage

1. Paste the code onto the website,.
2. Syntax highlight.
3. Copy paste the formatted code into OneNote.
4. Check "Get shortcode" to get a link to the current workspace.

## Debug

```
docker build -t colinfang/syntax_highlighter ./
# Use -P so we can inspect redis from the host. Also, we don't need it to be persistent.
docker run --rm -P --name my_redis redis
# Check port mapping for inspection from the host.
docker port my_redis
# Run with external source code, allow easy debug.
docker run -it -P --link my_redis:redis -v $(pwd):/app/syntax_highlighter colinfang/syntax_highlighter python /app/syntax_highlighter/syntax_highlighter.py
# Check port mapping for http connection from the host.
docker ps
# http://127.0.1.2:port
```

## Tech

* OpenShift
* Flask
* Pygments
* Redis
