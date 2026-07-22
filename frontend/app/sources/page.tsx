"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import { Plus, Eye, RotateCw, Trash2 } from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { buttonVariants } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import { PageHeader } from "@/components/shared/page-header";
import { StatusBadge } from "@/components/shared/status-badge";
import { SearchInput } from "@/components/shared/search-input";
import { SkeletonTable } from "@/components/shared/skeleton-loader";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { ConfirmationModal } from "@/components/shared/confirmation-modal";

import {
  useSources,
  useCreateSource,
  useDeleteSource,
  useStartCrawl,
} from "@/hooks/use-sources";

// Form schema
const addSourceSchema = z.object({
  name: z.string().min(1, "Name is required"),
  base_url: z.string().url("Must be a valid URL"),
  technology: z.string().optional(),
  version: z.string().optional(),
});

type AddSourceForm = z.infer<typeof addSourceSchema>;

export default function SourcesPage() {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<number | null>(null);

  const { data: sources, isLoading, error, refetch } = useSources();
  const createSource = useCreateSource();
  const deleteSource = useDeleteSource();
  const startCrawl = useStartCrawl();

  const form = useForm<AddSourceForm>({
    resolver: zodResolver(addSourceSchema),
    defaultValues: {
      name: "",
      base_url: "",
      technology: "",
      version: "",
    },
  });

  const onSubmit = async (data: AddSourceForm) => {
    await createSource.mutateAsync(data);
    form.reset();
    setDialogOpen(false);
  };

  const filtered = useMemo(() => {
    if (!sources) return [];
    return sources.filter((s) => {
      const matchesSearch =
        s.name.toLowerCase().includes(search.toLowerCase()) ||
        s.base_url.toLowerCase().includes(search.toLowerCase());
      const matchesStatus =
        statusFilter === "all" || s.status === statusFilter;
      return matchesSearch && matchesStatus;
    });
  }, [sources, search, statusFilter]);

  if (error) {
    return (
      <>
        <PageHeader title="Sources" description="Manage documentation sources" />
        <ErrorState onRetry={() => refetch()} />
      </>
    );
  }

  return (
    <>
      <PageHeader title="Sources" description="Manage documentation sources">
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger render={<Button />}>
            <Plus className="mr-2 h-4 w-4" />
            Add Source
          </DialogTrigger>
          <DialogContent className="sm:max-w-lg">
            <form onSubmit={form.handleSubmit(onSubmit)}>
              <DialogHeader>
                <DialogTitle>Add Documentation Source</DialogTitle>
                <DialogDescription>
                  Add a new documentation website to crawl and index.
                </DialogDescription>
              </DialogHeader>
              <div className="mt-4 space-y-4">
                <div>
                  <label className="mb-1.5 block text-sm font-medium">
                    Documentation Name
                  </label>
                  <Input
                    placeholder="e.g. React Documentation"
                    {...form.register("name")}
                  />
                  {form.formState.errors.name && (
                    <p className="mt-1 text-xs text-destructive">
                      {form.formState.errors.name.message}
                    </p>
                  )}
                </div>
                <div>
                  <label className="mb-1.5 block text-sm font-medium">
                    Base URL
                  </label>
                  <Input
                    placeholder="https://react.dev/reference"
                    {...form.register("base_url")}
                  />
                  {form.formState.errors.base_url && (
                    <p className="mt-1 text-xs text-destructive">
                      {form.formState.errors.base_url.message}
                    </p>
                  )}
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="mb-1.5 block text-sm font-medium">
                      Technology
                    </label>
                    <Input
                      placeholder="e.g. React"
                      {...form.register("technology")}
                    />
                  </div>
                  <div>
                    <label className="mb-1.5 block text-sm font-medium">
                      Version{" "}
                      <span className="text-muted-foreground">(optional)</span>
                    </label>
                    <Input
                      placeholder="e.g. 19.x"
                      {...form.register("version")}
                    />
                  </div>
                </div>
              </div>
              <DialogFooter className="mt-6">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setDialogOpen(false)}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={createSource.isPending}>
                  {createSource.isPending ? "Saving..." : "Save"}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </PageHeader>

      {/* Filters */}
      <div className="mb-4 flex flex-col gap-3 sm:flex-row">
        <SearchInput
          placeholder="Search sources..."
          value={search}
          onChange={setSearch}
          className="sm:max-w-xs"
        />
        <Select value={statusFilter} onValueChange={(v) => v && setStatusFilter(v)}>
          <SelectTrigger className="w-full sm:w-40">
            <SelectValue placeholder="All statuses" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All statuses</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="crawling">Crawling</SelectItem>
            <SelectItem value="processed">Processed</SelectItem>
            <SelectItem value="failed">Failed</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Table */}
      {isLoading ? (
        <SkeletonTable />
      ) : filtered.length === 0 ? (
        <EmptyState
          title="No sources found"
          description={
            sources && sources.length > 0
              ? "No sources match your filters."
              : "Add your first documentation source to get started."
          }
          actionLabel={!sources || sources.length === 0 ? "Add Source" : undefined}
          onAction={
            !sources || sources.length === 0
              ? () => setDialogOpen(true)
              : undefined
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
                      Name
                    </th>
                    <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                      Base URL
                    </th>
                    <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                      Status
                    </th>
                    <th className="px-4 py-3 text-right font-medium text-muted-foreground">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((source) => (
                    <tr
                      key={source.id}
                      className="border-b border-border last:border-0 hover:bg-muted/50 transition-colors"
                    >
                      <td className="px-4 py-3 font-medium">{source.name}</td>
                      <td className="px-4 py-3 text-muted-foreground">
                        <span className="max-w-[300px] truncate block">
                          {source.base_url}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <StatusBadge status={source.status} />
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center justify-end gap-1">
                          <Link href={`/sources/${source.id}`} className={buttonVariants({ variant: "ghost", size: "icon", className: "h-8 w-8" })}>
                            <Eye className="h-4 w-4" />
                          </Link>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8"
                            onClick={() => startCrawl.mutate(source.id)}
                            disabled={source.status === "crawling"}
                          >
                            <RotateCw className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-destructive hover:text-destructive"
                            onClick={() => setDeleteTarget(source.id)}
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

      {/* Delete Confirmation */}
      <ConfirmationModal
        open={deleteTarget !== null}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        title="Delete Source"
        description="This will permanently delete this documentation source and all its crawled pages. This action cannot be undone."
        confirmLabel="Delete"
        loading={deleteSource.isPending}
        onConfirm={async () => {
          if (deleteTarget !== null) {
            await deleteSource.mutateAsync(deleteTarget);
            setDeleteTarget(null);
          }
        }}
      />
    </>
  );
}
