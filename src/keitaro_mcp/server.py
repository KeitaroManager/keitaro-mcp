"""Keitaro MCP Server.

Provides tools to interact with Keitaro Tracker Admin API — campaign management,
traffic analytics, offers, streams (flows), landing pages, traffic sources,
affiliate networks, domains, reports, raw clicks/conversions data.

Transport: stdio (launched by Claude Code via settings).
Config: KEITARO_URL + KEITARO_API_KEY env vars, or KEITARO_CONFIG_FILE path.
"""

import asyncio
import json
import os
import shutil
import sys

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from keitaro_mcp.errors import KeitaroError
from keitaro_mcp.registry import InstanceRegistry

registry = InstanceRegistry()
app = Server("keitaro")


def _init():
    """Load instances from config file or env vars."""
    # curl is required for HTTP requests (bypasses Cloudflare TLS fingerprinting)
    if not shutil.which("curl"):
        print(
            "ERROR: 'curl' is required but not found in PATH. "
            "Install curl: apt install curl / brew install curl",
            file=sys.stderr,
        )
        sys.exit(1)

    config_file = os.environ.get("KEITARO_CONFIG_FILE", "")
    if config_file:
        if not os.path.exists(config_file):
            print(
                f"ERROR: KEITARO_CONFIG_FILE is set but file not found: {config_file}",
                file=sys.stderr,
            )
            sys.exit(1)
        try:
            count = registry.load_from_file(config_file)
        except ValueError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        count = registry.load_from_env()
    if count == 0:
        print(
            "WARNING: No Keitaro instances configured. "
            "Set KEITARO_URL + KEITARO_API_KEY or KEITARO_CONFIG_FILE.",
            file=sys.stderr,
        )


def _ok(data) -> list[TextContent]:
    text = json.dumps(data, indent=2, ensure_ascii=False, default=str)
    return [TextContent(type="text", text=text)]


def _err(msg: str) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps({"error": msg}))]


# Shared parameter for multi-instance support
_INSTANCE_PARAM = {
    "instance": {
        "type": "string",
        "description": "Keitaro instance name. Omit if only one instance is configured.",
    }
}

# ============================================================================
# Tool Definitions
# ============================================================================

