export type ApiErrorDetails =
  | Record<string, unknown>
  | {
      errors?: Array<{
        field?: string;
        message?: string;
        type?: string;
      }>;
    };

export class ApiError extends Error {
  status: number;
  error: string;
  details?: ApiErrorDetails;
  raw?: unknown;

  constructor(args: { status: number; error: string; message: string; details?: ApiErrorDetails; raw?: unknown }) {
    super(args.message);
    this.name = "ApiError";
    this.status = args.status;
    this.error = args.error;
    this.details = args.details;
    this.raw = args.raw;
  }
}

export function isApiError(err: unknown): err is ApiError {
  return err instanceof ApiError;
}


