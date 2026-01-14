"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { RequireAuth } from "@/lib/auth/requireAuth";
import { useAuth } from "@/lib/auth/useAuth";
import { Button } from "@/components/ui/Button";

const nav = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/accounts", label: "Accounts" },
  { href: "/transactions", label: "Transactions" },
];

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();

  return (
    <RequireAuth>
      <div className="min-h-dvh bg-neutral-50">
        <div className="mx-auto flex min-h-dvh w-full max-w-6xl gap-4 px-4 py-4">
          <aside className="w-56 shrink-0">
            <div className="rounded-lg border border-neutral-200 bg-white p-3">
              <div className="mb-2 text-sm font-semibold">Personal Finance</div>
              <nav className="space-y-1">
                {nav.map((item) => {
                  const active = pathname?.startsWith(item.href);
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={[
                        "block rounded-md px-3 py-2 text-sm",
                        active ? "bg-neutral-900 text-white" : "text-neutral-800 hover:bg-neutral-100",
                      ].join(" ")}
                    >
                      {item.label}
                    </Link>
                  );
                })}
              </nav>
              <div className="mt-3 border-t border-neutral-200 pt-3">
                <div className="mb-2 text-xs text-neutral-800">{user?.email ?? "—"}</div>
                <Button
                  variant="secondary"
                  className="w-full"
                  onClick={async () => {
                    await logout();
                    router.replace("/login");
                  }}
                >
                  Logout
                </Button>
              </div>
            </div>
          </aside>

          <main className="min-w-0 flex-1">{children}</main>
        </div>
      </div>
    </RequireAuth>
  );
}