TOOLS = [
    # ==================== Platform ====================
    Tool(
        name="keitaro_list_instances",
        description=(
            "List all registered Keitaro tracker instances with URLs and descriptions. "
            "Use this first to discover available instances."
        ),
        inputSchema={"type": "object", "properties": {}},
    ),

    # ==================== Campaigns ====================
    Tool(
        name="keitaro_list_campaigns",
        description=(
            "List all campaigns. Returns id, name, alias, state, type, group_id, "
            "cost_type, cost_value, traffic_source_id. "
            "Use to discover campaign IDs for reports or stream management. "
            "Supports limit/offset pagination."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                **_INSTANCE_PARAM,
                "limit": {"type": "integer", "description": "Max results to return"},
                "offset": {"type": "integer", "description": "Skip N results for pagination"},
            },
        },
    ),
    Tool(
        name="keitaro_get_campaign",
        description=(
            "Get campaign details by ID. Returns full config including alias, name, "
            "type, state, cost_type, cost_value, cookies_ttl, token, group_id, "
            "traffic_source_id."
        ),
        inputSchema={
            "type": "object",
            "required": ["id"],
            "properties": {
                **_INSTANCE_PARAM,
                "id": {"type": "integer", "description": "Campaign ID"},
            },
        },
    ),

    # ==================== Streams (Flows) ====================
    Tool(
        name="keitaro_list_streams",
        description=(
            "List streams (flows) for a campaign. Returns id, name, type, position, "
            "state, action_type, schema. Streams define how traffic is routed to "
            "landing pages and offers. Requires campaign_id."
        ),
        inputSchema={
            "type": "object",
            "required": ["campaign_id"],
            "properties": {
                **_INSTANCE_PARAM,
                "campaign_id": {"type": "integer", "description": "Campaign ID to list streams for"},
            },
        },
    ),
    Tool(
        name="keitaro_get_stream",
        description=(
            "Get stream details by ID. Returns full config including filters, "
            "landings, offers, action_options, schema, triggers."
        ),
        inputSchema={
            "type": "object",
            "required": ["id"],
            "properties": {
                **_INSTANCE_PARAM,
                "id": {"type": "integer", "description": "Stream ID"},
            },
        },
    ),

    # ==================== Offers ====================
    Tool(
        name="keitaro_list_offers",
        description=(
            "List all offers. Returns id, name, group_id, offer_type, action_type, "
            "payout_value, payout_currency, payout_type, state, affiliate_network_id."
        ),
        inputSchema={
            "type": "object",
            "properties": {**_INSTANCE_PARAM},
        },
    ),
    Tool(
        name="keitaro_get_offer",
        description=(
            "Get offer details by ID. Returns full config including payout settings, "
            "affiliate network, country, action_payload (URL), notes."
        ),
        inputSchema={
            "type": "object",
            "required": ["id"],
            "properties": {
                **_INSTANCE_PARAM,
                "id": {"type": "integer", "description": "Offer ID"},
            },
        },
    ),

    # ==================== Landing Pages ====================
    Tool(
        name="keitaro_list_landing_pages",
        description=(
            "List all landing pages. Returns id, name, group_id, action_type, "
            "action_payload, state."
        ),
        inputSchema={
            "type": "object",
            "properties": {**_INSTANCE_PARAM},
        },
    ),
    Tool(
        name="keitaro_get_landing_page",
        description="Get landing page details by ID.",
        inputSchema={
            "type": "object",
            "required": ["id"],
            "properties": {
                **_INSTANCE_PARAM,
                "id": {"type": "integer", "description": "Landing page ID"},
            },
        },
    ),

    # ==================== Traffic Sources ====================
    Tool(
        name="keitaro_list_traffic_sources",
        description=(
            "List all traffic sources. Returns id, name, postback_url, template params."
        ),
        inputSchema={
            "type": "object",
            "properties": {**_INSTANCE_PARAM},
        },
    ),
    Tool(
        name="keitaro_get_traffic_source",
        description="Get traffic source details by ID.",
        inputSchema={
            "type": "object",
            "required": ["id"],
            "properties": {
                **_INSTANCE_PARAM,
                "id": {"type": "integer", "description": "Traffic source ID"},
            },
        },
    ),

    # ==================== Affiliate Networks ====================
    Tool(
        name="keitaro_list_affiliate_networks",
        description=(
            "List all affiliate networks. Returns id, name, postback_url, "
            "offer_param, state."
        ),
        inputSchema={
            "type": "object",
            "properties": {**_INSTANCE_PARAM},
        },
    ),
    Tool(
        name="keitaro_get_affiliate_network",
        description="Get affiliate network details by ID.",
        inputSchema={
            "type": "object",
            "required": ["id"],
            "properties": {
                **_INSTANCE_PARAM,
                "id": {"type": "integer", "description": "Affiliate network ID"},
            },
        },
    ),

    # ==================== Domains ====================
    Tool(
        name="keitaro_list_domains",
        description=(
            "List all domains. Returns id, name, is_ssl, network_status, "
            "default_campaign_id."
        ),
        inputSchema={
            "type": "object",
            "properties": {**_INSTANCE_PARAM},
        },
    ),
    Tool(
        name="keitaro_get_domain",
        description="Get domain details by ID including SSL and DNS status.",
        inputSchema={
            "type": "object",
            "required": ["id"],
            "properties": {
                **_INSTANCE_PARAM,
                "id": {"type": "integer", "description": "Domain ID"},
            },
        },
    ),

    # ==================== Groups ====================
    Tool(
        name="keitaro_list_groups",
        description=(
            "List groups by type. Types: campaigns, offers, landings, domains. "
            "Returns id, name, type. Groups organize entities into categories."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                **_INSTANCE_PARAM,
                "type": {
                    "type": "string",
                    "enum": ["campaigns", "offers", "landings", "domains"],
                    "description": "Group type to filter by",
                },
            },
        },
    ),

    # ==================== Reports (Phase 3 — highest AI value) ====================
    Tool(
        name="keitaro_build_report",
        description=(
            "Build aggregated analytics report with custom dimensions, measures, "
            "filters, and date range. This is the main analytics tool. "
            "Common dimensions: campaign, offer, landing, ts (traffic source), "
            "stream, country, day, hour, device_type, browser, os. "
            "Common measures: clicks, conversions, revenue, profit, roi, cr, "
            "cpc, cpa, epc, leads, sales, cost, bot_share, lp_clicks, lp_ctr. "
            "Filter operators: EQUALS, NOT_EQUAL, GREATER_THAN, LESS_THAN, "
            "CONTAINS, NOT_CONTAIN, IN_LIST, NOT_IN_LIST, BETWEEN. "
            "Returns rows array with aggregated data plus total count."
        ),
        inputSchema={
            "type": "object",
            "required": ["date_from", "date_to"],
            "properties": {
                **_INSTANCE_PARAM,
                "date_from": {"type": "string", "description": "Start date YYYY-MM-DD"},
                "date_to": {"type": "string", "description": "End date YYYY-MM-DD"},
                "timezone": {"type": "string", "description": "Timezone, e.g. Europe/Kyiv. Default: UTC"},
                "dimensions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Grouping columns. Options: campaign, offer, landing, ts, "
                        "stream, country, region, city, day, hour, week, month, "
                        "device_type, browser, os, isp, connection_type, language, "
                        "sub_id_1..sub_id_30, affiliate_network, campaign_group"
                    ),
                },
                "measures": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Metrics to calculate. Options: clicks, conversions, revenue, "
                        "profit, roi, cr, cpc, cpa, epc, cost, leads, sales, "
                        "campaign_unique_clicks, lp_clicks, lp_ctr, bot_share, "
                        "rejected, rebills, ecpm, profitability"
                    ),
                },
                "filters": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Field name to filter"},
                            "operator": {
                                "type": "string",
                                "enum": [
                                    "EQUALS", "NOT_EQUAL", "GREATER_THAN", "LESS_THAN",
                                    "EQUALS_OR_GREATER_THAN", "EQUALS_OR_LESS_THAN",
                                    "CONTAINS", "NOT_CONTAIN", "IN_LIST", "NOT_IN_LIST",
                                    "BETWEEN", "BEGINS_WITH", "ENDS_WITH",
                                    "MATCH_REGEXP", "NOT_MATCH_REGEXP",
                                    "IS_SET", "IS_NOT_SET", "IS_TRUE", "IS_FALSE",
                                ],
                            },
                            "expression": {"type": "string", "description": "Filter value"},
                        },
                        "required": ["name", "operator", "expression"],
                    },
                    "description": "Filter conditions. Example: [{name: 'campaign_id', operator: 'EQUALS', expression: '10'}]",
                },
                "sort": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "order": {"type": "string", "enum": ["ASC", "DESC"]},
                        },
                        "required": ["name", "order"],
                    },
                    "description": "Sort order. Example: [{name: 'profit', order: 'DESC'}]",
                },
            },
        },
    ),

    # ==================== Clicks (Raw Data) ====================
    Tool(
        name="keitaro_get_clicks",
        description=(
            "Query raw click records via POST /clicks/log. Returns individual click "
            "data with selected columns. ALWAYS set limit to avoid huge responses. "
            "Available columns: click_id, datetime, campaign_id, campaign, offer_id, "
            "offer, landing_id, landing, stream_id, ip, country, country_code, "
            "region, city, device_type, browser, os, user_agent, referrer, "
            "sub_id, sub_id_1..sub_id_30, revenue, cost, profit, is_bot, is_unique_campaign. "
            "For aggregated stats use keitaro_build_report instead."
        ),
        inputSchema={
            "type": "object",
            "required": ["date_from", "date_to"],
            "properties": {
                **_INSTANCE_PARAM,
                "date_from": {"type": "string", "description": "Start date YYYY-MM-DD"},
                "date_to": {"type": "string", "description": "End date YYYY-MM-DD"},
                "columns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Columns to return. Default: click_id, datetime, campaign, ip, country",
                },
                "filters": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "Same filter format as keitaro_build_report",
                },
                "sort": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "Same sort format as keitaro_build_report",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results. ALWAYS set this to avoid huge responses. Default: 100",
                },
                "offset": {"type": "integer", "description": "Skip N results for pagination"},
            },
        },
    ),

    # ==================== Conversions (Raw Data) ====================
    Tool(
        name="keitaro_get_conversions",
        description=(
            "Query raw conversion records via POST /conversions/log. Returns "
            "individual conversion data. ALWAYS set limit. "
            "Available columns: conversion_id, click_id, campaign, offer, status, "
            "revenue, sub_id, postback_datetime, sale_datetime, country, ip, "
            "sub_id_1..sub_id_30. "
            "For aggregated conversion stats use keitaro_build_report instead."
        ),
        inputSchema={
            "type": "object",
            "required": ["date_from", "date_to"],
            "properties": {
                **_INSTANCE_PARAM,
                "date_from": {"type": "string", "description": "Start date YYYY-MM-DD"},
                "date_to": {"type": "string", "description": "End date YYYY-MM-DD"},
                "columns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Columns to return. Default: conversion_id, campaign, status, revenue",
                },
                "filters": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "Same filter format as keitaro_build_report",
                },
                "sort": {
                    "type": "array",
                    "items": {"type": "object"},
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results. ALWAYS set this. Default: 100",
                },
                "offset": {"type": "integer", "description": "Skip N results for pagination"},
            },
        },
    ),

    # ==================== CRUD: Campaigns ====================
    Tool(
        name="keitaro_create_campaign",
        description=(
            "Create a new campaign. Required: name. "
            "Optional: alias (URL slug), type (position/weight), cost_type (CPC/CPM/CPUC), "
            "cost_value, group_id, traffic_source_id, state (active/disabled)."
        ),
        inputSchema={
            "type": "object",
            "required": ["name"],
            "properties": {
                **_INSTANCE_PARAM,
                "name": {"type": "string", "description": "Campaign name"},
                "alias": {"type": "string", "description": "URL slug for campaign link"},
                "type": {"type": "string", "enum": ["position", "weight"], "description": "Stream priority type"},
                "cost_type": {"type": "string", "enum": ["CPC", "CPM", "CPUC"], "description": "Cost model"},
                "cost_value": {"type": "number", "description": "Cost value"},
                "cost_currency": {"type": "string", "description": "Currency code, e.g. USD"},
                "group_id": {"type": "integer", "description": "Campaign group ID"},
                "traffic_source_id": {"type": "integer", "description": "Traffic source ID"},
                "state": {"type": "string", "enum": ["active", "disabled"]},
            },
        },
    ),
    Tool(
        name="keitaro_update_campaign",
        description=(
            "Update campaign fields. Only provided fields are changed (partial update). "
            "Same fields as keitaro_create_campaign."
        ),
        inputSchema={
            "type": "object",
            "required": ["id"],
            "properties": {
                **_INSTANCE_PARAM,
                "id": {"type": "integer", "description": "Campaign ID to update"},
                "name": {"type": "string"},
                "alias": {"type": "string"},
                "type": {"type": "string", "enum": ["position", "weight"]},
                "cost_type": {"type": "string", "enum": ["CPC", "CPM", "CPUC"]},
                "cost_value": {"type": "number"},
                "group_id": {"type": "integer"},
                "traffic_source_id": {"type": "integer"},
                "state": {"type": "string", "enum": ["active", "disabled"]},
            },
        },
    ),
    Tool(
        name="keitaro_delete_campaign",
        description=(
            "Archive a campaign (soft delete). Campaign can be restored later with "
            "keitaro_restore_campaign. This does NOT permanently delete."
        ),
        inputSchema={
            "type": "object",
            "required": ["id"],
            "properties": {
                **_INSTANCE_PARAM,
                "id": {"type": "integer", "description": "Campaign ID to archive"},
            },
        },
    ),
    Tool(
        name="keitaro_clone_campaign",
        description="Duplicate a campaign including its streams.",
        inputSchema={
            "type": "object",
            "required": ["id"],
            "properties": {
                **_INSTANCE_PARAM,
                "id": {"type": "integer", "description": "Campaign ID to clone"},
            },
        },
    ),
    Tool(
        name="keitaro_toggle_campaign",
        description=(
            "Enable or disable a campaign. "
            "action='enable' activates, action='disable' deactivates."
        ),
        inputSchema={
            "type": "object",
            "required": ["id", "action"],
            "properties": {
                **_INSTANCE_PARAM,
                "id": {"type": "integer", "description": "Campaign ID"},
                "action": {"type": "string", "enum": ["enable", "disable"]},
            },
        },
    ),

    # ==================== CRUD: Offers ====================
    Tool(
        name="keitaro_create_offer",
        description=(
            "Create a new offer. Required: name. "
            "Optional: offer_type (external/preloaded), action_type, action_payload (URL), "
            "affiliate_network_id, payout_value, payout_currency, payout_type (CPA/CPC), "
            "country, group_id."
        ),
        inputSchema={
            "type": "object",
            "required": ["name"],
            "properties": {
                **_INSTANCE_PARAM,
                "name": {"type": "string"},
                "offer_type": {"type": "string", "enum": ["external", "preloaded", "other"]},
                "action_type": {"type": "string"},
                "action_payload": {"type": "string", "description": "Offer URL"},
                "affiliate_network_id": {"type": "integer"},
                "payout_value": {"type": "number"},
                "payout_currency": {"type": "string"},
                "payout_type": {"type": "string", "enum": ["CPA", "CPC"]},
                "country": {"type": "string"},
                "group_id": {"type": "integer"},
            },
        },
    ),
    Tool(
        name="keitaro_update_offer",
        description="Update offer fields (partial update).",
        inputSchema={
            "type": "object",
            "required": ["id"],
            "properties": {
                **_INSTANCE_PARAM,
                "id": {"type": "integer", "description": "Offer ID"},
                "name": {"type": "string"},
                "action_payload": {"type": "string"},
                "payout_value": {"type": "number"},
                "payout_type": {"type": "string", "enum": ["CPA", "CPC"]},
                "affiliate_network_id": {"type": "integer"},
                "group_id": {"type": "integer"},
            },
        },
    ),
    Tool(
        name="keitaro_delete_offer",
        description="Archive an offer (soft delete, can be restored).",
        inputSchema={
            "type": "object",
            "required": ["id"],
            "properties": {
                **_INSTANCE_PARAM,
                "id": {"type": "integer", "description": "Offer ID to archive"},
            },
        },
    ),

    # ==================== CRUD: Streams ====================
    Tool(
        name="keitaro_create_stream",
        description=(
            "Create a new stream (flow) in a campaign. Required: campaign_id, type, name. "
            "Types: regular, forced, default. "
            "Schema options: redirect, action, landings, offers."
        ),
        inputSchema={
            "type": "object",
            "required": ["campaign_id", "type", "name"],
            "properties": {
                **_INSTANCE_PARAM,
                "campaign_id": {"type": "integer"},
                "type": {"type": "string", "enum": ["regular", "forced", "default"]},
                "name": {"type": "string"},
                "action_type": {"type": "string"},
                "schema": {"type": "string", "enum": ["redirect", "action", "landings", "offers"]},
                "position": {"type": "integer"},
            },
        },
    ),
    Tool(
        name="keitaro_update_stream",
        description="Update stream fields (partial update).",
        inputSchema={
            "type": "object",
            "required": ["id"],
            "properties": {
                **_INSTANCE_PARAM,
                "id": {"type": "integer", "description": "Stream ID"},
                "name": {"type": "string"},
                "type": {"type": "string", "enum": ["regular", "forced", "default"]},
                "action_type": {"type": "string"},
                "schema": {"type": "string"},
                "position": {"type": "integer"},
            },
        },
    ),
    Tool(
        name="keitaro_delete_stream",
        description="Delete a stream from a campaign. This removes the stream permanently.",
        inputSchema={
            "type": "object",
            "required": ["id"],
            "properties": {
                **_INSTANCE_PARAM,
                "id": {"type": "integer", "description": "Stream ID to delete"},
            },
        },
    ),
    Tool(
        name="keitaro_toggle_stream",
        description="Enable or disable a stream.",
        inputSchema={
            "type": "object",
            "required": ["id", "action"],
            "properties": {
                **_INSTANCE_PARAM,
                "id": {"type": "integer", "description": "Stream ID"},
                "action": {"type": "string", "enum": ["enable", "disable"]},
            },
        },
    ),

    # ==================== CRUD: Landing Pages ====================
    Tool(
        name="keitaro_create_landing_page",
        description="Create a landing page. Required: name, action_type, action_payload (URL).",
        inputSchema={
            "type": "object",
            "required": ["name"],
            "properties": {
                **_INSTANCE_PARAM,
                "name": {"type": "string"},
                "action_type": {"type": "string"},
                "action_payload": {"type": "string", "description": "Landing page URL"},
                "group_id": {"type": "integer"},
            },
        },
    ),
    Tool(
        name="keitaro_update_landing_page",
        description="Update landing page fields.",
        inputSchema={
            "type": "object",
            "required": ["id"],
            "properties": {
                **_INSTANCE_PARAM,
                "id": {"type": "integer"},
                "name": {"type": "string"},
                "action_payload": {"type": "string"},
                "group_id": {"type": "integer"},
            },
        },
    ),
    Tool(
        name="keitaro_delete_landing_page",
        description="Archive a landing page.",
        inputSchema={
            "type": "object",
            "required": ["id"],
            "properties": {
                **_INSTANCE_PARAM,
                "id": {"type": "integer"},
            },
        },
    ),

    # ==================== CRUD: Traffic Sources ====================
    Tool(
        name="keitaro_create_traffic_source",
        description="Create a traffic source.",
        inputSchema={
            "type": "object",
            "required": ["name"],
            "properties": {
                **_INSTANCE_PARAM,
                "name": {"type": "string"},
                "postback_url": {"type": "string"},
            },
        },
    ),

    # ==================== CRUD: Affiliate Networks ====================
    Tool(
        name="keitaro_create_affiliate_network",
        description="Create an affiliate network.",
        inputSchema={
            "type": "object",
            "required": ["name"],
            "properties": {
                **_INSTANCE_PARAM,
                "name": {"type": "string"},
                "postback_url": {"type": "string"},
            },
        },
    ),

    # ==================== Domain Operations ====================
    Tool(
        name="keitaro_check_domain",
        description="Check domain DNS/SSL status. Returns updated domain info.",
        inputSchema={
            "type": "object",
            "required": ["id"],
            "properties": {
                **_INSTANCE_PARAM,
                "id": {"type": "integer", "description": "Domain ID to check"},
            },
        },
    ),
]


