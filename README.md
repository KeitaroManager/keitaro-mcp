# Keitaro MCP Server

MCP server for [Keitaro Tracker](https://keitaro.io) Admin API. Provides **37 tools** for campaign management, traffic analytics, reports, and raw click/conversion data — accessible from [Claude Code](https://claude.com/claude-code), Cursor, and other MCP-compatible AI agents.

## Quick Start

### Prerequisites

- **Python** >= 3.11
- **uv** ([install guide](https://docs.astral.sh/uv/getting-started/installation/))
- **curl** (pre-installed on most systems)
- **Keitaro API key** (see [How to Get API Key](#how-to-get-api-key) below)

### Step 1: Clone the repository

```bash
git clone https://github.com/KeitaroManager/keitaro-mcp.git
```

Choose where to clone. It can be anywhere — your home directory, a tools folder, etc:

```bash
# Example locations:
git clone https://github.com/KeitaroManager/keitaro-mcp.git ~/keitaro-mcp
git clone https://github.com/KeitaroManager/keitaro-mcp.git ~/tools/keitaro-mcp
git clone https://github.com/KeitaroManager/keitaro-mcp.git /opt/keitaro-mcp
```

### Step 2: Install the MCP server

Pick ONE of the two scopes below. Replace the placeholder values with your real tracker URL and API key.

**Option A — Project scope** (available only when working inside a specific project directory):

```bash
cd /path/to/your/project

claude mcp add keitaro -s project \
  -e KEITARO_URL=https://your-tracker.example.com \
  -e KEITARO_API_KEY=your-api-key-here \
  -- uv --directory /absolute/path/to/keitaro-mcp run python -m keitaro_mcp
```

**Option B — User scope** (available in all your projects, globally):

```bash
claude mcp add keitaro -s user \
  -e KEITARO_URL=https://your-tracker.example.com \
  -e KEITARO_API_KEY=your-api-key-here \
  -- uv --directory /absolute/path/to/keitaro-mcp run python -m keitaro_mcp
```

### Step 3: Done

Restart Claude Code. The `keitaro_*` tools are now available. Try:

```
You: "List my Keitaro campaigns"
You: "Show ROI by campaign for last 7 days"
You: "Create a campaign named Test"
```

### Full Example (copy-paste ready)

```bash
# 1. Clone
git clone https://github.com/KeitaroManager/keitaro-mcp.git ~/keitaro-mcp

# 2. Install (project scope — run this inside your project directory)
claude mcp add keitaro -s project \
  -e KEITARO_URL=https://tracker.mycompany.com \
  -e KEITARO_API_KEY=abc123def456 \
  -- uv --directory ~/keitaro-mcp run python -m keitaro_mcp

# 3. Restart Claude Code and use it
```

## How to Get API Key

1. Log into your Keitaro tracker admin panel
2. Go to **Maintenance → Users** (or click your account icon → **Account → API keys**)
3. Click **Create API key**
4. Copy the key — it cannot be viewed again after creation

The API key requires admin or expert-level permissions.

## Updating

When a new version is released, pull the latest code:

```bash
cd /path/to/keitaro-mcp
git pull
```

That's it. The next time Claude Code starts, it will use the updated version automatically. No reinstall needed — `uv` reads the source directly.

## Uninstalling

```bash
# Remove from project scope
claude mcp remove keitaro -s project

# Or remove from user scope
claude mcp remove keitaro -s user
```

## Multiple Keitaro Instances

If you have more than one Keitaro tracker (e.g. production + staging), create a JSON config file:

```json
[
  {
    "name": "production",
    "url": "https://tracker.example.com",
    "api_key": "prod-api-key",
    "description": "Production tracker"
  },
  {
    "name": "staging",
    "url": "https://staging.example.com",
    "api_key": "staging-api-key",
    "description": "Staging tracker"
  }
]
```

Save it (e.g. `~/keitaro-instances.json`), then install with:

```bash
claude mcp add keitaro -s project \
  -e KEITARO_CONFIG_FILE=/absolute/path/to/keitaro-instances.json \
  -- uv --directory /absolute/path/to/keitaro-mcp run python -m keitaro_mcp
```

When multiple instances are configured, tools accept an optional `instance` parameter. If only one instance exists, it is selected automatically.

## Connecting to Cursor

Add to Cursor settings (Settings → MCP Servers → Add):

```json
{
  "keitaro": {
    "command": "uv",
    "args": ["--directory", "/absolute/path/to/keitaro-mcp", "run", "python", "-m", "keitaro_mcp"],
    "env": {
      "KEITARO_URL": "https://your-tracker.example.com",
      "KEITARO_API_KEY": "your-api-key"
    }
  }
}
```

## What It Does

### 37 Tools by Category

| Category | Tools | Operations |
|----------|-------|------------|
| **Campaigns** | 7 | List, get, create, update, archive, clone, enable/disable |
| **Streams (Flows)** | 6 | List, get, create, update, delete, enable/disable |
| **Offers** | 5 | List, get, create, update, archive |
| **Landing Pages** | 5 | List, get, create, update, archive |
| **Traffic Sources** | 3 | List, get, create |
| **Affiliate Networks** | 3 | List, get, create |
| **Domains** | 3 | List, get, check DNS/SSL |
| **Groups** | 1 | List by type |
| **Reports** | 1 | Build aggregated report (dimensions, measures, filters, sort) |
| **Clicks** | 1 | Query raw click log with pagination |
| **Conversions** | 1 | Query raw conversion log with pagination |
| **Platform** | 1 | List configured instances |

### Analytics: Report Builder

The `keitaro_build_report` tool is the primary analytics interface:

- **30+ metrics**: clicks, conversions, revenue, profit, ROI, CR, CPC, CPA, EPC, cost, leads, sales...
- **50+ dimensions**: campaign, offer, landing, country, day, hour, device, browser, OS, sub_id_1..30...
- **20+ filter operators**: EQUALS, GREATER_THAN, CONTAINS, IN_LIST, BETWEEN, MATCH_REGEXP...
- **Date ranges**: any from/to with timezone support

Example:
```
User: "Show me ROI by campaign for the last 7 days, sorted by profit"
→ keitaro_build_report(date_from="2026-03-17", date_to="2026-03-24",
    dimensions=["campaign"], measures=["clicks", "conversions", "revenue", "profit", "roi"],
    sort=[{name: "profit", order: "DESC"}])
```

### Raw Data: Clicks & Conversions

Query individual click and conversion records with column selection, filtering, and pagination. Useful for debugging traffic quality, checking specific sub_ids, or investigating conversions.

### Full Tool List

<details>
<summary>Read Tools (safe, no side effects) — 19 tools</summary>

| Tool | Description |
|------|-------------|
| `keitaro_list_instances` | List configured tracker instances |
| `keitaro_list_campaigns` | List campaigns (supports limit/offset) |
| `keitaro_get_campaign` | Get campaign by ID |
| `keitaro_list_streams` | List streams for a campaign |
| `keitaro_get_stream` | Get stream by ID |
| `keitaro_list_offers` | List all offers |
| `keitaro_get_offer` | Get offer by ID |
| `keitaro_list_landing_pages` | List all landing pages |
| `keitaro_get_landing_page` | Get landing page by ID |
| `keitaro_list_traffic_sources` | List all traffic sources |
| `keitaro_get_traffic_source` | Get traffic source by ID |
| `keitaro_list_affiliate_networks` | List all affiliate networks |
| `keitaro_get_affiliate_network` | Get affiliate network by ID |
| `keitaro_list_domains` | List all domains |
| `keitaro_get_domain` | Get domain by ID |
| `keitaro_list_groups` | List groups by type |
| `keitaro_build_report` | Build aggregated analytics report |
| `keitaro_get_clicks` | Query raw click records |
| `keitaro_get_conversions` | Query raw conversion records |

</details>

<details>
<summary>Write Tools (create, update, modify) — 18 tools</summary>

| Tool | Description |
|------|-------------|
| `keitaro_create_campaign` | Create a new campaign |
| `keitaro_update_campaign` | Update campaign fields |
| `keitaro_delete_campaign` | Archive campaign (soft delete, reversible) |
| `keitaro_clone_campaign` | Duplicate campaign with streams |
| `keitaro_toggle_campaign` | Enable or disable campaign |
| `keitaro_create_offer` | Create a new offer |
| `keitaro_update_offer` | Update offer fields |
| `keitaro_delete_offer` | Archive offer |
| `keitaro_create_stream` | Create stream in a campaign |
| `keitaro_update_stream` | Update stream fields |
| `keitaro_delete_stream` | Delete stream |
| `keitaro_toggle_stream` | Enable or disable stream |
| `keitaro_create_landing_page` | Create landing page |
| `keitaro_update_landing_page` | Update landing page |
| `keitaro_delete_landing_page` | Archive landing page |
| `keitaro_create_traffic_source` | Create traffic source |
| `keitaro_create_affiliate_network` | Create affiliate network |
| `keitaro_check_domain` | Check domain DNS/SSL status (triggers active probe) |

</details>

## Architecture

```
keitaro-mcp/
├── pyproject.toml                  # Package config, dependencies
├── README.md                       # This file
├── LICENSE                         # MIT
├── .env.example                    # Configuration template
├── keitaro-instances.example.json  # Multi-instance config template
└── src/keitaro_mcp/
    ├── __init__.py                 # Entry point
    ├── __main__.py                 # python -m keitaro_mcp
    ├── server.py                   # MCP Server — 37 tools, match/case routing
    ├── client.py                   # HTTP client (curl subprocess)
    ├── registry.py                 # Multi-instance support
    └── errors.py                   # Error types
```

### Why curl instead of requests/httpx?

Keitaro trackers are typically behind Cloudflare. Python HTTP libraries (`urllib`, `httpx`, `requests`) use TLS fingerprints that Cloudflare identifies and blocks with 403 Forbidden. `curl` uses a different TLS stack that passes through. This is a deliberate architectural choice.

### Design Principles

- **Low-level MCP Server** with `match/case` routing — scales well for 37+ tools
- **Zero Python dependencies** beyond `mcp>=1.0.0` — uses system `curl` for HTTP
- **Multi-instance** — one server can connect to multiple Keitaro trackers
- **Structured errors** — all errors return JSON `{"error": "..."}`, server never crashes
- **AI-optimized** — every tool has detailed description with field lists, enums, and usage hints

## Keitaro API Reference

This server wraps the [Keitaro Admin API v1](https://admin-api.docs.keitaro.io/). Full [OpenAPI spec](https://admin-api.docs.keitaro.io/openapi.json) covers 119 endpoints. This MCP server covers the most commonly used operations.

Key Keitaro concepts:
- **Campaign** → has **Streams** (flows) → each stream routes to **Landings** and **Offers**
- **Offers** belong to **Affiliate Networks** (for postback tracking)
- **Traffic Sources** define where clicks come from (Facebook, Google, etc.)
- **Domains** are tracker URLs used for campaign links
- **Groups** organize campaigns, offers, and landings into categories

## Contributing

1. Clone the repo
2. Install dev dependencies: `uv pip install -e ".[dev]"` (or `pip install -e ".[dev]"`)
3. Make changes in `src/keitaro_mcp/`
4. Test: `python -c "from keitaro_mcp.server import TOOLS; print(f'{len(TOOLS)} tools OK')"`
5. Submit a PR

To add a new tool:
1. Add the API method to `client.py`
2. Add the `Tool()` definition to `TOOLS` list in `server.py`
3. Add the `match case` handler in `call_tool()` in `server.py`

## License

MIT
