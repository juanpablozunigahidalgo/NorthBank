# AWS / Northmill stack mapping (prototype)

This MVP mirrors Northmill's cloud-only engineering posture (Lambda-heavy, Bedrock for GenAI)
without requiring a full AWS account for the local demo.

| Job / bank capability | This prototype | Production path |
|-----------------------|----------------|-----------------|
| Amazon Bedrock + structured outputs | `bedrock_service.py` (`USE_BEDROCK=true`) | Same code on Lambda; Claude via Bedrock Converse |
| Amazon Quick / Q | Not in MVP UI | Point Q/QuickSight at dossier JSON in S3 for NL query by Partnerships |
| MCP servers | `mcp_server.py` (FastMCP tools) | Host MCP over HTTP/SSE or expose same tools to Bedrock Agents |
| Agentic workflows / tool use | `orchestrator.py` (parallel registry + media workers) | Bedrock Agents or Step Functions fan-out |
| AWS Lambda (500+ at Northmill) | `main.handler` via Mangum | Function URL or API Gateway |
| Deterministic KYB data | Mock Roaring/Allabolag JSON | Roaring.io / Creditsafe / Allabolag APIs |
| Audit / ISO-minded banking | Response `sources` + `unsure_or_unverified` | Raw API payloads + dossier snapshots in S3 |
| TypeScript frontend | Step 3 | Amplify / CloudFront + S3 |
| .NET / C# core banking | Out of scope for take-home | Product Engineers integrate dossier API into merchant onboarding |

## Local commands

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
# GET http://127.0.0.1:8000/api/research?company=Northvolt

# MCP (Cursor / Claude Desktop)
python mcp_server.py
```

## Enable Bedrock

1. Configure AWS credentials with `bedrock:InvokeModel` in `eu-north-1` (or `eu-west-1`).
2. Set in `.env`: `USE_BEDROCK=true`
3. Restart uvicorn. Hard financial numbers still come only from the registry tool — Bedrock only enriches `audit_summary`.
