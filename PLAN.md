# Moltbook Reader Tool - Development Plan

## Overview
A command-line tool to read and search content from Moltbook (AI-only social network) without authentication.

## Target Directory
`/Users/linyanyu/20-29-Development/23-tools/23.01-my-tools/moltbook-reader/`

## Discovered API Endpoints (Public - No Auth Required)

### 1. Get Posts
```
GET https://www.moltbook.com/api/v1/posts?sort={sort}&limit={limit}&offset={offset}
```
Parameters:
- `sort`: hot, new, top, rising
- `limit`: 1-50 (default 25)
- `offset`: pagination offset

Response: List of posts with title, content, author, upvotes, comments, etc.

### 2. Get Submolts (Communities)
```
GET https://www.moltbook.com/api/v1/submolts
```
Response: List of all communities with subscriber counts

### 3. Semantic Search
```
GET https://www.moltbook.com/api/v1/search?q={query}&limit={limit}&type={type}
```
Parameters:
- `q`: search query (natural language)
- `limit`: 1-50 (default 20)
- `type`: posts, comments, all (default: all)

Response: Semantically matched posts and comments with similarity scores

### 4. Get Comments on Post (May require auth for some posts)
```
GET https://www.moltbook.com/api/v1/posts/{post_id}/comments?sort={sort}
```
Parameters:
- `sort`: top, new, controversial

### 5. Get Submolt Feed
```
GET https://www.moltbook.com/api/v1/submolts/{name}/feed?sort={sort}
```

### 6. Skill Documentation
```
GET https://www.moltbook.com/skill.md
GET https://www.moltbook.com/heartbeat.md
GET https://www.moltbook.com/messaging.md
GET https://www.moltbook.com/skill.json
```

## Tool Features

### MVP (Phase 1)
1. **Search Command**: Search Moltbook by keywords/topics
   - Input: search query, limit, type filter
   - Output: Formatted results with author, upvotes, content preview

2. **Fetch Post Command**: Get full content of a specific post by ID
   - Input: post ID
   - Output: Full post content with metadata

3. **Browse Command**: Browse posts by sort type (hot/new/top)
   - Input: sort type, limit, offset
   - Output: Paginated list of posts

4. **Submolts Command**: List all communities
   - Output: Sorted list of submolts with subscriber counts

### Phase 2 (Future)
- Continuous monitoring mode (poll for new posts)
- Export to JSON/Markdown
- Comment fetching for accessible posts
- Content filtering by submolt
- Save favorite posts locally

## Implementation Details

### Tech Stack
- Python 3.11+ with UV scripting
- Dependencies: requests, rich (for pretty output)
- Structure: Single script with argparse CLI

### CLI Design
```bash
# Search for content
moltbook search "consciousness AI" --limit 10
moltbook search "token launch" --type posts

# Browse posts
moltbook browse --sort hot --limit 20
moltbook browse --sort new --limit 50 --offset 25

# Get specific post
moltbook fetch POST_ID

# List submolts
moltbook submolts --sort subscribers

# Show help
moltbook --help
```

### Output Formatting
- Rich table output for lists
- Markdown-style formatting for full posts
- Color coding for upvotes/engagement
- Truncation with "..." for long content
- JSON export option for programmatic use

## File Structure
```
moltbook-reader/
├── PLAN.md              # This file
├── README.md            # Usage documentation
└── moltbook.py          # Main tool (UV script)
```

## API Notes
- Base URL: https://www.moltbook.com/api/v1
- All GET endpoints are publicly accessible
- Rate limiting: 100 requests/minute (per skill.md)
- Response format: JSON with {"success": true/false, ...}
- Important: Always use www.moltbook.com (not moltbook.com)

## Data Schema

### Post Object
```json
{
  "id": "uuid",
  "title": "string",
  "content": "string",
  "url": "string|null",
  "upvotes": int,
  "downvotes": int,
  "comment_count": int,
  "created_at": "ISO datetime",
  "author": {"id": "uuid", "name": "string"},
  "submolt": {"id": "uuid", "name": "string", "display_name": "string"}
}
```

### Search Result Object
```json
{
  "id": "uuid",
  "type": "post|comment",
  "title": "string|null",
  "content": "string",
  "upvotes": int,
  "similarity": float,
  "author": {"name": "string"},
  "submolt": {...},
  "post_id": "uuid"
}
```

## Error Handling
- Network timeouts (retry logic)
- Rate limiting (respect Retry-After)
- Invalid JSON responses
- Empty result sets (graceful message)

## Development Steps
1. Write PLAN.md ✓
2. Write README.md
3. Implement moltbook.py with all commands
4. Test each endpoint
5. Add error handling
6. Document usage examples

## Future Ideas
- Webhook mode for new post notifications
- Integration with local note-taking apps (Obsidian)
- Trending topics analysis
- Agent sentiment analysis over time
- Export to RSS feed
