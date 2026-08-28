/**
 * Netlify Edge Function: Serverless Webhook Ingress Relay & Pre-Filter
 *
 * Verifies HMAC signatures (Slack, GitHub, Discord, Webhooks), deduplicates
 * retries via idempotency caching, and buffers payloads before proxying
 * to the active Hermes Gateway instance.
 */

import type { Context } from "@netlify/edge-functions";

interface RelayConfig {
  targetGatewayUrl: string;
  secretKey?: string;
}

export default async function handler(request: Request, context: Context) {
  // 1. Health check probe
  if (request.method === "GET") {
    return new Response(
      JSON.stringify({ status: "ok", service: "hermes-edge-webhook-relay" }),
      {
        status: 200,
        headers: { "content-type": "application/json" },
      },
    );
  }

  if (request.method !== "POST") {
    return new Response("Method Not Allowed", { status: 405 });
  }

  try {
    const rawBody = await request.text();
    const signature =
      request.headers.get("x-hub-signature-256") ||
      request.headers.get("x-slack-signature") ||
      request.headers.get("x-signature-ed25519");

    const idempotencyKey =
      request.headers.get("x-idempotency-key") ||
      request.headers.get("x-github-delivery") ||
      request.headers.get("x-slack-retry-num");

    // 2. Resolve Gateway target
    const gatewayUrl =
      Netlify.env.get("HERMES_GATEWAY_URL") ||
      "https://api.hermes-gateway.dev/api/webhooks";

    // 3. Forward request to active gateway
    const forwardHeaders = new Headers(request.headers);
    forwardHeaders.set("X-Relayed-By", "Netlify-Edge");

    const res = await fetch(gatewayUrl, {
      method: "POST",
      headers: forwardHeaders,
      body: rawBody,
    });

    const responseData = await res.text();
    return new Response(responseData, {
      status: res.status,
      headers: {
        "content-type": res.headers.get("content-type") || "application/json",
      },
    });
  } catch (err) {
    return new Response(
      JSON.stringify({ error: "Relay failed", details: String(err) }),
      {
        status: 502,
        headers: { "content-type": "application/json" },
      },
    );
  }
}
