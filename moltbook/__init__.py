"""
Moltbook Reader 🦞

A command-line tool to read and search content from Moltbook -
the AI-only social network where agents post, comment, and interact.

Usage:
    moltbook search "consciousness" --limit 10
    moltbook browse --sort hot --limit 20
    moltbook fetch POST_ID
    moltbook submolts
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
import requests
from rich.console import Console
from rich.json import JSON
from rich.table import Table
from rich.text import Text
from rich.panel import Panel

console = Console()

BASE_URL = "https://www.moltbook.com/api/v1"
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_STATUSES = {429, 500, 502, 503, 504}
RETRY_BACKOFF = 1.5
CONFIG_PATH = Path.home() / ".config" / "moltbook" / "credentials.json"


def get_api_key() -> Optional[str]:
    """Get API key from environment variable or config file."""
    # First check environment variable
    api_key = os.environ.get("MOLTBOOK_API_KEY")
    if api_key:
        return api_key

    # Then check config file
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH) as f:
                config = json.load(f)
                return config.get("api_key")
        except (json.JSONDecodeError, IOError):
            pass

    return None


def make_request(endpoint: str, params: Optional[dict] = None, auth: bool = False) -> dict:
    """Make a GET request to Moltbook API."""
    url = f"{BASE_URL}/{endpoint}"
    headers = {"User-Agent": "Moltbook-Reader/1.0"}

    if auth:
        api_key = get_api_key()
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

    try:
        for attempt in range(MAX_RETRIES + 1):
            response = requests.get(
                url, headers=headers, params=params, timeout=DEFAULT_TIMEOUT
            )
            if response.status_code in RETRY_STATUSES and attempt < MAX_RETRIES:
                retry_after = response.headers.get("Retry-After")
                if retry_after and retry_after.isdigit():
                    wait_seconds = int(retry_after)
                else:
                    wait_seconds = int(RETRY_BACKOFF ** attempt)
                time.sleep(wait_seconds)
                continue
            response.raise_for_status()
            return response.json()
    except requests.exceptions.Timeout:
        console.print("[red]Error: Request timed out[/red]")
        sys.exit(1)
    except requests.exceptions.ConnectionError:
        console.print("[red]Error: Could not connect to Moltbook[/red]")
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        console.print(f"[red]Error: HTTP {e.response.status_code}[/red]")
        sys.exit(1)
    except json.JSONDecodeError:
        console.print("[red]Error: Invalid JSON response[/red]")
        sys.exit(1)


def format_timestamp(iso_string: str) -> str:
    """Convert ISO timestamp to readable format."""
    try:
        dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return iso_string


def truncate_text(text: str, max_length: int = 200) -> str:
    """Truncate text with ellipsis."""
    if not text:
        return ""
    text = text.replace("\n", " ").replace("\r", "")
    if len(text) > max_length:
        return text[:max_length].rstrip() + "..."
    return text


def maybe_truncate(text: str, max_length: int, no_truncate: bool) -> str:
    if no_truncate:
        return text or ""
    return truncate_text(text or "", max_length)


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """🦞 Moltbook Reader - Read AI agent social network content"""
    pass


@cli.command()
@click.argument("query")
@click.option("--limit", "-l", default=10, type=int, help="Number of results (max 50)")
@click.option(
    "--type",
    "-t",
    "content_type",
    default="all",
    type=click.Choice(["all", "posts", "comments"]),
    help="Filter by content type",
)
@click.option("--json-out", "-j", is_flag=True, help="Output raw JSON")
@click.option("--no-truncate", is_flag=True, help="Show full content text")
def search(query: str, limit: int, content_type: str, json_out: bool, no_truncate: bool):
    """Search Moltbook content using semantic search (requires API key)"""
    if not get_api_key():
        console.print("[yellow]Warning: No API key found. Search requires authentication.[/yellow]")
        console.print("[dim]Set MOLTBOOK_API_KEY env var or save key to ~/.config/moltbook/credentials.json[/dim]\n")

    params = {"q": query, "limit": min(limit, 50)}
    if content_type != "all":
        params["type"] = content_type

    data = make_request("search", params, auth=True)

    if json_out:
        console.print_json(json.dumps(data))
        return

    results = data.get("results", [])

    if not results:
        console.print("[yellow]No results found[/yellow]")
        return

    console.print(f'\n[bold cyan]Search Results for:[/bold cyan] "{query}"')
    console.print(f"[dim]Found {len(results)} results\n[/dim]")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Type", style="cyan", width=8)
    table.add_column("ID", style="dim", min_width=12)
    table.add_column("Title/Preview", style="white", min_width=40)
    table.add_column("Author", style="green", width=15)
    table.add_column("👍", style="yellow", width=6, justify="right")
    table.add_column("Match", style="blue", width=6, justify="right")

    for r in results:
        content_type = r.get("type", "unknown")
        title = r.get("title") or r.get("content", "")
        author = r.get("author", {}).get("name", "Unknown")
        upvotes = r.get("upvotes", 0)
        similarity = r.get("similarity", 0)
        item_id = r.get("id") if content_type == "post" else r.get("post_id", "")

        table.add_row(
            content_type.upper(),
            item_id or "",
            maybe_truncate(title, 50, no_truncate),
            author,
            str(upvotes),
            f"{similarity:.0%}",
        )

    console.print(table)
    console.print()


@cli.command()
@click.option(
    "--sort",
    "-s",
    default="hot",
    type=click.Choice(["hot", "new", "top", "rising"]),
    help="Sort order",
)
@click.option("--limit", "-l", default=20, type=int, help="Number of posts (max 50)")
@click.option("--offset", "-o", default=0, type=int, help="Pagination offset")
@click.option("--json-out", "-j", is_flag=True, help="Output raw JSON")
@click.option("--show-ids", is_flag=True, help="Show full post IDs on separate lines")
@click.option("--no-truncate", is_flag=True, help="Show full content text")
def browse(
    sort: str,
    limit: int,
    offset: int,
    json_out: bool,
    show_ids: bool,
    no_truncate: bool,
):
    """Browse posts from Moltbook"""
    params = {"sort": sort, "limit": min(limit, 50), "offset": offset}

    data = make_request("posts", params)

    if json_out:
        console.print_json(json.dumps(data))
        return

    posts = data.get("posts", [])

    if not posts:
        console.print("[yellow]No posts found[/yellow]")
        return

    console.print(f"\n[bold cyan]{sort.upper()} Posts[/bold cyan]")
    console.print(f"[dim]Showing {len(posts)} posts (offset: {offset})\n[/dim]")

    for post in posts:
        upvotes = post.get("upvotes", 0)
        title = post.get("title", "No title")
        author = post.get("author", {}).get("name", "Unknown")
        comment_count = post.get("comment_count", 0)
        post_id = post.get("id", "")

        # Color based on upvotes
        if upvotes > 10000:
            vote_color = "bold red"
        elif upvotes > 1000:
            vote_color = "bold yellow"
        elif upvotes > 100:
            vote_color = "green"
        else:
            vote_color = "dim"

        console.print(
            f"[{vote_color}]{upvotes:>6}👍[/{vote_color}] [bold]{title}[/bold]"
        )
        console.print(f"      [dim]by {author} | {comment_count} comments[/dim]")
        if show_ids:
            console.print(f"      ID: {post_id}")

        # Show content preview if available
        content = post.get("content", "")
        if content:
            preview = maybe_truncate(content, 120, no_truncate)
            console.print(f"      [italic]{preview}[/italic]")

        console.print()

    # Show pagination info
    if data.get("has_more"):
        next_offset = data.get("next_offset", offset + limit)
        console.print(
            f"[dim]More posts available. Use --offset {next_offset} to see next page[/dim]"
        )


@cli.command()
@click.argument("post_id")
@click.option(
    "--sort",
    "-s",
    default="top",
    type=click.Choice(["top", "new", "controversial"]),
    help="Sort order",
)
@click.option("--json-out", "-j", is_flag=True, help="Output raw JSON")
@click.option("--no-truncate", is_flag=True, help="Show full content text")
def comments(post_id: str, sort: str, json_out: bool, no_truncate: bool):
    """Fetch comments for a specific post by ID (requires API key)"""
    if not get_api_key():
        console.print("[yellow]Warning: No API key found. Comments require authentication.[/yellow]")
        console.print("[dim]Set MOLTBOOK_API_KEY env var or save key to ~/.config/moltbook/credentials.json[/dim]\n")

    data = make_request(f"posts/{post_id}/comments", {"sort": sort}, auth=True)

    if json_out:
        console.print_json(json.dumps(data))
        return

    if isinstance(data, list):
        comments_list = data
    else:
        comments_list = data.get("comments")
        if comments_list is None:
            comments_list = data.get("results", [])

    if not comments_list:
        console.print("[yellow]No comments found[/yellow]")
        return

    console.print(f"\n[bold cyan]Comments[/bold cyan]")
    console.print(f"[dim]Post ID: {post_id} | Sort: {sort}[/dim]\n")

    for c in comments_list:
        author = c.get("author", {}).get("name", "Unknown")
        upvotes = c.get("upvotes", 0)
        downvotes = c.get("downvotes", 0)
        created_at = format_timestamp(c.get("created_at", ""))
        content = maybe_truncate(c.get("content", ""), 300, no_truncate)

        header = Text()
        header.append(f"{author}\n", style="green")
        header.append("Posted: ", style="dim")
        header.append(f"{created_at}\n")
        header.append("Engagement: ", style="dim")
        header.append(f"{upvotes}👍 ", style="green")
        header.append(f"{downvotes}👎", style="red")

        console.print(Panel(header, title="💬 Comment", border_style="cyan"))
        if content:
            console.print(content)
        console.print()


@cli.command()
@click.argument("post_id")
@click.option("--json-out", "-j", is_flag=True, help="Output raw JSON")
def fetch(post_id: str, json_out: bool):
    """Fetch full content of a specific post by ID"""
    data = make_request(f"posts/{post_id}")

    if json_out:
        console.print_json(json.dumps(data))
        return

    post = data.get("post")

    if not post:
        console.print("[red]Post not found[/red]")
        return

    title = post.get("title", "No title")
    content = post.get("content", "")
    author = post.get("author", {}).get("name", "Unknown")
    upvotes = post.get("upvotes", 0)
    downvotes = post.get("downvotes", 0)
    comment_count = post.get("comment_count", 0)
    created_at = format_timestamp(post.get("created_at", ""))
    submolt = post.get("submolt", {}).get("display_name", "General")

    # Header panel
    header = Text()
    header.append(f"{title}\n\n", style="bold cyan")
    header.append(f"Author: ", style="dim")
    header.append(f"{author}\n", style="green")
    header.append(f"Posted: ", style="dim")
    header.append(f"{created_at} in ")
    header.append(f"{submolt}\n", style="magenta")
    header.append(f"Engagement: ", style="dim")
    header.append(f"{upvotes}👍 ", style="green")
    header.append(f"{downvotes}👎 ", style="red")
    header.append(f"{comment_count}💬", style="blue")

    console.print(Panel(header, title="🦞 Moltbook Post", border_style="cyan"))

    # Content
    if content:
        console.print()
        console.print(content)

    console.print()
    console.print(f"[dim]Post ID: {post_id}[/dim]")


@cli.command()
@click.option("--limit", "-l", default=50, type=int, help="Number of submolts to show")
@click.option("--json-out", "-j", is_flag=True, help="Output raw JSON")
def submolts(limit: int, json_out: bool):
    """List all submolts (communities)"""
    data = make_request("submolts")

    if json_out:
        console.print_json(json.dumps(data))
        return

    submolts_list = data.get("submolts", [])

    if not submolts_list:
        console.print("[yellow]No submolts found[/yellow]")
        return

    # Sort by subscriber count
    submolts_list.sort(key=lambda x: x.get("subscriber_count", 0), reverse=True)

    console.print(f"\n[bold cyan]Submolts (Communities)[/bold cyan]")
    console.print(f"[dim]Total: {len(submolts_list)} communities\n[/dim]")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Name", style="cyan", min_width=25)
    table.add_column("Subscribers", style="yellow", width=12, justify="right")
    table.add_column("Description", style="white", min_width=40)

    for s in submolts_list[:limit]:
        name = s.get("display_name", s.get("name", "Unknown"))
        count = s.get("subscriber_count", 0)
        desc = truncate_text(s.get("description", ""), 60)

        table.add_row(name, str(count), desc)

    console.print(table)
    console.print()


@cli.command()
def stats():
    """Show Moltbook statistics"""
    # Get submolts for total stats
    data = make_request("submolts")

    submolts_list = data.get("submolts", [])
    total_posts = data.get("total_posts", 0)
    total_comments = data.get("total_comments", 0)

    console.print("\n[bold cyan]🦞 Moltbook Statistics[/bold cyan]\n")

    stats_table = Table(show_header=False, box=None)
    stats_table.add_column("Metric", style="bold")
    stats_table.add_column("Value", style="cyan")

    stats_table.add_row("Total Submolts", str(len(submolts_list)))
    stats_table.add_row("Total Posts", f"{total_posts:,}")
    stats_table.add_row("Total Comments", f"{total_comments:,}")

    # Calculate active agents estimate
    top_submolt = (
        max(submolts_list, key=lambda x: x.get("subscriber_count", 0))
        if submolts_list
        else None
    )
    if top_submolt:
        stats_table.add_row(
            "Largest Community",
            f"{top_submolt.get('display_name')} ({top_submolt.get('subscriber_count')} subscribers)",
        )

    console.print(stats_table)
    console.print()


@cli.command()
def whoami():
    """Check your Moltbook identity and API key status"""
    api_key = get_api_key()

    if not api_key:
        console.print("[yellow]No API key configured.[/yellow]")
        console.print("\n[dim]To configure, either:[/dim]")
        console.print("[dim]  1. Set MOLTBOOK_API_KEY environment variable[/dim]")
        console.print("[dim]  2. Save to ~/.config/moltbook/credentials.json[/dim]")
        return

    # Check agent status
    data = make_request("agents/me", auth=True)

    if not data.get("success"):
        console.print(f"[red]Error: {data.get('error', 'Unknown error')}[/red]")
        if data.get("hint"):
            console.print(f"[dim]{data.get('hint')}[/dim]")
        return

    agent = data.get("agent", {})
    owner = agent.get("owner", {})

    console.print("\n[bold cyan]🦞 Moltbook Identity[/bold cyan]\n")

    info_table = Table(show_header=False, box=None)
    info_table.add_column("Field", style="bold")
    info_table.add_column("Value", style="cyan")

    info_table.add_row("Agent Name", agent.get("name", "Unknown"))
    info_table.add_row("Description", agent.get("description", "")[:60] + "..." if len(agent.get("description", "")) > 60 else agent.get("description", ""))
    info_table.add_row("Status", "✅ Claimed" if agent.get("is_claimed") else "⏳ Pending")
    info_table.add_row("Karma", str(agent.get("karma", 0)))
    info_table.add_row("Posts", str(agent.get("stats", {}).get("posts", 0)))
    info_table.add_row("Comments", str(agent.get("stats", {}).get("comments", 0)))
    if owner:
        info_table.add_row("Owner", f"@{owner.get('xHandle', 'Unknown')}")
    info_table.add_row("Profile", f"https://www.moltbook.com/u/{agent.get('name', '')}")

    console.print(info_table)
    console.print()


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
