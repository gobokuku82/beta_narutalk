/**
 * BackendError — REST 응답 4xx/5xx 시 throw.
 *
 * spec: 63 §2.4
 */
export class BackendError extends Error {
  constructor(
    public status: number,
    public body: { code?: string; message?: string; detail?: unknown } = {},
  ) {
    super(body.message ?? `HTTP ${status}`);
    this.name = 'BackendError';
  }
}
