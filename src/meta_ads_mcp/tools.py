"""MCP tool definitions wrapping the Meta Marketing API.

29 tools split across 6 domains:
- Accounts (3)
- Campaigns (7)
- Ad Sets (4)
- Ads & Creatives (4)
- Insights & Reporting (4)
- Audiences & Targeting (4)
- Account-level helpers (3)
"""

from __future__ import annotations

from typing import Any

from .client import MetaAdsClient

# ────────────────────────────────────────────────────────────────────
# Accounts (3)
# ────────────────────────────────────────────────────────────────────


async def list_ad_accounts(client: MetaAdsClient) -> list[dict]:
    """List all ad accounts the token has access to (via /me/adaccounts)."""
    return await client.paginated(
        "me/adaccounts",
        fields="id,name,account_status,currency,timezone_name,balance,amount_spent",
    )


async def get_ad_account(client: MetaAdsClient, account_id: str | None = None) -> dict:
    """Detailed view of one ad account (default = META_AD_ACCOUNT_ID)."""
    acct = client._account(account_id)
    return await client.get(
        acct,
        fields="id,name,account_status,currency,timezone_name,balance,amount_spent,"
               "spend_cap,daily_spend_limit,business,disable_reason,age",
    )


async def get_account_balance(client: MetaAdsClient, account_id: str | None = None) -> dict:
    """Balance + monthly cumulative spend for one ad account."""
    acct = client._account(account_id)
    info = await client.get(acct, fields="balance,amount_spent,currency,spend_cap")
    return {
        "account_id": acct,
        "currency": info.get("currency"),
        "balance": info.get("balance"),
        "amount_spent": info.get("amount_spent"),
        "spend_cap": info.get("spend_cap"),
    }


# ────────────────────────────────────────────────────────────────────
# Campaigns (7)
# ────────────────────────────────────────────────────────────────────


async def list_campaigns(
    client: MetaAdsClient,
    account_id: str | None = None,
    status: list[str] | None = None,
) -> list[dict]:
    """All campaigns for an ad account. Optionally filter by status."""
    acct = client._account(account_id)
    params: dict[str, Any] = {
        "fields": "id,name,status,objective,daily_budget,lifetime_budget,"
                  "start_time,stop_time,buying_type,bid_strategy,created_time"
    }
    if status:
        params["effective_status"] = str(status).replace("'", '"')
    return await client.paginated(f"{acct}/campaigns", **params)


async def get_campaign(client: MetaAdsClient, campaign_id: str) -> dict:
    """Full details of one campaign."""
    return await client.get(
        campaign_id,
        fields="id,name,status,effective_status,objective,daily_budget,lifetime_budget,"
               "start_time,stop_time,buying_type,bid_strategy,special_ad_categories,"
               "created_time,updated_time,configured_status",
    )


async def create_campaign(
    client: MetaAdsClient,
    name: str,
    objective: str,
    status: str = "PAUSED",
    daily_budget: int | None = None,
    lifetime_budget: int | None = None,
    special_ad_categories: list[str] | None = None,
    account_id: str | None = None,
) -> dict:
    """Create a new campaign (defaults PAUSED for safety).

    Args:
        name: campaign name
        objective: e.g. OUTCOME_TRAFFIC, OUTCOME_LEADS, OUTCOME_SALES
        status: PAUSED | ACTIVE
        daily_budget: in cents (e.g. 5000 = 50€/day)
        lifetime_budget: in cents
        special_ad_categories: e.g. ["EMPLOYMENT"], ["HOUSING"], or [] (recommended)
    """
    acct = client._account(account_id)
    data: dict[str, Any] = {
        "name": name,
        "objective": objective,
        "status": status,
        "special_ad_categories": str(special_ad_categories or []).replace("'", '"'),
    }
    if daily_budget is not None:
        data["daily_budget"] = daily_budget
    if lifetime_budget is not None:
        data["lifetime_budget"] = lifetime_budget
    return await client.post(f"{acct}/campaigns", **data)


