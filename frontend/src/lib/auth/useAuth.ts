"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/endpoints";
import { queryKeys } from "../api/queryKeys";
import { clearAuthToken, getAuthToken } from "./token";
import { isApiError } from "../api/errors";

export function useAuth() {
  const qc = useQueryClient();

  const token = getAuthToken();
  const meQuery = useQuery({
    queryKey: queryKeys.auth.me(),
    queryFn: () => api.auth.me(),
    enabled: Boolean(token),
    retry: false,
  });

  const logout = async () => {
    // best-effort
    try {
      if (getAuthToken()) await api.auth.logout();
    } catch {
      // ignore
    }
    clearAuthToken();
    qc.clear();
  };

  // If /me ever returns 401, clear token to force relogin
  if (meQuery.error && isApiError(meQuery.error) && meQuery.error.status === 401) {
    clearAuthToken();
  }

  return {
    token,
    user: meQuery.data ?? null,
    isLoading: meQuery.isLoading,
    isAuthed: Boolean(token) && Boolean(meQuery.data),
    logout,
  };
}


