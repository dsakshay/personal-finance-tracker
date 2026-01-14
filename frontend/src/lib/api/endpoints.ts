import { apiFetch } from "./client";
import type {
  Account,
  AccountListResponse,
  CreateAccountRequest,
  CreateTransactionRequest,
  CreateTransferRequest,
  LoginRequest,
  MonthlySummary,
  SignupRequest,
  TokenResponse,
  Transaction,
  TransactionListResponse,
  TransferResponse,
  UserRead,
} from "./types";

export const api = {
  auth: {
    signup: (body: SignupRequest) =>
      apiFetch<UserRead>("/api/v1/auth/signup", {
        method: "POST",
        body: JSON.stringify(body),
        skipAuth: true,
      }),
    login: (body: LoginRequest) =>
      apiFetch<TokenResponse>("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify(body),
        skipAuth: true,
      }),
    me: () => apiFetch<UserRead>("/api/v1/auth/me"),
    logout: () => apiFetch<{ message: string }>("/api/v1/auth/logout", { method: "POST" }),
  },

  accounts: {
    list: (params?: { currency?: string }) => {
      const qs = new URLSearchParams();
      if (params?.currency) qs.set("currency", params.currency);
      const suffix = qs.toString() ? `?${qs}` : "";
      return apiFetch<AccountListResponse>(`/api/v1/accounts${suffix}`);
    },
    create: (body: CreateAccountRequest) =>
      apiFetch<Account>("/api/v1/accounts", {
        method: "POST",
        body: JSON.stringify(body),
      }),
  },

  transactions: {
    list: (params?: {
      account_id?: string;
      transaction_type?: string;
      tag?: string;
      limit?: number;
      offset?: number;
    }) => {
      const qs = new URLSearchParams();
      if (params?.account_id) qs.set("account_id", params.account_id);
      if (params?.transaction_type) qs.set("transaction_type", params.transaction_type);
      if (params?.tag) qs.set("tag", params.tag);
      if (typeof params?.limit === "number") qs.set("limit", String(params.limit));
      if (typeof params?.offset === "number") qs.set("offset", String(params.offset));
      const suffix = qs.toString() ? `?${qs}` : "";
      return apiFetch<TransactionListResponse>(`/api/v1/transactions${suffix}`);
    },
    get: (id: string) => apiFetch<Transaction>(`/api/v1/transactions/${id}`),
    create: (body: CreateTransactionRequest) =>
      apiFetch<Transaction>("/api/v1/transactions", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    transfer: (body: CreateTransferRequest) =>
      apiFetch<TransferResponse>("/api/v1/transactions/transfer", {
        method: "POST",
        body: JSON.stringify({
          transaction_type: "transfer",
          tag: "transfer",
          ...body,
        }),
      }),
  },

  summary: {
    monthly: (params: { year: number; month: number; currency?: string }) => {
      const qs = new URLSearchParams({
        year: String(params.year),
        month: String(params.month),
      });
      if (params.currency) qs.set("currency", params.currency);
      return apiFetch<MonthlySummary>(`/api/v1/summary/monthly?${qs.toString()}`);
    },
  },
} as const;


