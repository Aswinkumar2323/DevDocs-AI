"use client";

import Link from "next/link";
import {
  Database,
  FileText,
  Layers,
  Binary,
  Clock,
  Server,
  Plus,
  Search,
  MessageSquare,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { buttonVariants } from "@/components/ui/button";
import { PageHeader } from "@/components/shared/page-header";
import { StatusBadge } from "@/components/shared/status-badge";
import { SkeletonCards } from "@/components/shared/skeleton-loader";
import { ErrorState } from "@/components/shared/error-state";
import { useSources } from "@/hooks/use-sources";
import { usePages } from "@/hooks/use-pages";

import { useQueries } from "@tanstack/react-query";
import { indexingService } from "@/services/indexing";

const statIcons = [Database, FileText, Layers, Binary, Clock, Server];

export default function DashboardPage() {
  const { data: sources, isLoading: sourcesLoading, error: sourcesError, refetch: refetchSources } = useSources();
  const { data: pages, isLoading: pagesLoading, error: pagesError, refetch: refetchPages } = usePages();

  const indexingQueries = useQueries({
    queries: (sources || []).map((source) => ({
      queryKey: ["indexing-status", source.id],
      queryFn: () => indexingService.getStatus(source.id),
      staleTime: 30000,
    })),
  });

  const isIndexingLoading = indexingQueries.some((q) => q.isLoading);
  const isLoading = sourcesLoading || pagesLoading || (sources && sources.length > 0 && isIndexingLoading);
  const hasError = sourcesError || pagesError;

  const totalSources = sources?.length ?? 0;
  const totalPages = pages?.length ?? 0;
  
  const totalChunks = indexingQueries.reduce((sum, q) => {
    return sum + (q.data?.total_chunks ?? 0);
  }, 0);

  const hasIndexedSource = sources?.some((s) => s.status === "indexed" || s.status === "partially_indexed" || s.status === "processed");
  const vectorDbStatus = hasError ? "offline" : hasIndexedSource || totalChunks > 0 ? "healthy" : "pending";

  // Find the most recent updated page as a proxy for last crawl time
  const lastCrawl = pages && pages.length > 0
    ? pages.reduce((latest, p) => {
        const pDate = new Date(p.updated_at).getTime();
        const lDate = new Date(latest.updated_at).getTime();
        return pDate > lDate ? p : latest;
      })
    : null;

  const stats = [
    {
      title: "Documentation Sources",
      value: totalSources,
      icon: Database,
    },
    {
      title: "Pages Indexed",
      value: totalPages,
      icon: FileText,
    },
    {
      title: "Chunks Generated",
      value: totalChunks,
      icon: Layers,
    },
    {
      title: "Embeddings Generated",
      value: totalChunks,
      icon: Binary,
    },
    {
      title: "Last Crawl Time",
      value: lastCrawl
        ? new Date(lastCrawl.updated_at).toLocaleString()
        : "Never",
      icon: Clock,
    },
    {
      title: "Vector DB Status",
      value: vectorDbStatus,
      icon: Server,
      isBadge: true,
    },
  ];

  // Build recent crawl jobs from sources
  const recentJobs = sources
    ?.filter((s) => s.status !== "pending")
    .slice(0, 5)
    .map((s) => ({
      id: s.id,
      name: s.name,
      status: s.status,
      url: s.base_url,
    }));

  if (hasError) {
    return (
      <>
        <PageHeader
          title="Dashboard"
          description="Overview of your RAG pipeline"
        />
        <ErrorState
          message="Could not connect to the backend. Make sure the API server is running."
          onRetry={() => {
            refetchSources();
            refetchPages();
          }}
        />
      </>
    );
  }

  return (
    <>
      <PageHeader
        title="Dashboard"
        description="Overview of your RAG pipeline"
      />

      {/* Stats Grid */}
      {isLoading ? (
        <SkeletonCards count={6} />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {stats.map((stat) => (
            <Card key={stat.title} className="border-border bg-card">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  {stat.title}
                </CardTitle>
                <stat.icon className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                {stat.isBadge ? (
                  <StatusBadge status={String(stat.value)} />
                ) : (
                  <p className="text-2xl font-semibold tracking-tight">
                    {stat.value}
                  </p>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Recent Crawl Jobs */}
      {!isLoading && recentJobs && recentJobs.length > 0 && (
        <div className="mt-8">
          <h2 className="mb-4 text-lg font-semibold tracking-tight">
            Recent Crawl Jobs
          </h2>
          <Card className="border-border">
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border">
                      <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                        Source
                      </th>
                      <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                        URL
                      </th>
                      <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                        Status
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {recentJobs.map((job) => (
                      <tr
                        key={job.id}
                        className="border-b border-border last:border-0"
                      >
                        <td className="px-4 py-3 font-medium">{job.name}</td>
                        <td className="px-4 py-3 text-muted-foreground">
                          <span className="max-w-[300px] truncate block">
                            {job.url}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <StatusBadge status={job.status} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Quick Actions */}
      <div className="mt-8">
        <h2 className="mb-4 text-lg font-semibold tracking-tight">
          Quick Actions
        </h2>
        <div className="flex flex-wrap gap-3">
          <Link href="/sources" className={buttonVariants()}>
            <Plus className="mr-2 h-4 w-4" />
            Add Source
          </Link>
          <Link href="/retrieval" className={buttonVariants({ variant: "outline" })}>
            <Search className="mr-2 h-4 w-4" />
            Go to Retrieval
          </Link>
          <Link href="/chat" className={buttonVariants({ variant: "outline" })}>
            <MessageSquare className="mr-2 h-4 w-4" />
            Open Chat
          </Link>
        </div>
      </div>
    </>
  );
}