# ============================================================================
# Tool Routing (match/case)
# ============================================================================

@app.list_tools()
async def list_tools() -> list[Tool]:
    return TOOLS


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        match name:
            # === Platform ===
            case "keitaro_list_instances":
                return _ok(registry.list_all())

            # === Campaigns (Read) ===
            case "keitaro_list_campaigns":
                client = registry.resolve(arguments)
                result = client.list_campaigns(
                    limit=arguments.get("limit"),
                    offset=arguments.get("offset"),
                )
                return _ok(result)

            case "keitaro_get_campaign":
                client = registry.resolve(arguments)
                return _ok(client.get_campaign(arguments["id"]))

            # === Streams (Read) ===
            case "keitaro_list_streams":
                client = registry.resolve(arguments)
                return _ok(client.list_streams(arguments["campaign_id"]))

            case "keitaro_get_stream":
                client = registry.resolve(arguments)
                return _ok(client.get_stream(arguments["id"]))

            # === Offers (Read) ===
            case "keitaro_list_offers":
                client = registry.resolve(arguments)
                return _ok(client.list_offers())

            case "keitaro_get_offer":
                client = registry.resolve(arguments)
                return _ok(client.get_offer(arguments["id"]))

            # === Landing Pages (Read) ===
            case "keitaro_list_landing_pages":
                client = registry.resolve(arguments)
                return _ok(client.list_landing_pages())

            case "keitaro_get_landing_page":
                client = registry.resolve(arguments)
                return _ok(client.get_landing_page(arguments["id"]))

            # === Traffic Sources (Read) ===
            case "keitaro_list_traffic_sources":
                client = registry.resolve(arguments)
                return _ok(client.list_traffic_sources())

            case "keitaro_get_traffic_source":
                client = registry.resolve(arguments)
                return _ok(client.get_traffic_source(arguments["id"]))

            # === Affiliate Networks (Read) ===
            case "keitaro_list_affiliate_networks":
                client = registry.resolve(arguments)
                return _ok(client.list_affiliate_networks())

            case "keitaro_get_affiliate_network":
                client = registry.resolve(arguments)
                return _ok(client.get_affiliate_network(arguments["id"]))

            # === Domains (Read) ===
            case "keitaro_list_domains":
                client = registry.resolve(arguments)
                return _ok(client.list_domains())

            case "keitaro_get_domain":
                client = registry.resolve(arguments)
                return _ok(client.get_domain(arguments["id"]))

            # === Groups (Read) ===
            case "keitaro_list_groups":
                client = registry.resolve(arguments)
                return _ok(client.list_groups(group_type=arguments.get("type")))

            # === Reports & Analytics ===
            case "keitaro_build_report":
                client = registry.resolve(arguments)
                body = {
                    "range": {
                        "from": arguments["date_from"],
                        "to": arguments["date_to"],
                    },
                }
                if arguments.get("timezone"):
                    body["range"]["timezone"] = arguments["timezone"]
                if arguments.get("dimensions"):
                    body["dimensions"] = arguments["dimensions"]
                if arguments.get("measures"):
                    body["measures"] = arguments["measures"]
                if arguments.get("filters"):
                    body["filters"] = arguments["filters"]
                if arguments.get("sort"):
                    body["sort"] = arguments["sort"]
                return _ok(client.build_report(body))

            case "keitaro_get_clicks":
                client = registry.resolve(arguments)
                body = {
                    "range": {
                        "from": arguments["date_from"],
                        "to": arguments["date_to"],
                    },
                    "limit": arguments.get("limit", 100),
                }
                if arguments.get("offset"):
                    body["offset"] = arguments["offset"]
                if arguments.get("columns"):
                    body["columns"] = arguments["columns"]
                else:
                    body["columns"] = ["click_id", "datetime", "campaign", "ip", "country"]
                if arguments.get("filters"):
                    body["filters"] = arguments["filters"]
                if arguments.get("sort"):
                    body["sort"] = arguments["sort"]
                return _ok(client.get_clicks(body))

            case "keitaro_get_conversions":
                client = registry.resolve(arguments)
                body = {
                    "range": {
                        "from": arguments["date_from"],
                        "to": arguments["date_to"],
                    },
                    "limit": arguments.get("limit", 100),
                }
                if arguments.get("offset"):
                    body["offset"] = arguments["offset"]
                if arguments.get("columns"):
                    body["columns"] = arguments["columns"]
                else:
                    body["columns"] = ["conversion_id", "campaign", "status", "revenue"]
                if arguments.get("filters"):
                    body["filters"] = arguments["filters"]
                if arguments.get("sort"):
                    body["sort"] = arguments["sort"]
                return _ok(client.get_conversions(body))

            # === CRUD: Campaigns ===
            case "keitaro_create_campaign":
                client = registry.resolve(arguments)
                data = {k: v for k, v in arguments.items()
                        if k not in ("instance",) and v is not None}
                return _ok(client.create_campaign(data))

            case "keitaro_update_campaign":
                client = registry.resolve(arguments)
                campaign_id = arguments["id"]
                data = {k: v for k, v in arguments.items()
                        if k not in ("instance", "id") and v is not None}
                return _ok(client.update_campaign(campaign_id, data))

            case "keitaro_delete_campaign":
                client = registry.resolve(arguments)
                return _ok(client.delete_campaign(arguments["id"]))

            case "keitaro_clone_campaign":
                client = registry.resolve(arguments)
                return _ok(client.clone_campaign(arguments["id"]))

            case "keitaro_toggle_campaign":
                client = registry.resolve(arguments)
                if arguments["action"] == "enable":
                    return _ok(client.enable_campaign(arguments["id"]))
                else:
                    return _ok(client.disable_campaign(arguments["id"]))

            # === CRUD: Offers ===
            case "keitaro_create_offer":
                client = registry.resolve(arguments)
                data = {k: v for k, v in arguments.items()
                        if k not in ("instance",) and v is not None}
                return _ok(client.create_offer(data))

            case "keitaro_update_offer":
                client = registry.resolve(arguments)
                offer_id = arguments["id"]
                data = {k: v for k, v in arguments.items()
                        if k not in ("instance", "id") and v is not None}
                return _ok(client.update_offer(offer_id, data))

            case "keitaro_delete_offer":
                client = registry.resolve(arguments)
                return _ok(client.delete_offer(arguments["id"]))

            # === CRUD: Streams ===
            case "keitaro_create_stream":
                client = registry.resolve(arguments)
                data = {k: v for k, v in arguments.items()
                        if k not in ("instance",) and v is not None}
                return _ok(client.create_stream(data))

            case "keitaro_update_stream":
                client = registry.resolve(arguments)
                stream_id = arguments["id"]
                data = {k: v for k, v in arguments.items()
                        if k not in ("instance", "id") and v is not None}
                return _ok(client.update_stream(stream_id, data))

            case "keitaro_delete_stream":
                client = registry.resolve(arguments)
                return _ok(client.delete_stream(arguments["id"]))

            case "keitaro_toggle_stream":
                client = registry.resolve(arguments)
                if arguments["action"] == "enable":
                    return _ok(client.enable_stream(arguments["id"]))
                else:
                    return _ok(client.disable_stream(arguments["id"]))

            # === CRUD: Landing Pages ===
            case "keitaro_create_landing_page":
                client = registry.resolve(arguments)
                data = {k: v for k, v in arguments.items()
                        if k not in ("instance",) and v is not None}
                return _ok(client.create_landing_page(data))

            case "keitaro_update_landing_page":
                client = registry.resolve(arguments)
                landing_id = arguments["id"]
                data = {k: v for k, v in arguments.items()
                        if k not in ("instance", "id") and v is not None}
                return _ok(client.update_landing_page(landing_id, data))

            case "keitaro_delete_landing_page":
                client = registry.resolve(arguments)
                return _ok(client.delete_landing_page(arguments["id"]))

            # === CRUD: Traffic Sources ===
            case "keitaro_create_traffic_source":
                client = registry.resolve(arguments)
                data = {k: v for k, v in arguments.items()
                        if k not in ("instance",) and v is not None}
                return _ok(client.create_traffic_source(data))

            # === CRUD: Affiliate Networks ===
            case "keitaro_create_affiliate_network":
                client = registry.resolve(arguments)
                data = {k: v for k, v in arguments.items()
                        if k not in ("instance",) and v is not None}
                return _ok(client.create_affiliate_network(data))

            # === Domain Operations ===
            case "keitaro_check_domain":
                client = registry.resolve(arguments)
                return _ok(client.check_domain(arguments["id"]))

            case _:
                return _err(f"Unknown tool: {name}")

    except KeitaroError as e:
        return _err(f"Keitaro API error: HTTP {e.status_code} — {e.body[:300]}")
    except (KeyError, ValueError) as e:
        return _err(str(e))
    except Exception as e:
        return _err(f"Unexpected error: {e}")


# ============================================================================
# Entry point
# ============================================================================

def run():
    """Start the MCP server."""
    _init()

    async def _run():
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())

    asyncio.run(_run())