async def update_campaign(
    client: MetaAdsClient,
    campaign_id: str,
    name: str | None = None,
    status: str | None = None,
    daily_budget: int | None = None,
    lifetime_budget: int | None = None,
) -> dict:
    """Patch campaign fields (name, status, budget)."""
    data = {k: v for k, v in {
        "name": name, "status": status,
        "daily_budget": daily_budget, "lifetime_budget": lifetime_budget,
    }.items() if v is not None}
    return await client.post(campaign_id, **data)


async def pause_campaign(client: MetaAdsClient, campaign_id: str) -> dict:
    """Set status=PAUSED. Sugar for `update_campaign(status='PAUSED')`."""
    return await update_campaign(client, campaign_id, status="PAUSED")


async def resume_campaign(client: MetaAdsClient, campaign_id: str) -> dict:
    """Set status=ACTIVE. Sugar for `update_campaign(status='ACTIVE')`."""
    return await update_campaign(client, campaign_id, status="ACTIVE")


async def archive_campaign(client: MetaAdsClient, campaign_id: str) -> dict:
    """Set status=ARCHIVED (irreversible from UI but reversible via API)."""
    return await update_campaign(client, campaign_id, status="ARCHIVED")


# ────────────────────────────────────────────────────────────────────
# Ad Sets (4)
# ────────────────────────────────────────────────────────────────────


async def list_adsets(
    client: MetaAdsClient,
    campaign_id: str | None = None,
    account_id: str | None = None,
) -> list[dict]:
    """List ad sets — scoped to a campaign or all account ad sets."""
    fields = ("id,name,status,campaign_id,daily_budget,lifetime_budget,"
              "billing_event,optimization_goal,bid_amount,start_time,end_time,targeting")
    if campaign_id:
        return await client.paginated(f"{campaign_id}/adsets", fields=fields)
    acct = client._account(account_id)
    return await client.paginated(f"{acct}/adsets", fields=fields)


async def get_adset(client: MetaAdsClient, adset_id: str) -> dict:
    """Full details of one ad set."""
    return await client.get(
        adset_id,
        fields="id,name,status,effective_status,campaign_id,daily_budget,lifetime_budget,"
               "billing_event,optimization_goal,bid_amount,start_time,end_time,"
               "targeting,promoted_object,attribution_spec",
    )


async def create_adset(
    client: MetaAdsClient,
    campaign_id: str,
    name: str,
    daily_budget: int,
    optimization_goal: str,
    billing_event: str = "IMPRESSIONS",
    targeting: dict | None = None,
    status: str = "PAUSED",
    account_id: str | None = None,
) -> dict:
    """Create an ad set under a campaign.

    Args:
        targeting: e.g. {"geo_locations": {"countries": ["FR"]}, "age_min": 25, "age_max": 55}
    """
    import json
    acct = client._account(account_id)
    data: dict[str, Any] = {
        "name": name,
        "campaign_id": campaign_id,
        "daily_budget": daily_budget,
        "optimization_goal": optimization_goal,
        "billing_event": billing_event,
        "status": status,
        "targeting": json.dumps(targeting or {"geo_locations": {"countries": ["FR"]}}),
    }
    return await client.post(f"{acct}/adsets", **data)


async def update_adset(
    client: MetaAdsClient,
    adset_id: str,
    name: str | None = None,
    status: str | None = None,
    daily_budget: int | None = None,
    bid_amount: int | None = None,
) -> dict:
    """Patch an ad set."""
    data = {k: v for k, v in {
        "name": name, "status": status,
        "daily_budget": daily_budget, "bid_amount": bid_amount,
    }.items() if v is not None}
    return await client.post(adset_id, **data)


# ────────────────────────────────────────────────────────────────────
# Ads & Creatives (4)
# ────────────────────────────────────────────────────────────────────


async def list_ads(
    client: MetaAdsClient,
    adset_id: str | None = None,
    campaign_id: str | None = None,
    account_id: str | None = None,
) -> list[dict]:
    """List ads scoped to ad set, campaign, or whole account."""
    fields = "id,name,status,adset_id,campaign_id,creative,created_time,updated_time"
    if adset_id:
        return await client.paginated(f"{adset_id}/ads", fields=fields)
    if campaign_id:
        return await client.paginated(f"{campaign_id}/ads", fields=fields)
    acct = client._account(account_id)
    return await client.paginated(f"{acct}/ads", fields=fields)


