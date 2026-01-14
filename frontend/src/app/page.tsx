import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-dvh bg-neutral-50">
      <div className="mx-auto max-w-3xl px-4 py-16">
        <div className="rounded-lg border border-neutral-200 bg-white p-6 shadow-sm">
          <div className="text-xl font-semibold">Personal Finance Tracker</div>
          <div className="mt-1 text-sm text-neutral-600">
            MVP frontend for the FastAPI backend.
          </div>
          <div className="mt-6 flex gap-3">
            <Link
              className="rounded-md bg-neutral-900 px-4 py-2 text-sm font-medium text-white hover:bg-neutral-800"
              href="/login"
            >
              Login
            </Link>
            <Link
              className="rounded-md bg-neutral-100 px-4 py-2 text-sm font-medium text-neutral-900 hover:bg-neutral-200"
              href="/signup"
            >
              Sign up
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
