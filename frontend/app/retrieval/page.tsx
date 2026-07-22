"use client";

import { useState } from "react";
import { Search, FileText, ExternalLink, Layers, Hash } from "lucide-react";
import { useMutation } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import { PageHeader } from "@/components/shared/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingSpinner } from "@/components/shared/loading-spinner";

import { searchService } from "@/services/retrieval";
import { SearchResponse, SearchMode } from "@/types";
import { useSources } from "@/hooks/use-sources";

export default function RetrievalPage() {
  const [query, setQuery] = useState("");
  const [topK, setTopK] = useState("5");
  const [mode, setMode] = useState<SearchMode>("hybrid");
  const [sourceFilter, setSourceFilter] = useState<string>("all");
  const [result, setResult] = useState<SearchResponse | null>(null);

  const { data: sources } = useSources();

  const searchMutation = useMutation({
    mutationFn: () =>
      searchService.search({
        query,
        top_k: Number(topK),
        search_type: mode,
        source_id: sourceFilter !== "all" ? Number(sourceFilter) : null,
      }),
    onSuccess: (data) => setResult(data),
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    searchMutation.mutate();
  };

  return (
    <>
      <PageHeader
        title="Retrieval"
        description="Search your indexed documentation. Returns retrieved chunks — no AI answer."
      />

      {/* Search Form */}
      <Card className="border-border mb-6">
        <CardContent className="pt-6">
          <form onSubmit={handleSearch} className="space-y-4">
            <div className="flex gap-3">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Enter your question to search documentation..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="pl-9"
                />
              </div>
              <Button
                type="submit"
                disabled={!query.trim() || searchMutation.isPending}
              >
                {searchMutation.isPending ? (
                  <LoadingSpinner size="sm" className="mr-2" />
                ) : (
                  <Search className="mr-2 h-4 w-4" />
                )}
                Search
              </Button>
            </div>

            <div className="flex flex-wrap gap-3">
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">Source:</span>
                <Select value={sourceFilter} onValueChange={(v) => v && setSourceFilter(v)}>
                  <SelectTrigger className="w-44">
                    <SelectValue placeholder="All sources" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All sources</SelectItem>
                    {sources?.map((s) => (
                      <SelectItem key={s.id} value={String(s.id)}>
                        {s.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">Top-K:</span>
                <Select value={topK} onValueChange={(v) => v && setTopK(v)}>
                  <SelectTrigger className="w-20">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="3">3</SelectItem>
                    <SelectItem value="5">5</SelectItem>
                    <SelectItem value="10">10</SelectItem>
                    <SelectItem value="20">20</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">Mode:</span>
                <Select
                  value={mode}
                  onValueChange={(v) => v && setMode(v as SearchMode)}
                >
                  <SelectTrigger className="w-28">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="vector">Vector</SelectItem>
                    <SelectItem value="hybrid">Hybrid</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Error */}
      {searchMutation.isError && (
        <ErrorState
          title="Search Failed"
          message={
            searchMutation.error instanceof Error
              ? searchMutation.error.message.includes("Network Error")
                ? "Could not reach the search endpoint. Make sure your backend is running and documents are indexed."
                : searchMutation.error.message
              : "An error occurred while searching."
          }
          onRetry={() => searchMutation.mutate()}
        />
      )}

      {/* Results */}
      {searchMutation.isPending && (
        <div className="flex items-center justify-center py-16">
          <LoadingSpinner size="lg" />
        </div>
      )}

      {result && !searchMutation.isPending && !searchMutation.isError && (
        <>
          {/* Summary */}
          <div className="mb-4 flex items-center gap-4 text-sm text-muted-foreground">
            <span>
              {result.total} result{result.total !== 1 ? "s" : ""} found
            </span>
            <Badge variant="outline" className="text-xs">
              {mode}
            </Badge>
            {sourceFilter !== "all" && (
              <Badge variant="outline" className="text-xs">
                Source #{sourceFilter}
              </Badge>
            )}
          </div>

          {result.results.length === 0 ? (
            <EmptyState
              icon={Search}
              title="No results found"
              description="The search didn't return any results. Try a different query or make sure your documentation is indexed."
            />
          ) : (
            <div className="space-y-4">
              {result.results.map((item, index) => (
                <Card key={index} className="border-border">
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between gap-4">
                      <div className="space-y-1 min-w-0">
                        <CardTitle className="text-sm font-medium flex items-center gap-2">
                          <FileText className="h-4 w-4 text-muted-foreground shrink-0" />
                          <span className="truncate">
                            {item.page_title || "Unknown Page"}
                          </span>
                          {item.source_name && (
                            <Badge
                              variant="outline"
                              className="shrink-0 text-xs font-normal"
                            >
                              {item.source_name}
                            </Badge>
                          )}
                        </CardTitle>
                        {item.heading && (
                          <p className="text-xs text-muted-foreground flex items-center gap-1">
                            <Hash className="h-3 w-3" />
                            {item.heading}
                          </p>
                        )}
                      </div>
                      <Badge
                        variant="outline"
                        className="shrink-0 font-mono text-xs tabular-nums"
                      >
                        {(item.score * 100).toFixed(1)}%
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="rounded-md bg-muted/50 p-3 text-sm leading-relaxed font-mono whitespace-pre-wrap max-h-64 overflow-y-auto">
                      {item.content}
                    </div>

                    <div className="mt-3 flex items-center gap-4 text-xs text-muted-foreground">
                      {item.url && (
                        <a
                          href={item.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-1 hover:text-foreground transition-colors truncate max-w-md"
                        >
                          <ExternalLink className="h-3 w-3 shrink-0" />
                          {item.url}
                        </a>
                      )}
                      <span className="flex items-center gap-1 shrink-0">
                        <Layers className="h-3 w-3" />
                        Chunk #{item.chunk_index}
                      </span>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </>
      )}

      {/* Initial empty state */}
      {!result && !searchMutation.isPending && !searchMutation.isError && (
        <EmptyState
          icon={Search}
          title="Search your documentation"
          description="Enter a question above to search your indexed documentation and validate retrieval quality."
        />
      )}
    </>
  );
}