async def get_ad(client: MetaAdsClient, ad_id: str) -> dict:
    """Full details of one ad including creative."""
    return await client.get(
        ad_id,
        fields="id,name,status,effective_status,adset_id,campaign_id,"
               "creative{id,name,title,body,image_url,thumbnail_url,object_story_spec},"
               "tracking_specs,conversion_specs,created_time",
    )


async def list_creatives(
    client: MetaAdsClient, account_id: str | None = None
) -> list[dict]:
    """List all creatives in an ad account."""
    acct = client._account(account_id)
    return await client.paginated(
        f"{acct}/adcreatives",
        fields="id,name,title,body,image_url,thumbnail_url,object_type,status",
    )


async def create_ad(
    client: MetaAdsClient,
    adset_id: str,
    name: str,
    creative_id: str,
    status: str = "PAUSED",
    account_id: str | None = None,
) -> dict:
    """Create an ad linking a creative to an ad set."""
    import json
    acct = client._account(account_id)
    return await client.post(
        f"{acct}/ads",
        name=name,
        adset_id=adset_id,
        creative=json.dumps({"creative_id": creative_id}),
        status=status,
    )


# ────────────────────────────────────────────────────────────────────
# Insights & Reporting (4)
# ────────────────────────────────────────────────────────────────────


async def get_insights(
    client: MetaAdsClient,
    object_id: str,
    date_preset: str = "last_30d",
    fields: str | None = None,
    breakdowns: list[str] | None = None,
    level: str = "campaign",
) -> list[dict]:
    """Performance insights for any object (account, campaign, adset, ad).

    Args:
        object_id: e.g. act_123, campaign_id, adset_id, ad_id
        date_preset: today, yesterday, last_7d, last_14d, last_30d, last_90d,
                     this_month, last_month, this_quarter, lifetime
        fields: comma-sep custom fields, default = standard set
        breakdowns: e.g. ["age","gender"], ["country"], ["publisher_platform"]
        level: account | campaign | adset | ad
    """
    f = fields or ("spend,impressions,clicks,ctr,cpc,cpm,reach,frequency,"
                   "actions,action_values,cost_per_action_type,"
                   "video_p100_watched_actions")
    params: dict[str, Any] = {
        "fields": f, "date_preset": date_preset, "level": level,
    }
    if breakdowns:
        params["breakdowns"] = ",".join(breakdowns)
    return await client.paginated(f"{object_id}/insights", **params)


async def get_spend_by_day(
    client: MetaAdsClient,
    object_id: str,
    days: int = 30,
) -> list[dict]:
    """Daily spend time series for a campaign/account."""
    return await client.paginated(
        f"{object_id}/insights",
        fields="spend,impressions,clicks,ctr,cpc,actions",
        time_increment=1,
        date_preset=f"last_{days}d",
    )


async def get_account_summary(
    client: MetaAdsClient,
    account_id: str | None = None,
    date_preset: str = "last_30d",
) -> dict:
    """One-shot summary : account-level KPIs over a period."""
    acct = client._account(account_id)
    rows = await client.paginated(
        f"{acct}/insights",
        fields="spend,impressions,clicks,reach,frequency,ctr,cpc,cpm,actions",
        date_preset=date_preset,
        level="account",
    )
    return rows[0] if rows else {}


async def export_campaign_csv(
    client: MetaAdsClient,
    object_id: str,
    date_preset: str = "last_30d",
    breakdowns: list[str] | None = None,
) -> str:
    """Return CSV-formatted insights (1 line per breakdown bucket)."""
    rows = await get_insights(
        client, object_id, date_preset=date_preset, breakdowns=breakdowns,
    )
    if not rows:
        return ""
    keys = sorted({k for r in rows for k in r.keys()})
    lines = [",".join(keys)]
    for r in rows:
        lines.append(",".join(str(r.get(k, "")).replace(",", ";") for k in keys))
    return "\n".join(lines)


