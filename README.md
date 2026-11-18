# Noctua B2B Data & GTM MCP Server

[![noctua-b2b-mcp MCP server](https://glama.ai/mcp/servers/kkhomej33-netizen/noctua-b2b-mcp/badges/score.svg)](https://glama.ai/mcp/servers/kkhomej33-netizen/noctua-b2b-mcp)

Official Model Context Protocol (MCP) server for **[Noctua Data](https://apify.com/kkhome)** — providing lightweight, browserless B2B intelligence & lead-enrichment tools for **Claude Desktop**, **Cursor**, **Glama**, **Clay**, and **n8n** workflows.

All cloud extraction engines execute on minimal **256 MB** serverless containers via official public feeds and clean SSR parsing, keeping platform compute overhead near **$0.00** with automatic cross-run deduplication.

---

## Exposed MCP Tools

| MCP Tool | Underlying Cloud Engine | Built-In Verified Coverage | All-Inclusive PPE Rate |
| :--- | :--- | :--- | :--- |
| **`search_ats_jobs`** | [kkhome/unified-ats-jobs](https://apify.com/kkhome/unified-ats-jobs) | **4,066+ Employers** (~780K active jobs across `Workday`, `Greenhouse`, `Ashby`, `Lever`, `SmartRecruiters`, `Recruitee`, `Workable`) + bare domain auto-resolution & 60+ B2B tech signals | **$1.50 / 1,000 jobs** |
| **`discover_ecommerce_store_leads`** | [kkhome/store-tech-leads](https://apify.com/kkhome/store-tech-leads) | **16,345+ Live Stores** (`10,148` Shopify + `6,197` custom-domain WooCommerce) + Web Pixels 2.0 sandbox decoding, verified emails, `isShopifyPlus` & monthly SaaS tech spend (`$/mo`) | **$2.00 / 1,000 stores** |
| **`extract_app_reviews_and_churn_leads`** | [kkhome/shopify-chrome-app-reviews](https://apify.com/kkhome/shopify-chrome-app-reviews) | **3-in-1 Marketplaces** (`Shopify App Store`, `Chrome Web Store`, `WordPress.org`) + whole category benchmarks, pain/churn tagging & live Shopify reviewer -> store domain/email resolution | **$1.00 / 1,000 items** |

---

## Quickstart Configuration (`Claude Desktop` / `Cursor`)

Get a free API token from [Apify Console -> Integrations](https://console.apify.com/settings/integrations), then configure either the **Docker / Python stdio server** in this repository or the hosted `@apify/actors-mcp-server`:

### Option A: Local Docker MCP Server

With Docker running, clone the repository and build the image locally.

```sh
git clone https://github.com/kkhomej33-netizen/noctua-b2b-mcp.git
cd noctua-b2b-mcp
docker build -t noctua-b2b-mcp .
```

Then add this configuration to your MCP client.

```json
{
  "mcpServers": {
    "noctua-b2b-mcp": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "APIFY_TOKEN",
        "noctua-b2b-mcp"
      ],
      "env": {
        "APIFY_TOKEN": "<YOUR_APIFY_TOKEN>"
      }
    }
  }
}
```

### Option B: Zero-Install Hosted Bridge (`npx`)
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

---

## Example Agent Prompts

- *"Find US remote Account Executive roles posted in the last 7 days at companies using HubSpot and Snowflake, including their company domains and normalized salaries."*
- *"Discover 20 US skincare Shopify stores spending at least $100/month on apps that use Klaviyo but are missing the TikTok Pixel, with verified contact emails."*
- *"Pull the newest 1-star and 2-star reviews on Klaviyo and Yotpo from the Shopify App Store, tag billing complaints, and resolve the unhappy merchants' live store domains and emails."*

---

## Clay HTTP API Enrichment Recipes

- **ATS Hiring & Tech Signals**: `POST https://api.apify.com/v2/acts/kkhome~unified-ats-jobs/run-sync-get-dataset-items?token=<YOUR_APIFY_TOKEN>`
- **Ecommerce Store Leads**: `POST https://api.apify.com/v2/acts/kkhome~store-tech-leads/run-sync-get-dataset-items?token=<YOUR_APIFY_TOKEN>`
- **App Reviews & Churn Leads**: `POST https://api.apify.com/v2/acts/kkhome~shopify-chrome-app-reviews/run-sync-get-dataset-items?token=<YOUR_APIFY_TOKEN>`

---

## License

Released under the [MIT License](LICENSE).
