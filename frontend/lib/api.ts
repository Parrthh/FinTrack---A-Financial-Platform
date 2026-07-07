"use client";

/**
 * API client. Access token lives in memory only (never localStorage); the
 * refresh token is an httpOnly cookie managed entirely by the backend, so a
 * page reload re-authenticates via POST /api/auth/refresh.
 */

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

let accessToken: string | null = null;

export function setAccessToken(token: string | null) {
  accessToken = token;
}

export function getAccessToken() {
  return accessToken;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (accessToken) headers["Authorization"] = `Bearer ${accessToken}`;

  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
    credentials: "include", // send the refresh cookie
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      // non-JSON error body; keep statusText
    }
    throw new ApiError(res.status, detail);
  }
  return res.json() as Promise<T>;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface User {
  id: string;
  email: string;
  display_name: string;
  email_verified: boolean;
  created_at: string;
}

export interface Asset {
  id: string;
  symbol: string;
  name: string;
  asset_type: "stock" | "etf" | "crypto";
  exchange: string | null;
  sector: string | null;
  currency: string;
  last_price: number | null;
  last_price_at: string | null;
  day_change_pct: number | null;
  market_cap: number | null;
}

export interface AssetList {
  items: Asset[];
  total: number;
  limit: number;
  offset: number;
}

export interface PriceBar {
  ts: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number | null;
  volume: number | null;
}

export interface AssetHistory {
  symbol: string;
  range: string;
  bars: PriceBar[];
}

export interface TickerEntry {
  symbol: string;
  asset_type: string;
  last_price: number | null;
  day_change_pct: number | null;
}

export const api = {
  signup: (email: string, password: string, displayName: string) =>
    request<TokenResponse>("/api/auth/signup", {
      method: "POST",
      body: JSON.stringify({ email, password, display_name: displayName }),
    }),
  login: (email: string, password: string) =>
    request<TokenResponse>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  refresh: () => request<TokenResponse>("/api/auth/refresh", { method: "POST" }),
  logout: () => request<{ message: string }>("/api/auth/logout", { method: "POST" }),
  me: () => request<User>("/api/auth/me"),

  listAssets: (params: {
    q?: string;
    asset_type?: string;
    sort?: string;
    order?: string;
    limit?: number;
    offset?: number;
  }) => {
    const search = new URLSearchParams();
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== "") search.set(k, String(v));
    }
    return request<AssetList>(`/api/assets?${search}`);
  },
  getAsset: (symbol: string) => request<Asset>(`/api/assets/${symbol}`),
  getAssetHistory: (symbol: string, range: string) =>
    request<AssetHistory>(`/api/assets/${symbol}/history?range=${range}`),
  marketTicker: (limit = 10) => request<TickerEntry[]>(`/api/market/ticker?limit=${limit}`),
};
