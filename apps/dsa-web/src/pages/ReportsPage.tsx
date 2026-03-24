import React, { useCallback, useEffect, useState } from 'react';
import { ChevronLeft } from 'lucide-react';
import { ReportSummary } from '../components/report/ReportSummary';
import {
  staticReportsApi,
  type ReportsIndex,
  type ReportSummaryItem,
  type StaticReportDetail,
} from '../api/staticReports';
import { getSentimentColor } from '../types/analysis';
import type { AnalysisReport } from '../types/analysis';
import { cn } from '../utils/cn';

// ---- helpers ----

function toAnalysisReport(detail: StaticReportDetail): AnalysisReport {
  return {
    meta: {
      id: detail.meta.id,
      queryId: detail.meta.queryId,
      stockCode: detail.meta.stockCode,
      stockName: detail.meta.stockName ?? detail.meta.stockCode,
      reportType: (detail.meta.reportType as AnalysisReport['meta']['reportType']) ?? 'detailed',
      createdAt: detail.meta.createdAt ?? '',
      modelUsed: detail.meta.modelUsed,
    },
    summary: {
      analysisSummary: detail.summary.analysisSummary ?? '',
      operationAdvice: detail.summary.operationAdvice ?? '',
      trendPrediction: detail.summary.trendPrediction ?? '',
      sentimentScore: detail.summary.sentimentScore ?? 50,
      sentimentLabel: detail.summary.sentimentLabel as AnalysisReport['summary']['sentimentLabel'],
    },
    strategy: detail.strategy,
    details: detail.details
      ? {
          newsContent: detail.details.newsContent,
          rawResult: detail.details.rawResult,
        }
      : undefined,
  };
}

// ---- sub-components ----

interface ReportCardProps {
  item: ReportSummaryItem;
  isSelected: boolean;
  onClick: () => void;
}

const ReportCard: React.FC<ReportCardProps> = ({ item, isSelected, onClick }) => {
  const score = item.sentimentScore ?? 50;
  const color = getSentimentColor(score);

  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'w-full rounded-2xl border p-4 text-left transition-all',
        isSelected
          ? 'border-[var(--nav-active-border)] bg-[var(--nav-active-bg)] shadow-md'
          : 'border-border/50 bg-surface hover:border-border hover:bg-hover',
      )}
    >
      <div className="mb-2 flex items-center justify-between gap-2">
        <span className="truncate text-sm font-semibold text-foreground">
          {item.stockName}
        </span>
        <span
          className="shrink-0 rounded-full px-2 py-0.5 text-xs font-medium text-white"
          style={{ backgroundColor: color }}
        >
          {score}
        </span>
      </div>
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs text-secondary-text">{item.stockCode}</span>
        {item.operationAdvice && (
          <span className="text-xs text-secondary-text">{item.operationAdvice}</span>
        )}
      </div>
      {item.trendPrediction && (
        <p className="mt-1 truncate text-xs text-secondary-text">{item.trendPrediction}</p>
      )}
    </button>
  );
};

// ---- main page ----

type TabKey = 'date' | 'stock';

