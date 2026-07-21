/** Port of api/metrics.py ApiMetrics — in-memory, per-isolate (best
 * effort per spec; values are a sanctioned parity divergence). */

interface RouteMetrics {
  calls: number;
  errors: number;
  total_ms: number;
}

export class ApiMetrics {
  private data = new Map<string, RouteMetrics>();

  record(route: string, ok: boolean, ms: number): void {
    let m = this.data.get(route);
    if (!m) {
      m = { calls: 0, errors: 0, total_ms: 0 };
      this.data.set(route, m);
    }
    m.calls += 1;
    if (!ok) m.errors += 1;
    m.total_ms += ms;
  }

  snapshot(): Record<string, RouteMetrics & { avg_ms: number }> {
    const out: Record<string, RouteMetrics & { avg_ms: number }> = {};
    for (const [route, m] of this.data) {
      out[route] = { ...m, avg_ms: Math.round((m.total_ms / m.calls) * 100) / 100 };
    }
    return out;
  }
}

export const metrics = new ApiMetrics();
