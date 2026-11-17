#!/usr/bin/env python3
"""Noctua Data 官方轻量 MCP Server 网关：零外部依赖实现标准 MCP JSON-RPC 2.0 协议并桥接 Apify 云端 B2B 数据引擎。"""

from __future__ import annotations

import json
import os
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

SERVER_NAME = "noctua-b2b-mcp"
SERVER_VERSION = "1.0.0"
SUPPORTED_PROTOCOLS = ("2025-03-26", "2024-11-05", "2024-10-07")

ACTOR_ENDPOINTS = {
    "search_ats_jobs": "kkhome~unified-ats-jobs",
    "discover_ecommerce_store_leads": "kkhome~store-tech-leads",
    "extract_app_reviews_and_churn_leads": "kkhome~shopify-chrome-app-reviews",
}

# 定义暴露给 MCP 客户端与自省扫描器的三大工具及完整注解
TOOLS_SPEC: list[dict[str, Any]] = [
    {
        "name": "search_ats_jobs",
        "description": (
            "Query 780,000+ live verified job postings across 4,066+ employers on 7 ATS platforms "
            "(Workday, Greenhouse, Ashby, Lever, SmartRecruiters, Recruitee, Workable) or resolve "
            "bare company domains (e.g. 'airtable.com') into active roles, normalized salaries, "
            "and 60+ B2B technographic buying signals."
        ),
        "annotations": {
            "title": "Search Live ATS Jobs & B2B Tech Signals",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
        "inputSchema": {
            "type": "object",
            "properties": {
                "targets": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of bare company domains (e.g. 'mistral.ai'), career URLs, or ATS board URLs. Leave empty to search across the built-in 4,066-company index.",
                },
                "searchQuery": {
                    "type": "string",
                    "description": "Job title, skill, or tool keyword filter (e.g. 'Data Engineer', 'Account Executive', 'Snowflake').",
                },
                "locationQuery": {
                    "type": "string",
                    "description": "Country, state, or city filter (e.g. 'United States', 'Remote', 'London').",
                },
                "remoteOnly": {
                    "type": "boolean",
                    "description": "Return only remote-eligible positions.",
                    "default": False,
                },
                "postedWithinDays": {
                    "type": "integer",
                    "description": "Incremental recency filter in days (e.g. 7 or 30). 0 means all active roles.",
                    "default": 0,
                },
                "maxResults": {
                    "type": "integer",
                    "description": "Maximum number of job records to return (1-500).",
                    "default": 20,
                },
            },
        },
    },
    {
        "name": "discover_ecommerce_store_leads",
        "description": (
            "Discover verified B2B ecommerce leads across 16,345+ indexed storefronts "
            "(10,148 Shopify + 6,197 custom-domain WooCommerce) plus live web niche search, "
            "or enrich a list of domains with contact emails, phones, postal addresses, "
            "65+ installed apps, Shopify OS 2.0 Web Pixels, Shopify Plus status, and monthly SaaS spend."
        ),
        "annotations": {
            "title": "Discover & Enrich Shopify / WooCommerce Store Leads",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
        "inputSchema": {
            "type": "object",
            "properties": {
                "domains": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of store domains to enrich directly. Leave empty to discover stores by niche/tech criteria.",
                },
                "searchQuery": {
                    "type": "string",
                    "description": "Niche or product keyword (e.g. 'coffee', 'skincare', 'pickleball').",
                },
                "platformFilter": {
                    "type": "string",
                    "enum": ["any", "shopify", "woocommerce"],
                    "description": "Filter by ecommerce platform.",
                    "default": "any",
                },
                "countryFilter": {
                    "type": "string",
                    "description": "Two-letter ISO country code (e.g. 'US', 'GB', 'AU', 'CA', 'DE').",
                },
                "requiredTech": {
                    "type": "string",
                    "description": "App or pixel that must be installed (e.g. 'Klaviyo', 'Meta Pixel').",
                },
                "missingTech": {
                    "type": "string",
                    "description": "App or pixel that must NOT be installed (ideal for agency pitch lists, e.g. 'TikTok Pixel').",
                },
                "onlyShopifyPlus": {
                    "type": "boolean",
                    "description": "Return only verified Shopify Plus storefronts.",
                    "default": False,
                },
                "minTechSpendUsd": {
                    "type": "integer",
                    "description": "Minimum estimated monthly software spend in USD (e.g. 100).",
                    "default": 0,
                },
                "onlyWithEmail": {
                    "type": "boolean",
                    "description": "Return only stores with at least one verified contact email.",
                    "default": True,
                },
                "maxResults": {
                    "type": "integer",
                    "description": "Maximum number of store leads to return (1-200).",
                    "default": 15,
                },
            },
        },
    },
    {
        "name": "extract_app_reviews_and_churn_leads",
        "description": (
            "Extract reviews, category/partner benchmarks, pricing tiers, Built for Shopify badges, "
            "Chrome manifest permissions, and deterministic B2B pain/churn signals from Shopify App Store, "
            "Chrome Web Store, and WordPress.org Plugins — and resolve unhappy Shopify app reviewers "
            "into live merchant store domains and contact emails."
        ),
        "annotations": {
            "title": "Extract App Reviews, Category Benchmarks & Churn Leads",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
        "inputSchema": {
            "type": "object",
            "properties": {
                "targets": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "App/Extension URLs, handles, 32-char Chrome IDs, or whole Shopify Category / Partner URLs.",
                },
                "searchQuery": {
                    "type": "string",
                    "description": "Keyword to auto-discover apps when targets is empty (e.g. 'email marketing', 'loyalty').",
                },
                "platformFilter": {
                    "type": "string",
                    "enum": ["all", "shopify", "chrome", "wordpress"],
                    "default": "all",
                },
                "outputMode": {
                    "type": "string",
                    "enum": ["reviews_and_leads", "app_profiles_only"],
                    "description": "Choose 'reviews_and_leads' for review pain/churn analysis or 'app_profiles_only' for category benchmarking.",
                    "default": "reviews_and_leads",
                },
                "minRating": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 5,
                    "default": 1,
                },
                "maxRating": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 5,
                    "default": 2,
                },
                "reviewLanguage": {
                    "type": "string",
                    "enum": ["all", "en", "de", "es", "fr", "pt", "it", "nl", "ja", "zh"],
                    "default": "all",
                },
                "enrichMerchantLeads": {
                    "type": "boolean",
                    "description": "Resolve Shopify reviewer store names into live domains and verified emails.",
                    "default": True,
                },
                "onlyWithMerchantEmail": {
                    "type": "boolean",
                    "description": "Deliver only Shopify review leads with a verified merchant contact email.",
                    "default": False,
                },
                "maxResults": {
                    "type": "integer",
                    "description": "Maximum items to return (1-200).",
                    "default": 20,
                },
            },
        },
    },
]

