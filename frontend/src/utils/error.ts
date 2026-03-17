/**
 * Error handling utilities
 */

/**
 * Extracts a user-friendly error message from various error types.
 * Handles Axios error responses, Error objects, and unknown types.
 */
export function getErrorMessage(error: unknown): string {
  if (error && typeof error === 'object' && 'response' in error) {
    // Axios Error Response
    const res = (error as { response?: { data?: { error?: string } } }).response;
    if (res?.data?.error) return res.data.error;
  }
  if (error instanceof Error) return error.message;
  return String(error);
}
