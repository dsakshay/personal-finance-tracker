"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

export function Providers({ children }: { children: React.ReactNode }) {
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            retry: (failureCount, error: any) => {
              // Avoid retry loops on auth failures and obvious client errors
              const status = typeof error?.status === "number" ? error.status : null;
              if (status && status >= 400 && status < 500) return false;
              return failureCount < 2;
            },
          },
        },
      })
  );

  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}


