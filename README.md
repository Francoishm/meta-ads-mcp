# meta-ads-mcp

> MCP server exposing the Meta (Facebook/Instagram) Marketing API to Claude.

29 tools split across Accounts, Campaigns, Ad Sets, Ads & Creatives, Insights,
Audiences/Targeting, Helpers. Read **and** write capabilities (campaign
create/pause/resume, audience builder, etc.). Read-only mode available.

## Features

| Domain | Tools |
|---|---|
| Accounts | `list_ad_accounts`, `get_ad_account`, `get_account_balance` |
| Campaigns | `list_campaigns`, `get_campaign`, `create_campaign`, `update_campaign`, `pause_campaign`, `resume_campaign`, `archive_campaign` |
| Ad Sets | `list_adsets`, `get_adset`, `create_adset`, `update_adset` |
| Ads & Creatives | `list_ads`, `get_ad`, `list_creatives`, `create_ad` |
| Insights | `get_insights`, `get_spend_by_day`, `get_account_summary`, `export_campaign_csv` |
| Audiences | `list_audiences`, `create_custom_audience`, `search_targeting`, `estimate_audience_size` |
| Helpers | `list_pixels`, `list_business_users`, `duplicate_campaign` |

## Quick start

### 1. Get a Meta access token

1. Create an app at https://developers.facebook.com/apps (type "Business")
2. Add the **Marketing API** product
3. Generate a **System User token** (preferred — long-lived) or use Graph
   API Explorer for testing
4. Required scopes: `ads_management`, `ads_read`, `business_management`,
   `read_insights`
5. Note your ad account id (format `act_XXXXXXXXX`)

### 2. Install the server

```bash
git clone https://github.com/Francoishm/meta-ads-mcp
cd meta-ads-mcp
./scripts/install.sh
```

Edit `.env` :

```ini
META_ACCESS_TOKEN=EAA...
META_AD_ACCOUNT_ID=act_123456789
```

### 3. Connect to Claude Desktop (stdio)

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` :

```json
{
  "mcpServers": {
    "meta-ads": {
      "command": "/full/path/to/meta-ads-mcp/.venv/bin/meta-ads-mcp",
      "env": {
        "META_ACCESS_TOKEN": "EAA...",
        "META_AD_ACCOUNT_ID": "act_123456789"
      }
    }
  }
}
```

Restart Claude Desktop. The 29 Meta tools should appear in the tool picker.

### 4. Connect remotely via SSE (optional)

If you've deployed the server on a remote VPS (see `scripts/meta-ads-mcp.service`):

```bash
.venv/bin/meta-ads-mcp --sse --host 0.0.0.0 --port 8765
```

In Claude Desktop config :

```json
{
  "mcpServers": {
    "meta-ads": {
      "url": "https://your-vps/sse"
    }
  }
}
```

> **Always front the SSE endpoint with HTTPS + auth (nginx + basic auth or
> mTLS).** The Meta token gives full account access.

## Safety

- Set `META_READ_ONLY=true` in `.env` to disable all write tools (campaign
  creation, status updates, audience creation).
- All `create_*` tools default to `status="PAUSED"` — newly created campaigns
  /ad sets /ads do **not** start spending until you explicitly resume them.
- The server logs every tool invocation; rotate logs and never log token.

## Common usage in Claude

```
Show me the campaigns running in my ad account this month.
→ list_campaigns + get_insights with date_preset=this_month

Pause all campaigns spending more than 30€ for less than 1% CTR.
→ list_campaigns → get_insights → pause_campaign for matches

Create a new campaign for the spring promo, daily budget 50€,
audience women 30-50 in Île-de-France interested in fitness.
→ search_targeting + estimate_audience_size + create_campaign
  + create_adset + create_ad
```

## Development

```bash
. .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## License

MIT
