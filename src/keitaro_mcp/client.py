"""Keitaro Tracker Admin API Client.

HTTP client for Keitaro Tracker Admin API (/admin_api/v1).
Zero external dependencies — uses only stdlib (subprocess + curl).

Supports all Keitaro entities: campaigns, offers, streams, landing pages,
traffic sources, affiliate networks, domains, groups, reports, clicks,
conversions, users, logs, bot list.

Authentication: Api-Key header.
Uses curl subprocess to bypass Cloudflare JA3 TLS fingerprinting.
"""

import json
import subprocess
import urllib.parse

from keitaro_mcp.errors import KeitaroError


class KeitaroClient:
    """HTTP client for a single Keitaro tracker instance.

    All endpoints are under /admin_api/v1/.
    Authentication via Api-Key header.
    Uses curl to avoid Cloudflare blocking Python TLS fingerprints.
    """

    def __init__(self, base_url: str, api_key: str, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def _request(
        self,
        method: str,
        path: str,
        data: dict | list | None = None,
        params: dict | None = None,
    ) -> dict | list:
        """Core HTTP method. All API calls go through here via curl."""
        url = f"{self.base_url}/admin_api/v1{path}"
        if params:
            filtered = {k: v for k, v in params.items() if v is not None}
            if filtered:
                url = f"{url}?{urllib.parse.urlencode(filtered)}"

        cmd = [
            "curl", "-s", "-S", "--fail-with-body",
            "-X", method,
            "-H", f"Api-Key: {self.api_key}",
            "-H", "Content-Type: application/json",
            "-H", "Accept: application/json",
            "--max-time", str(self.timeout),
            "-w", "\n%{http_code}",
        ]
        if data is not None:
            cmd += ["-d", json.dumps(data, ensure_ascii=False)]
        cmd.append(url)

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout + 5)
        except subprocess.TimeoutExpired as e:
            raise KeitaroError(0, "Request timed out", url) from e

        output = result.stdout.rstrip()
        lines = output.rsplit("\n", 1)
        body = lines[0] if len(lines) > 1 else ""
        status = int(lines[-1]) if lines[-1].isdigit() else 0

        if status >= 400 or result.returncode != 0:
            raise KeitaroError(status, body or result.stderr, url)

        return json.loads(body) if body else {}

    # ==================== Campaigns ====================

    def list_campaigns(self, limit: int | None = None, offset: int | None = None) -> list:
        """List all campaigns."""
        return self._request("GET", "/campaigns", params={"limit": limit, "offset": offset})

    def get_campaign(self, campaign_id: int) -> dict:
        """Get campaign by ID."""
        return self._request("GET", f"/campaigns/{campaign_id}")

    def create_campaign(self, data: dict) -> dict:
        """Create campaign. Required: alias, name."""
        return self._request("POST", "/campaigns", data=data)

    def update_campaign(self, campaign_id: int, data: dict) -> dict:
        """Update campaign fields (partial update)."""
        return self._request("PUT", f"/campaigns/{campaign_id}", data=data)

    def delete_campaign(self, campaign_id: int) -> dict:
        """Archive campaign (soft delete)."""
        return self._request("DELETE", f"/campaigns/{campaign_id}")

    def clone_campaign(self, campaign_id: int) -> dict:
        """Duplicate campaign."""
        return self._request("POST", f"/campaigns/{campaign_id}/clone")

    def enable_campaign(self, campaign_id: int) -> dict:
        """Activate campaign."""
        return self._request("POST", f"/campaigns/{campaign_id}/enable")

    def disable_campaign(self, campaign_id: int) -> dict:
        """Deactivate campaign."""
        return self._request("POST", f"/campaigns/{campaign_id}/disable")

    def restore_campaign(self, campaign_id: int) -> dict:
        """Restore archived campaign."""
        return self._request("POST", f"/campaigns/{campaign_id}/restore")

    def list_deleted_campaigns(self) -> list:
        """List archived campaigns."""
        return self._request("GET", "/campaigns/deleted")

    # ==================== Streams (Flows) ====================

    def list_streams(self, campaign_id: int) -> list:
        """List streams for a campaign."""
        return self._request("GET", f"/campaigns/{campaign_id}/streams")

    def get_stream(self, stream_id: int) -> dict:
        """Get stream by ID."""
        return self._request("GET", f"/streams/{stream_id}")

    def create_stream(self, data: dict) -> dict:
        """Create stream. Required: campaign_id, type, name."""
        return self._request("POST", "/streams", data=data)

    def update_stream(self, stream_id: int, data: dict) -> dict:
        """Update stream fields."""
        return self._request("PUT", f"/streams/{stream_id}", data=data)

    def delete_stream(self, stream_id: int) -> dict:
        """Delete stream."""
        return self._request("DELETE", f"/streams/{stream_id}")

    def enable_stream(self, stream_id: int) -> dict:
        return self._request("POST", f"/streams/{stream_id}/enable")

    def disable_stream(self, stream_id: int) -> dict:
        return self._request("POST", f"/streams/{stream_id}/disable")

    def search_streams(self, query: str | None = None) -> list:
        """Search streams."""
        return self._request("GET", "/streams/search", params={"query": query})

    # ==================== Offers ====================

    def list_offers(self) -> list:
        """List all offers."""
        return self._request("GET", "/offers")

    def get_offer(self, offer_id: int) -> dict:
        """Get offer by ID."""
        return self._request("GET", f"/offers/{offer_id}")

    def create_offer(self, data: dict) -> dict:
        """Create offer. Required: name."""
        return self._request("POST", "/offers", data=data)

    def update_offer(self, offer_id: int, data: dict) -> dict:
        """Update offer fields."""
        return self._request("PUT", f"/offers/{offer_id}", data=data)

    def delete_offer(self, offer_id: int) -> dict:
        """Archive offer."""
        return self._request("DELETE", f"/offers/{offer_id}/archive")

    def clone_offer(self, offer_id: int) -> dict:
        """Duplicate offer."""
        return self._request("POST", f"/offers/{offer_id}/clone")

    # ==================== Landing Pages ====================

    def list_landing_pages(self) -> list:
        """List all landing pages."""
        return self._request("GET", "/landing_pages")

    def get_landing_page(self, landing_id: int) -> dict:
        """Get landing page by ID."""
        return self._request("GET", f"/landing_pages/{landing_id}")

    def create_landing_page(self, data: dict) -> dict:
        """Create landing page."""
        return self._request("POST", "/landing_pages", data=data)

    def update_landing_page(self, landing_id: int, data: dict) -> dict:
        """Update landing page."""
        return self._request("PUT", f"/landing_pages/{landing_id}", data=data)

    def delete_landing_page(self, landing_id: int) -> dict:
        """Archive landing page."""
        return self._request("DELETE", f"/landing_pages/{landing_id}")

    # ==================== Traffic Sources ====================

    def list_traffic_sources(self) -> list:
        """List all traffic sources."""
        return self._request("GET", "/traffic_sources")

    def get_traffic_source(self, ts_id: int) -> dict:
        """Get traffic source by ID."""
        return self._request("GET", f"/traffic_sources/{ts_id}")

    def create_traffic_source(self, data: dict) -> dict:
        """Create traffic source."""
        return self._request("POST", "/traffic_sources", data=data)

    def update_traffic_source(self, ts_id: int, data: dict) -> dict:
        """Update traffic source."""
        return self._request("PUT", f"/traffic_sources/{ts_id}", data=data)

    def delete_traffic_source(self, ts_id: int) -> dict:
        """Delete traffic source."""
        return self._request("DELETE", f"/traffic_sources/{ts_id}")

    # ==================== Affiliate Networks ====================

    def list_affiliate_networks(self) -> list:
        """List all affiliate networks."""
        return self._request("GET", "/affiliate_networks")

    def get_affiliate_network(self, network_id: int) -> dict:
        """Get affiliate network by ID."""
        return self._request("GET", f"/affiliate_networks/{network_id}")

    def create_affiliate_network(self, data: dict) -> dict:
        """Create affiliate network."""
        return self._request("POST", "/affiliate_networks", data=data)

    def update_affiliate_network(self, network_id: int, data: dict) -> dict:
        """Update affiliate network."""
        return self._request("PUT", f"/affiliate_networks/{network_id}", data=data)

    def delete_affiliate_network(self, network_id: int) -> dict:
        """Archive affiliate network."""
        return self._request("DELETE", f"/affiliate_networks/{network_id}")

    # ==================== Domains ====================

    def list_domains(self) -> list:
        """List all domains."""
        return self._request("GET", "/domains")

    def get_domain(self, domain_id: int) -> dict:
        """Get domain by ID."""
        return self._request("GET", f"/domains/{domain_id}")

    def create_domain(self, data: dict) -> dict:
        """Create domain."""
        return self._request("POST", "/domains", data=data)

    def update_domain(self, domain_id: int, data: dict) -> dict:
        """Update domain."""
        return self._request("PUT", f"/domains/{domain_id}", data=data)

    def delete_domain(self, domain_id: int) -> dict:
        """Archive domain."""
        return self._request("DELETE", f"/domains/{domain_id}")

    def check_domain(self, domain_id: int) -> dict:
        """Check domain DNS/SSL status."""
        return self._request("POST", f"/domains/{domain_id}/check")

    def get_server_ip(self) -> dict:
        """Get tracker server IPs (ipv4, ipv6)."""
        return self._request("GET", "/domains/ip")

    # ==================== Groups ====================

    def list_groups(self, group_type: str | None = None) -> list:
        """List groups. Types: campaigns, offers, landings, domains."""
        return self._request("GET", "/groups", params={"type": group_type})

    def create_group(self, data: dict) -> dict:
        """Create group."""
        return self._request("POST", "/groups", data=data)

    def update_group(self, group_id: int, data: dict) -> dict:
        """Update group."""
        return self._request("PUT", f"/groups/{group_id}", data=data)

    def delete_group(self, group_id: int) -> dict:
        """Delete group."""
        return self._request("DELETE", f"/groups/{group_id}/delete")

    # ==================== Reports ====================

    def build_report(self, data: dict) -> dict:
        """Build aggregated report. POST /report/build with full query body."""
        return self._request("POST", "/report/build", data=data)

    def get_report_labels(self) -> dict:
        """Get report labels."""
        return self._request("GET", "/report/labels")

    def update_report_labels(self, data: dict) -> dict:
        """Update report labels."""
        return self._request("POST", "/report/labels", data=data)

    # ==================== Clicks (Raw Data) ====================

    def get_clicks(self, data: dict) -> dict:
        """Query raw click records. POST /clicks/log with query body."""
        return self._request("POST", "/clicks/log", data=data)

    def update_click_costs(self, data: dict) -> dict:
        """Bulk update click costs."""
        return self._request("POST", "/clicks/update_costs", data=data)

    def clean_stats(self, start_date: str, end_date: str, timezone: str = "UTC") -> dict:
        """Delete stats for date range. DESTRUCTIVE — cannot be undone."""
        return self._request("POST", "/clicks/clean", data={
            "start_date": start_date,
            "end_date": end_date,
            "timezone": timezone,
        })

    # ==================== Conversions (Raw Data) ====================

    def get_conversions(self, data: dict) -> dict:
        """Query raw conversion records. POST /conversions/log with query body."""
        return self._request("POST", "/conversions/log", data=data)

    # ==================== Users ====================

    def list_users(self) -> list:
        """List all users."""
        return self._request("GET", "/users")

    def get_user(self, user_id: int) -> dict:
        """Get user by ID."""
        return self._request("GET", f"/users/{user_id}")

    # ==================== Logs ====================

    def get_logs(self, log_type: str, limit: int | None = None, offset: int | None = None) -> list:
        """Get log entries by type."""
        return self._request("GET", f"/logs/{log_type}", params={"limit": limit, "offset": offset})

    def get_log_types(self) -> list:
        """Get available log types."""
        return self._request("POST", "/logs/types")

    # ==================== Bot List ====================

    def get_botlist(self) -> str:
        """Get bot IP list."""
        return self._request("GET", "/botlist")

    def add_to_botlist(self, ips: str) -> dict:
        """Add IPs to bot list."""
        return self._request("POST", "/botlist/add", data={"ips": ips})
