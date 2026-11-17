# Noctua B2B Data & GTM Tools for MCP, Clay & n8n

Lightweight, browserless B2B intelligence & lead-enrichment APIs built for **Model Context Protocol (MCP) agents** (`Claude Desktop`, `Cursor`, `Windsurf`), **Clay tables**, **n8n / Make workflows**, and outbound GTM pipelines.

All three tools run on minimal **256 MB** serverless containers via [Apify Store](https://apify.com/kkhome) using official public endpoints and clean SSR parsing — keeping compute overhead near **$0.00** with **automatic cross-run deduplication**.

---

## Tool Matrix Overview

| Tool | Core Capability | Built-In Verified Index | All-Inclusive PPE Pricing |
| :--- | :--- | :--- | :--- |
| **[Unified ATS Jobs & Tech Signals](https://apify.com/kkhome/unified-ats-jobs)** | Real-time job & hiring-intent API across **7 ATS** (`Workday`, `Greenhouse`, `Ashby`, `Lever`, `SmartRecruiters`, `Recruitee`, `Workable`) + bare company domain auto-discovery (`airtable.com` -> live ATS) + 60+ B2B tech stack signals | **4,066+ Employers** (~780K active jobs, incl. 1,534 Workday portals) | **$1.50 / 1,000 jobs** |
| **[Shopify & WooCommerce Store Leads](https://apify.com/kkhome/store-tech-leads)** | Ecommerce lead discovery & domain enrichment: verified emails (incl. `/policies/contact-information` disclosures), phones, physical addresses, 65+ apps, **Shopify OS 2.0 Web Pixels sandbox**, `isShopifyPlus` & monthly SaaS tech spend (`$/mo`) | **16,345+ Live Stores** (`10,148` Shopify + `6,197` custom-domain WooCommerce) + Live Web Long-Tail Search | **$2.00 / 1,000 stores** |
| **[Shopify App & Chrome Reviews + Churn Leads](https://apify.com/kkhome/shopify-chrome-app-reviews)** | 3-in-1 marketplace intelligence (`Shopify App Store`, `Chrome Web Store`, `WordPress.org Plugins`): category/partner benchmarks, pricing plans, `Built for Shopify`, Chrome manifest permissions, deterministic pain/churn tags — **plus live resolution of unhappy Shopify app reviewers into merchant domains & contact emails** | **22,300+ Merchant Lookup Keys** + 24-Country ccTLD Live Storefront Scanner | **$1.00 / 1,000 items** |

---

## 1. Connect to Claude Desktop / Cursor via Official Apify MCP

Add the following block to your `claude_desktop_config.json` or `.cursor/mcp.json` (replace `<YOUR_APIFY_TOKEN>` with your free [Apify API token](https://console.apify.com/settings/integrations)):

```json
{
  "mcpServers": {
    "noctua-b2b-intelligence": {
      "command": "npx",
      "args": [
        "-y",
        "@apify/actors-mcp-server",
        "--actors",
        "kkhome/unified-ats-jobs,kkhome/store-tech-leads,kkhome/shopify-chrome-app-reviews"
      ],
      "env": {
        "APIFY_TOKEN": "<YOUR_APIFY_TOKEN>"
      }
    }
  }
}
```

### Example Agent Prompts Once Connected
- *"Find US remote Account Executive roles posted in the last 7 days at companies using HubSpot and Snowflake, including their company domains and normalized salaries."*
- *"Discover 25 US coffee or skincare Shopify stores spending at least $100/month on apps that use Klaviyo but are missing the TikTok Pixel, with verified contact emails."*
- *"Pull the newest 1-star and 2-star reviews on Klaviyo and Yotpo from the Shopify App Store, tag billing complaints, and resolve the unhappy merchants' live store domains and emails."*

---

## 2. Clay HTTP API Enrichment Recipes

### Recipe A: Bare Company Domain -> Live Hiring & Tech Stack Signals
- **Endpoint**: `POST https://api.apify.com/v2/acts/kkhome~unified-ats-jobs/run-sync-get-dataset-items?token=<YOUR_APIFY_TOKEN>`
- **JSON Body**:
```json
{
  "targets": ["{{company_domain}}"],
  "postedWithinDays": 30,
  "maxResults": 10
}
```

### Recipe B: Ecommerce Domain -> Emails, Web Pixels 2.0, Shopify Plus & Est. Monthly SaaS Spend
- **Endpoint**: `POST https://api.apify.com/v2/acts/kkhome~store-tech-leads/run-sync-get-dataset-items?token=<YOUR_APIFY_TOKEN>`
- **JSON Body**:
```json
{
  "domains": ["{{store_domain}}"],
  "maxResults": 1
}
```

### Recipe C: Weekly Competitor Churn Outbound (Never Billed Twice)
- **Endpoint**: `POST https://api.apify.com/v2/acts/kkhome~shopify-chrome-app-reviews/run-sync-get-dataset-items?token=<YOUR_APIFY_TOKEN>`
- **JSON Body**:
```json
{
  "targets": [
    "https://apps.shopify.com/klaviyo-email-marketing",
    "https://apps.shopify.com/yotpo-social-reviews"
  ],
  "minRating": 1,
  "maxRating": 2,
  "sortBy": "newest",
  "enrichMerchantLeads": true,
  "onlyWithMerchantEmail": true,
  "skipPreviousReviews": true,
  "dedupListName": "weekly-churn-campaign",
  "maxResults": 25
}
```

---

## 3. Python Quickstart

```python
import requests

APIFY_TOKEN = "YOUR_APIFY_TOKEN"

resp = requests.post(
    f"https://api.apify.com/v2/acts/kkhome~shopify-chrome-app-reviews/run-sync-get-dataset-items?token={APIFY_TOKEN}",
    json={
        "targets": ["https://apps.shopify.com/categories/marketing-and-conversion-social-trust-product-reviews/all"],
        "outputMode": "app_profiles_only",
        "maxApps": 15,
        "maxResults": 15,
    },
    timeout=90,
)
for app in resp.json():
    print(app["appName"], app["appRating"], app["builtForShopify"], app["pricingSummary"])
```

---

## Architecture & Public Data Notes

- **Zero Browser Overhead**: Built on async HTTP/2 + SSR JSON-LD and official public JSON endpoints (`256 MB` RAM footprint).
- **Public Endpoints Only**: Accesses strictly public marketplace listings, public ATS job feeds, and public merchant contact disclosures via standard HTTP protocols.
- **Support & Feature Requests**: Open an issue in this repository or on the respective [Noctua Data Apify profile](https://apify.com/kkhome) Actor page.
