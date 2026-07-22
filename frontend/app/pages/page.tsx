"use client";

import { useState, useMemo } from "react";
import { FileText, Trash2, X, Layers, RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";

import { PageHeader } from "@/components/shared/page-header";
import { StatusBadge } from "@/components/shared/status-badge";
import { SearchInput } from "@/components/shared/search-input";
import { SkeletonTable } from "@/components/shared/skeleton-loader";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { ConfirmationModal } from "@/components/shared/confirmation-modal";
import { MarkdownViewer } from "@/components/shared/markdown-viewer";
import { LoadingSpinner } from "@/components/shared/loading-spinner";

import { usePages, usePage, useDeletePage } from "@/hooks/use-pages";
import { useIndexPage } from "@/hooks/use-indexing";

export default function PagesPage() {
  const [search, setSearch] = useState("");
  const [selectedPageId, setSelectedPageId] = useState<number | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<number | null>(null);

  const { data: pages, isLoading, error, refetch } = usePages();
  const { data: pageDetail, isLoading: detailLoading } = usePage(selectedPageId);
  const deletePage = useDeletePage();
  const indexPage = useIndexPage();

  const filtered = useMemo(() => {
    if (!pages) return [];
    if (!search) return pages;
    const q = search.toLowerCase();
    return pages.filter(
      (p) =>
        (p.title ?? "").toLowerCase().includes(q) ||
        p.url.toLowerCase().includes(q)
    );
  }, [pages, search]);

  const wordCount = pageDetail?.markdown
    ? pageDetail.markdown.split(/\s+/).filter(Boolean).length
    : 0;
  const charCount = pageDetail?.markdown?.length ?? 0;

  if (error) {
    return (
      <>
        <PageHeader title="Pages" description="Inspect crawled documentation" />
        <ErrorState onRetry={() => refetch()} />
      </>
    );
  }

  return (
    <>
      <PageHeader title="Pages" description="Inspect crawled documentation" />

      {/* Search */}
      <div className="mb-4">
        <SearchInput
          placeholder="Search pages by title or URL..."
          value={search}
          onChange={setSearch}
          className="sm:max-w-md"
        />
      </div>

      {/* Table */}
      {isLoading ? (
        <SkeletonTable />
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={FileText}
          title="No pages found"
          description={
            pages && pages.length > 0
              ? "No pages match your search."
              : "Crawl a documentation source to see pages here."
          }
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
                  {filtered.map((page) => (
                    <tr
                      key={page.id}
                      className="border-b border-border last:border-0 hover:bg-muted/50 transition-colors cursor-pointer"
                      onClick={() => setSelectedPageId(page.id)}
                    >
                      <td className="px-4 py-3 font-medium">
                        {page.title ?? "Untitled"}
                      </td>
                      <td className="px-4 py-3 text-muted-foreground">
                        <span className="max-w-[300px] truncate block">
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
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-destructive hover:text-destructive"
                            onClick={(e) => {
                              e.stopPropagation();
                              setDeleteTarget(page.id);
                            }}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
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

      {/* Detail Side Panel */}
      <Sheet
        open={selectedPageId !== null}
        onOpenChange={(open) => !open && setSelectedPageId(null)}
      >
        <SheetContent className="w-full sm:max-w-2xl overflow-hidden flex flex-col p-0">
          <SheetHeader className="px-6 pt-6 pb-4 border-b border-border shrink-0">
            <div className="flex items-center justify-between">
              <SheetTitle className="text-base">
                {detailLoading ? "Loading..." : pageDetail?.title ?? "Untitled"}
              </SheetTitle>
            </div>
          </SheetHeader>

          {detailLoading ? (
            <div className="flex items-center justify-center flex-1">
              <LoadingSpinner />
            </div>
          ) : pageDetail ? (
            <ScrollArea className="flex-1">
              <div className="px-6 py-4 space-y-6">
                {/* Metadata */}
                <div className="space-y-3">
                  <div>
                    <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                      URL
                    </span>
                    <p className="mt-1 text-sm break-all">
                      <a
                        href={pageDetail.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary underline underline-offset-4"
                      >
                        {pageDetail.url}
                      </a>
                    </p>
                  </div>

                  <div className="flex gap-6">
                    <div>
                      <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                        Status
                      </span>
                      <div className="mt-1">
                        <StatusBadge status={pageDetail.status} />
                      </div>
                    </div>
                    <div>
                      <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                        Words
                      </span>
                      <p className="mt-1 text-sm font-medium">
                        {wordCount.toLocaleString()}
                      </p>
                    </div>
                    <div>
                      <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                        Characters
                      </span>
                      <p className="mt-1 text-sm font-medium">
                        {charCount.toLocaleString()}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex flex-wrap gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => indexPage.mutate(pageDetail.id)}
                    disabled={!pageDetail.markdown || indexPage.isPending}
                  >
                    <Layers className="mr-2 h-3.5 w-3.5" />
                    {indexPage.isPending ? "Indexing Page..." : "Generate Chunks"}
                  </Button>
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={() => {
                      setDeleteTarget(pageDetail.id);
                      setSelectedPageId(null);
                    }}
                  >
                    <Trash2 className="mr-2 h-3.5 w-3.5" />
                    Delete
                  </Button>
                </div>

                <Separator />

                {/* Markdown Preview */}
                <div>
                  <h3 className="mb-3 text-sm font-medium">
                    Markdown Preview
                  </h3>
                  {pageDetail.markdown ? (
                    <div className="rounded-lg border border-border bg-card p-4">
                      <MarkdownViewer content={pageDetail.markdown} />
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">
                      No markdown content available.
                    </p>
                  )}
                </div>
              </div>
            </ScrollArea>
          ) : null}
        </SheetContent>
      </Sheet>

      {/* Delete Confirmation */}
      <ConfirmationModal
        open={deleteTarget !== null}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        title="Delete Page"
        description="This will permanently delete this page and all its associated data. This action cannot be undone."
        confirmLabel="Delete"
        loading={deletePage.isPending}
        onConfirm={async () => {
          if (deleteTarget !== null) {
            await deletePage.mutateAsync(deleteTarget);
            setDeleteTarget(null);
          }
        }}
      />
    </>
  );
}
