"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Play,
  Square,
  Trash2,
  ExternalLink,
  Globe,
  Zap,
  Layers,
  CheckCircle2,
  XCircle,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

import { PageHeader } from "@/components/shared/page-header";
import { StatusBadge } from "@/components/shared/status-badge";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { ConfirmationModal } from "@/components/shared/confirmation-modal";
import { LoadingPage } from "@/components/shared/loading-spinner";

import { useSource, useStartCrawl, useDeleteSource, useCrawlStatus } from "@/hooks/use-sources";
import { usePages } from "@/hooks/use-pages";
import { useStartIndexing, useIndexingStatus } from "@/hooks/use-indexing";

export default function SourceDetailPage() {
  const params = useParams();
  const router = useRouter();
  const sourceId = Number(params.id);

  const [deleteOpen, setDeleteOpen] = useState(false);

  const { data: source, isLoading, error, refetch } = useSource(sourceId);
  const isCrawling = source?.status === "crawling";
  const isIndexing = source?.status === "indexing";
  const { data: crawlStatus } = useCrawlStatus(sourceId, isCrawling);
  const { data: pages } = usePages({ source_id: sourceId });
  const startCrawl = useStartCrawl();
  const deleteSource = useDeleteSource();
  const startIndexing = useStartIndexing();
  const { data: indexingStatus } = useIndexingStatus(
    sourceId,
    isIndexing || source?.status === "indexed" || source?.status === "partially_indexed" || source?.status === "processed"
  );

  const canIndex =
    source?.status === "processed" ||
    source?.status === "indexed" ||
    source?.status === "partially_indexed";

  if (isLoading) return <LoadingPage />;
  if (error || !source) {
    return (
      <ErrorState
        title="Source not found"
        message="The documentation source could not be loaded."
        onRetry={() => refetch()}
      />
    );
  }

  return (
    <>
      <div className="mb-4">
        <Link href="/sources" className={buttonVariants({ variant: "ghost", size: "sm" })}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Sources
        </Link>
      </div>

      <PageHeader title={source.name} description={source.base_url}>
        <Button
          onClick={() => startCrawl.mutate(sourceId)}
          disabled={isCrawling || startCrawl.isPending}
        >
          <Play className="mr-2 h-4 w-4" />
          {isCrawling ? "Crawling..." : "Start Crawl"}
        </Button>
        <Button
          variant="outline"
          onClick={() => startIndexing.mutate(sourceId)}
          disabled={!canIndex || isIndexing || startIndexing.isPending}
        >
          <Zap className="mr-2 h-4 w-4" />
          {isIndexing ? "Indexing..." : startIndexing.isPending ? "Starting..." : "Index Source"}
        </Button>
        <Button variant="outline" disabled={!isCrawling}>
          <Square className="mr-2 h-4 w-4" />
          Stop Crawl
        </Button>
        <Button
          variant="destructive"
          onClick={() => setDeleteOpen(true)}
        >
          <Trash2 className="mr-2 h-4 w-4" />
          Delete
        </Button>
      </PageHeader>

      {/* Source Info */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-4">
        <Card className="border-border">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <StatusBadge status={source.status} />
          </CardContent>
        </Card>
        <Card className="border-border">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Pages
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-semibold">{pages?.length ?? 0}</p>
          </CardContent>
        </Card>
        <Card className="border-border">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Processed
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-semibold">
              {crawlStatus?.processed_pages ?? pages?.filter((p) => p.status === "processed").length ?? 0}
            </p>
          </CardContent>
        </Card>
        <Card className="border-border">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Failed
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-semibold text-destructive">
              {crawlStatus?.failed_pages ?? pages?.filter((p) => p.status === "failed").length ?? 0}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Indexing Status */}
      {indexingStatus && (
        <div className="mb-8">
          <h2 className="mb-4 text-lg font-semibold tracking-tight flex items-center gap-2">
            <Layers className="h-5 w-5 text-muted-foreground" />
            Indexing Status
          </h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Card className="border-border">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Indexed Pages
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-baseline gap-2">
                  <p className="text-2xl font-semibold">{indexingStatus.indexed_pages}</p>
                  <span className="text-sm text-muted-foreground">
                    / {indexingStatus.processed_pages}
                  </span>
                </div>
                {indexingStatus.processed_pages > 0 && (
                  <div className="mt-2 h-1.5 w-full rounded-full bg-muted overflow-hidden">
                    <div
                      className="h-full rounded-full bg-primary transition-all duration-500"
                      style={{
                        width: `${Math.round((indexingStatus.indexed_pages / indexingStatus.processed_pages) * 100)}%`,
                      }}
                    />
                  </div>
                )}
              </CardContent>
            </Card>
            <Card className="border-border">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Total Chunks
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-semibold">{indexingStatus.total_chunks}</p>
              </CardContent>
            </Card>
            <Card className="border-border">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Avg Chunks / Page
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-semibold">
                  {indexingStatus.indexed_pages > 0
                    ? (indexingStatus.total_chunks / indexingStatus.indexed_pages).toFixed(1)
                    : "—"}
                </p>
              </CardContent>
            </Card>
            <Card className="border-border">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Embeddings
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <p className="text-2xl font-semibold">{indexingStatus.total_chunks}</p>
                  {indexingStatus.total_chunks > 0 && (
                    <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* Pages Table */}
      <h2 className="mb-4 text-lg font-semibold tracking-tight">
        Crawled Pages
      </h2>

      {!pages || pages.length === 0 ? (
        <EmptyState
          icon={Globe}
          title="No pages crawled yet"
          description="Start a crawl to discover and index pages from this documentation source."
          actionLabel="Start Crawl"
          onAction={() => startCrawl.mutate(sourceId)}
        />
      ) : (
        <Card className="border-border">
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                      Title
                    </th>
                    <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                      URL
                    </th>
                    <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                      Status
                    </th>
                    <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                      Updated
                    </th>
                    <th className="px-4 py-3 text-right font-medium text-muted-foreground">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {pages.map((page) => (
                    <tr
                      key={page.id}
                      className="border-b border-border last:border-0 hover:bg-muted/50 transition-colors"
                    >
                      <td className="px-4 py-3 font-medium">
                        {page.title ?? "Untitled"}
                      </td>
                      <td className="px-4 py-3 text-muted-foreground">
                        <span className="max-w-[250px] truncate block">
                          {page.url}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <StatusBadge status={page.status} />
                      </td>
                      <td className="px-4 py-3 text-muted-foreground">
                        {new Date(page.updated_at).toLocaleDateString()}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center justify-end gap-1">
                          <Link
                            href={`/pages?id=${page.id}`}
                            className={buttonVariants({ variant: "ghost", size: "icon", className: "h-8 w-8" })}
                          >
                            <ExternalLink className="h-4 w-4" />
                          </Link>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Delete Confirmation */}
      <ConfirmationModal
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        title="Delete Source"
        description={`This will permanently delete "${source.name}" and all its crawled pages. This action cannot be undone.`}
        confirmLabel="Delete"
        loading={deleteSource.isPending}
        onConfirm={async () => {
          await deleteSource.mutateAsync(sourceId);
          router.push("/sources");
        }}
      />
    </>
  );
}
