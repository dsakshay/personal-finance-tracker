"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { getAuthToken } from "./token";

export function RequireAuth({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    const token = getAuthToken();
    if (!token) {
      const next = pathname ? `?next=${encodeURIComponent(pathname)}` : "";
      router.replace(`/login${next}`);
    }
  }, [router, pathname]);

  return <>{children}</>;
}