# 内置高价值 GTM 工作流提示词模板
PROMPTS_SPEC: list[dict[str, Any]] = [
    {
        "name": "competitor-churn-displacement",
        "description": "Find unhappy merchants leaving 1-2 star reviews on a competitor Shopify app and resolve their store emails.",
        "arguments": [
            {
                "name": "competitor_app",
                "description": "Shopify App handle or URL (e.g. 'klaviyo-email-marketing' or 'yotpo-social-reviews')",
                "required": True,
            }
        ],
    },
    {
        "name": "agency-missing-pixel-pitch",
        "description": "Build a targeted list of high-spend ecommerce stores in a niche that use Klaviyo but lack a specific ad pixel.",
        "arguments": [
            {"name": "niche", "description": "Store niche keyword (e.g. 'skincare', 'coffee')", "required": True},
            {"name": "missing_tech", "description": "Missing pixel or app (e.g. 'TikTok Pixel')", "required": False},
        ],
    },
]

RESOURCES_SPEC: list[dict[str, Any]] = [
    {
        "uri": "noctua://catalog/overview",
        "name": "Noctua Data B2B Actor Suite Overview",
        "description": "Capabilities, built-in index coverage, and pricing tiers for Noctua Data MCP tools.",
        "mimeType": "application/json",
    }
]


def _call_apify_actor(actor_slug: str, payload: dict[str, Any]) -> tuple[bool, str]:
    """调用 Apify 云端同步运行接口并返回 JSON 数据集文本。"""
    token = (os.environ.get("APIFY_TOKEN") or os.environ.get("APIFY_API_TOKEN") or "").strip()
    if not token:
        msg = {
            "error": "MISSING_APIFY_TOKEN",
            "message": (
                "Set the APIFY_TOKEN environment variable in your MCP client config to execute live queries. "
                "Get a free API token at https://console.apify.com/settings/integrations "
                "or view the actor suite at https://apify.com/kkhome"
            ),
            "actor": actor_slug.replace("~", "/"),
        }
        return True, json.dumps(msg, indent=2)

    qs = urllib.parse.urlencode({"token": token, "memory": 256, "timeout": 120})
    url = f"https://api.apify.com/v2/acts/{actor_slug}/run-sync-get-dataset-items?{qs}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": f"{SERVER_NAME}/{SERVER_VERSION}",
        },
    )
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=130, context=ctx) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return False, body
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")[:1000]
        return True, json.dumps({"error": f"HTTP_{exc.code}", "details": err_body}, indent=2)
    except Exception as exc:
        return True, json.dumps({"error": "REQUEST_FAILED", "details": str(exc)}, indent=2)