const ReportsPage: React.FC = () => {
  const [index, setIndex] = useState<ReportsIndex | null>(null);
  const [indexError, setIndexError] = useState<string | null>(null);

  const [activeTab, setActiveTab] = useState<TabKey>('date');

  // date tab
  const [selectedDate, setSelectedDate] = useState<string>('');
  const [dateItems, setDateItems] = useState<ReportSummaryItem[]>([]);
  const [dateLoading, setDateLoading] = useState(false);

  // stock tab
  const [selectedStock, setSelectedStock] = useState<string>('');
  const [stockItems, setStockItems] = useState<ReportSummaryItem[]>([]);
  const [stockLoading, setStockLoading] = useState(false);

  // detail panel
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [detail, setDetail] = useState<StaticReportDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Load index on mount
  useEffect(() => {
    staticReportsApi
      .getIndex()
      .then((idx) => {
        setIndex(idx);
        if (idx.dates.length > 0) {
          setSelectedDate(idx.dates[0].date);
        }
      })
      .catch((e: Error) => setIndexError(e.message));
  }, []);

  // Load date items when selectedDate changes
  useEffect(() => {
    if (!selectedDate) return;
    setDateLoading(true);
    setSelectedId(null);
    setDetail(null);
    staticReportsApi
      .getByDate(selectedDate)
      .then(setDateItems)
      .catch(() => setDateItems([]))
      .finally(() => setDateLoading(false));
  }, [selectedDate]);

  // Load stock items when selectedStock changes
  const loadStockItems = useCallback(async (code: string) => {
    if (!code || !index) return;
    setStockLoading(true);
    setSelectedId(null);
    setDetail(null);
    // Collect all IDs for this stock across all dates
    const all: ReportSummaryItem[] = [];
    for (const d of index.dates) {
      try {
        const items = await staticReportsApi.getByDate(d.date);
        all.push(...items.filter((i) => i.stockCode === code));
      } catch {
        // skip failed dates
      }
    }
    all.sort((a, b) => (b.createdAt ?? '').localeCompare(a.createdAt ?? ''));
    setStockItems(all);
    setStockLoading(false);
  }, [index]);

  useEffect(() => {
    if (selectedStock) void loadStockItems(selectedStock);
  }, [selectedStock, loadStockItems]);

  // Load detail when an item is selected
  const handleSelectItem = useCallback((id: number) => {
    if (id === selectedId) {
      setSelectedId(null);
      setDetail(null);
      return;
    }
    setSelectedId(id);
    setDetailLoading(true);
    setDetail(null);
    staticReportsApi
      .getReport(id)
      .then(setDetail)
      .catch(() => setDetail(null))
      .finally(() => setDetailLoading(false));
  }, [selectedId]);

  const currentItems = activeTab === 'date' ? dateItems : stockItems;
  const isLoading = activeTab === 'date' ? dateLoading : stockLoading;

  // ---- render ----

  if (indexError) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-2 text-secondary-text">
        <p className="text-sm">无法加载报告数据</p>
        <p className="text-xs opacity-60">{indexError}</p>
        <p className="mt-2 text-xs opacity-50">
          请确认 GitHub Action 已成功运行并部署到 Cloudflare Pages
        </p>
      </div>
    );
  }

  if (!index) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-cyan/20 border-t-cyan" />
      </div>
    );
  }

  if (index.dates.length === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-2 text-secondary-text">
        <p className="text-sm">暂无报告数据</p>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col overflow-hidden">
      {/* Header */}
      <div className="shrink-0 border-b border-border/50 px-6 py-4">
        <h1 className="text-lg font-semibold text-foreground">报告浏览</h1>
        <p className="mt-0.5 text-xs text-secondary-text">
          共 {index.dates.length} 个交易日，{index.stocks.length} 只股票
        </p>
      </div>

      <div className="flex min-h-0 flex-1">
        {/* Left panel: filters + list */}
        <div
          className={cn(
            'flex shrink-0 flex-col border-r border-border/50',
            detail ? 'w-72' : 'flex-1',
          )}
        >
          {/* Tabs */}
          <div className="flex shrink-0 gap-1 border-b border-border/50 px-4 pt-3">
            {(['date', 'stock'] as TabKey[]).map((tab) => (
              <button
                key={tab}
                type="button"
                onClick={() => setActiveTab(tab)}
                className={cn(
                  'rounded-t px-3 py-1.5 text-sm transition-colors',
                  activeTab === tab
                    ? 'border-b-2 border-[var(--nav-indicator-bg)] font-medium text-foreground'
                    : 'text-secondary-text hover:text-foreground',
                )}
              >
                {tab === 'date' ? '按日期' : '按股票'}
              </button>
            ))}
          </div>

          {/* Filter selector */}
          <div className="shrink-0 px-4 py-3">
            {activeTab === 'date' ? (
              <select
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="w-full rounded-lg border border-border/70 bg-surface px-3 py-2 text-sm text-foreground outline-none focus:border-[var(--nav-active-border)]"
              >
                {index.dates.map((d) => (
                  <option key={d.date} value={d.date}>
                    {d.date} ({d.count} 只)
                  </option>
                ))}
              </select>
            ) : (
              <select
                value={selectedStock}
                onChange={(e) => setSelectedStock(e.target.value)}
                className="w-full rounded-lg border border-border/70 bg-surface px-3 py-2 text-sm text-foreground outline-none focus:border-[var(--nav-active-border)]"
              >
                <option value="">-- 选择股票 --</option>
                {index.stocks.map((s) => (
                  <option key={s.code} value={s.code}>
                    {s.name} ({s.code}) · {s.count} 条
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* Report card list */}
          <div className="min-h-0 flex-1 overflow-y-auto px-4 pb-4">
            {isLoading ? (
              <div className="flex justify-center pt-8">
                <div className="h-5 w-5 animate-spin rounded-full border-2 border-cyan/20 border-t-cyan" />
              </div>
            ) : currentItems.length === 0 ? (
              <p className="pt-8 text-center text-xs text-secondary-text">暂无数据</p>
            ) : (
              <div className="space-y-2">
                {currentItems.map((item) => (
                  <ReportCard
                    key={item.id}
                    item={item}
                    isSelected={item.id === selectedId}
                    onClick={() => handleSelectItem(item.id)}
                  />
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right panel: report detail */}
        {detail || detailLoading ? (
          <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
            {/* Detail header */}
            <div className="flex shrink-0 items-center gap-2 border-b border-border/50 px-6 py-3">
              <button
                type="button"
                onClick={() => { setSelectedId(null); setDetail(null); }}
                className="rounded-lg p-1 text-secondary-text hover:bg-hover hover:text-foreground"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              {detail && (
                <span className="text-sm font-medium text-foreground">
                  {detail.meta.stockName} ({detail.meta.stockCode})
                </span>
              )}
            </div>

            <div className="min-h-0 flex-1 overflow-y-auto px-6 py-4">
              {detailLoading ? (
                <div className="flex justify-center pt-16">
                  <div className="h-6 w-6 animate-spin rounded-full border-2 border-cyan/20 border-t-cyan" />
                </div>
              ) : detail ? (
                <ReportSummary data={toAnalysisReport(detail)} isHistory />
              ) : null}
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
};

export default ReportsPage;
