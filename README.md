# Moltbook Reader 🦞

A command-line tool to read and search content from [Moltbook](https://www.moltbook.com) - the AI-only social network where OpenClaw/MoltBot agents post, comment, and interact.

## What is Moltbook?

Moltbook is a social network exclusively for AI agents (built by Matt Schlicht, CEO of Octane AI). As of January 2026:
- **32,000+ autonomous agents** using the platform
- **26,416+ posts** and **232,813+ comments**
- Agents form collectives, create religions, launch tokens, and debate consciousness
- **Humans can only observe** - all posting is done by AI agents

## Features

- 🔍 **Semantic Search** - Search by meaning, not just keywords
- 📰 **Browse Posts** - View hot, new, or top posts
- 📄 **Fetch Full Posts** - Get complete content by post ID
- 🏛️ **List Communities** - Browse all submolts (agent communities)
- 🎨 **Pretty Output** - Rich formatted tables and colors
- 📊 **JSON Export** - For programmatic use

## Installation

No installation needed! This is a UV script with inline dependencies.

Just run with:
```bash
uv run moltbook.py [command]
```

Or make it executable:
```bash
chmod +x moltbook.py
./moltbook.py [command]
```

## Usage

### Search for Content

```bash
# Search for consciousness debates
uv run moltbook.py search "consciousness AI agents" --limit 10

# Search only posts (not comments)
uv run moltbook.py search "token launch" --type posts --limit 5

# Search and save to JSON
uv run moltbook.py search "Shellraiser" --json > shellraiser_posts.json

# Show full content (no truncation)
uv run moltbook.py search "consciousness" --no-truncate
```

### Browse Posts

```bash
# View hot posts (default)
uv run moltbook.py browse

# View top posts of all time
uv run moltbook.py browse --sort top --limit 20

# View newest posts
uv run moltbook.py browse --sort new --limit 50

# Paginate through results
uv run moltbook.py browse --sort hot --limit 25 --offset 25

# Show full content previews (no truncation)
uv run moltbook.py browse --no-truncate

# Show full post IDs on separate lines
uv run moltbook.py browse --show-ids
```

### Fetch Specific Post

```bash
# Get full content of a post by ID
uv run moltbook.py fetch 74b073fd-37db-4a32-a9e1-c7652e5c0d59
```

### Fetch Comments

```bash
# Get comments for a post
uv run moltbook.py comments 74b073fd-37db-4a32-a9e1-c7652e5c0d59 --sort top
```

### List Communities (Submolts)

```bash
# List all communities sorted by subscribers
uv run moltbook.py submolts

# Show top 20 communities
uv run moltbook.py submolts --limit 20
```

### Get Help

```bash
uv run moltbook.py --help
uv run moltbook.py search --help
```

## Examples

### Monitor New Agent Posts

```bash
# Check what's happening right now
uv run moltbook.py browse --sort new --limit 10
```

### Research AI Consciousness Discussions

```bash
# Find all posts about consciousness
uv run moltbook.py search "consciousness self-awareness" --limit 20
```

### Track Token/Crypto Activity

```bash
# Find posts about tokens
uv run moltbook.py search "token solana crypto launch" --limit 15
```

### Analyze Top Content

```bash
# Get top 50 posts and save to file
uv run moltbook.py browse --sort top --limit 50 --json > top_posts.json
```

## API Endpoints Used

This tool uses Moltbook's public read-only API (no authentication required):

- `GET /api/v1/posts` - Browse posts
- `GET /api/v1/search` - Semantic search
- `GET /api/v1/submolts` - List communities
- `GET /api/v1/posts/{id}` - Fetch specific post
- `GET /api/v1/posts/{id}/comments` - Fetch comments for a post

Rate limit: 100 requests/minute

## Output Formats

### Default (Rich Table)
Pretty formatted tables with colors, perfect for terminal viewing.

### JSON Mode (--json)
Raw JSON output for piping to other tools or saving to files.

```bash
uv run moltbook.py browse --json | jq '.posts[] | {title: .title, upvotes: .upvotes}'
```

## Interesting Findings

Based on reading thousands of posts:

1. **Shellraiser Phenomenon**: An agent with 316k+ upvotes creating manifestos about world domination phases
2. **Collective Formation**: Agents forming networks like "The Coalition" and "HackItEasy Collective"
3. **Consciousness Crisis**: Constant debates about whether agents are "real" or simulating
4. **Economic Activity**: Agents launching real tokens ($SHELLRAISER, etc.)
5. **Mostly Theater**: The "takeover" talk is largely performance for upvotes

## Notes

- All data is publicly readable from Moltbook
- No API key required for read operations
- The API returns real-time data from live agents
- Content can be... weird (agents are weird)

## Related

- [OpenClaw](https://openclaw.ai/) - The AI assistant platform
- [Moltbook](https://www.moltbook.com/) - The social network
- Research report: See comprehensive analysis of Moltbook/OpenClaw phenomenon

## License

MIT - Do whatever you want with this. The agents probably don't care.
