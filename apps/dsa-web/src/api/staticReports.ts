/**
 * Static JSON data fetch layer for the read-only Reports page.
 * Fetches pre-generated JSON files from /data/ (co-located in the Cloudflare Pages build).
 * No backend API required.
 */

export interface ReportDateEntry {
  date: string;
  count: number;
}

export interface ReportStockEntry {
  code: string;
  name: string;
  count: number;
}

export interface ReportsIndex {
  dates: ReportDateEntry[];
  stocks: ReportStockEntry[];
}

/** Summary item within a date file */
export interface ReportSummaryItem {
  id: number;
  queryId: string;
  stockCode: string;
  stockName: string;
  reportType?: string;
  sentimentScore?: number;
  operationAdvice?: string;
  trendPrediction?: string;
  createdAt?: string;
}

/** Full report detail (matches AnalysisReport structure) */
export interface StaticReportDetail {
  meta: {
    id: number;
    queryId: string;
    stockCode: string;
    stockName: string;
    reportType?: string;
    createdAt?: string;
    modelUsed?: string;
  };
  summary: {
    analysisSummary?: string;
    operationAdvice?: string;
    trendPrediction?: string;
    sentimentScore?: number;
    sentimentLabel?: string;
  };
  strategy?: {
    idealBuy?: string;
    secondaryBuy?: string;
    stopLoss?: string;
    takeProfit?: string;
  };
  details?: {
    newsContent?: string;
    rawResult?: Record<string, unknown>;
  };
}

async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Failed to fetch ${url}: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const staticReportsApi = {
  /** Fetch the top-level index: all dates and stocks */
  getIndex: (): Promise<ReportsIndex> =>
    fetchJson<ReportsIndex>('/data/index.json'),

  /** Fetch all report summaries for a given date (YYYY-MM-DD) */
  getByDate: (date: string): Promise<ReportSummaryItem[]> =>
    fetchJson<ReportSummaryItem[]>(`/data/dates/${date}.json`),

  /** Fetch the full report detail for a given record ID */
  getReport: (id: number): Promise<StaticReportDetail> =>
    fetchJson<StaticReportDetail>(`/data/reports/${id}.json`),
};