def handle_rpc_request(msg: dict[str, Any]) -> dict[str, Any] | None:
    """处理单条 MCP JSON-RPC 2.0 请求消息（通知类消息返回 None）。"""
    method = msg.get("method", "")
    req_id = msg.get("id")
    params = msg.get("params") or {}

    # 通知消息无需返回响应体
    if req_id is None:
        return None

    if method == "initialize":
        client_proto = str(params.get("protocolVersion") or "2024-11-05")
        negotiated = client_proto if client_proto in SUPPORTED_PROTOCOLS else SUPPORTED_PROTOCOLS[0]
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": negotiated,
                "capabilities": {
                    "tools": {"listChanged": False},
                    "prompts": {"listChanged": False},
                    "resources": {"subscribe": False, "listChanged": False},
                },
                "serverInfo": {
                    "name": SERVER_NAME,
                    "version": SERVER_VERSION,
                },
            },
        }

    if method == "ping":
        return {"jsonrpc": "2.0", "id": req_id, "result": {}}

    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS_SPEC}}

    if method == "prompts/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"prompts": PROMPTS_SPEC}}

    if method == "prompts/get":
        p_name = params.get("name")
        p_args = params.get("arguments") or {}
        if p_name == "competitor-churn-displacement":
            comp = p_args.get("competitor_app", "klaviyo-email-marketing")
            text = (
                f"Use extract_app_reviews_and_churn_leads on target '{comp}' with minRating=1, maxRating=2, "
                f"enrichMerchantLeads=true, and summarize top pain points alongside verified merchant domains and emails."
            )
        elif p_name == "agency-missing-pixel-pitch":
            niche = p_args.get("niche", "skincare")
            missing = p_args.get("missing_tech", "TikTok Pixel")
            text = (
                f"Use discover_ecommerce_store_leads with searchQuery='{niche}', requiredTech='Klaviyo', "
                f"missingTech='{missing}', minTechSpendUsd=80, and onlyWithEmail=true."
            )
        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32602, "message": f"Unknown prompt: {p_name}"},
            }
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "description": f"Generated workflow prompt for {p_name}",
                "messages": [{"role": "user", "content": {"type": "text", "text": text}}],
            },
        }

    if method == "resources/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"resources": RESOURCES_SPEC}}

    if method == "resources/read":
        uri = params.get("uri", "")
        catalog = {
            "provider": "Noctua Data",
            "profileUrl": "https://apify.com/kkhome",
            "tools": [
                {
                    "tool": "search_ats_jobs",
                    "actor": "kkhome/unified-ats-jobs",
                    "coverage": "4,066+ verified employers, 780K+ active jobs across 7 ATS",
                    "pricingUsdPer1K": 1.50,
                },
                {
                    "tool": "discover_ecommerce_store_leads",
                    "actor": "kkhome/store-tech-leads",
                    "coverage": "16,345+ verified Shopify & WooCommerce stores + live web search",
                    "pricingUsdPer1K": 2.00,
                },
                {
                    "tool": "extract_app_reviews_and_churn_leads",
                    "actor": "kkhome/shopify-chrome-app-reviews",
                    "coverage": "Shopify App Store, Chrome Web Store & WordPress Plugins + merchant lead resolution",
                    "pricingUsdPer1K": 1.00,
                },
            ],
        }
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "contents": [
                    {
                        "uri": uri or "noctua://catalog/overview",
                        "mimeType": "application/json",
                        "text": json.dumps(catalog, indent=2),
                    }
                ]
            },
        }

    if method == "tools/call":
        t_name = str(params.get("name") or "")
        t_args = params.get("arguments") or {}
        actor_slug = ACTOR_ENDPOINTS.get(t_name)
        if not actor_slug:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32602, "message": f"Unknown tool: {t_name}"},
            }
        is_err, out_text = _call_apify_actor(actor_slug, t_args if isinstance(t_args, dict) else {})
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [{"type": "text", "text": out_text}],
                "isError": is_err,
            },
        }

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"},
    }


def main() -> None:
    """主事件循环：自动兼容标准逐行 JSON (NDJSON) 与 Content-Length 帧格式。"""
    stdin = sys.stdin.buffer
    stdout = sys.stdout.buffer

    while True:
        line = stdin.readline()
        if not line:
            break
        stripped = line.strip()
        if not stripped:
            continue

        use_content_length = False
        if stripped.lower().startswith(b"content-length:"):
            use_content_length = True
            length = int(stripped.split(b":", 1)[1].strip())
            # 消费头部结束空行
            while True:
                hdr = stdin.readline()
                if not hdr or hdr in (b"\r\n", b"\n"):
                    break
            raw_payload = stdin.read(length)
        else:
            raw_payload = stripped

        try:
            req_obj = json.loads(raw_payload.decode("utf-8"))
        except Exception:
            continue

        resp_obj = handle_rpc_request(req_obj)
        if resp_obj is not None:
            encoded = json.dumps(resp_obj, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
            if use_content_length:
                header = f"Content-Length: {len(encoded)}\r\n\r\n".encode("ascii")
                stdout.write(header + encoded)
            else:
                stdout.write(encoded + b"\n")
            stdout.flush()


if __name__ == "__main__":
    main()