# ────────────────────────────────────────────────────────────────────
# Audiences & Targeting (4)
# ────────────────────────────────────────────────────────────────────


async def list_audiences(
    client: MetaAdsClient, account_id: str | None = None
) -> list[dict]:
    """List custom + lookalike audiences in an ad account."""
    acct = client._account(account_id)
    return await client.paginated(
        f"{acct}/customaudiences",
        fields="id,name,subtype,description,approximate_count_lower_bound,"
               "approximate_count_upper_bound,delivery_status,operation_status",
    )


async def create_custom_audience(
    client: MetaAdsClient,
    name: str,
    description: str = "",
    subtype: str = "CUSTOM",
    customer_file_source: str = "USER_PROVIDED_ONLY",
    account_id: str | None = None,
) -> dict:
    """Create an empty custom audience (data added separately via /users)."""
    acct = client._account(account_id)
    return await client.post(
        f"{acct}/customaudiences",
        name=name, description=description, subtype=subtype,
        customer_file_source=customer_file_source,
    )


async def search_targeting(
    client: MetaAdsClient,
    query: str,
    type: str = "adinterest",
    limit: int = 25,
) -> list[dict]:
    """Search Meta's targeting catalog (interests, behaviors, demographics).

    type: adinterest, adworkemployer, adworkposition, education_school,
          adgeolocation (with location_types=country|region|city), etc.
    """
    return await client.paginated(
        "search", type=type, q=query, limit=limit,
    )


async def estimate_audience_size(
    client: MetaAdsClient,
    targeting: dict,
    optimization_goal: str = "REACH",
    account_id: str | None = None,
) -> dict:
    """Estimate audience size + delivery for a targeting spec."""
    import json
    acct = client._account(account_id)
    return await client.get(
        f"{acct}/delivery_estimate",
        targeting_spec=json.dumps(targeting),
        optimization_goal=optimization_goal,
    )


# ────────────────────────────────────────────────────────────────────
# Account helpers (3)
# ────────────────────────────────────────────────────────────────────


async def list_pixels(client: MetaAdsClient, account_id: str | None = None) -> list[dict]:
    """List all Meta pixels in an ad account."""
    acct = client._account(account_id)
    return await client.paginated(
        f"{acct}/adspixels",
        fields="id,name,code,creator,owner_business,is_unavailable",
    )


async def list_business_users(
    client: MetaAdsClient, account_id: str | None = None
) -> list[dict]:
    """List users with access to an ad account."""
    acct = client._account(account_id)
    return await client.paginated(
        f"{acct}/users",
        fields="id,name,permissions,role",
    )


async def duplicate_campaign(
    client: MetaAdsClient,
    campaign_id: str,
    new_name: str | None = None,
    deep_copy: bool = True,
) -> dict:
    """Server-side copy of a campaign (incl. ad sets + ads if deep_copy)."""
    return await client.post(
        f"{campaign_id}/copies",
        deep_copy="true" if deep_copy else "false",
        rename_options=f'{{"rename_strategy":"DEEP_RENAME","rename_prefix":"{new_name or "Copy of"} "}}',
    )


# ────────────────────────────────────────────────────────────────────
# Registry — used by the MCP server to expose all tools
# ────────────────────────────────────────────────────────────────────

ALL_TOOLS = [
    # Accounts
    list_ad_accounts, get_ad_account, get_account_balance,
    # Campaigns
    list_campaigns, get_campaign, create_campaign, update_campaign,
    pause_campaign, resume_campaign, archive_campaign,
    # Ad Sets
    list_adsets, get_adset, create_adset, update_adset,
    # Ads & Creatives
    list_ads, get_ad, list_creatives, create_ad,
    # Insights
    get_insights, get_spend_by_day, get_account_summary, export_campaign_csv,
    # Audiences
    list_audiences, create_custom_audience, search_targeting, estimate_audience_size,
    # Helpers
    list_pixels, list_business_users, duplicate_campaign,
]

assert len(ALL_TOOLS) == 29, f"Expected 29 tools, got {len(ALL_TOOLS)}"
