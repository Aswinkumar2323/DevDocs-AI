import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const statusConfig: Record<
  string,
  { label: string; className: string }
> = {
  pending: {
    label: "Pending",
    className: "bg-yellow-500/15 text-yellow-700 dark:text-yellow-400 border-yellow-500/25",
  },
  running: {
    label: "Running",
    className: "bg-blue-500/15 text-blue-700 dark:text-blue-400 border-blue-500/25",
  },
  crawling: {
    label: "Crawling",
    className: "bg-blue-500/15 text-blue-700 dark:text-blue-400 border-blue-500/25",
  },
  downloading: {
    label: "Downloading",
    className: "bg-blue-500/15 text-blue-700 dark:text-blue-400 border-blue-500/25",
  },
  indexing: {
    label: "Indexing",
    className: "bg-violet-500/15 text-violet-700 dark:text-violet-400 border-violet-500/25",
  },
  indexed: {
    label: "Indexed",
    className: "bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 border-emerald-500/25",
  },
  partially_indexed: {
    label: "Partially Indexed",
    className: "bg-amber-500/15 text-amber-700 dark:text-amber-400 border-amber-500/25",
  },
  completed: {
    label: "Completed",
    className: "bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 border-emerald-500/25",
  },
  processed: {
    label: "Processed",
    className: "bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 border-emerald-500/25",
  },
  healthy: {
    label: "Healthy",
    className: "bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 border-emerald-500/25",
  },
  failed: {
    label: "Failed",
    className: "bg-red-500/15 text-red-700 dark:text-red-400 border-red-500/25",
  },
  offline: {
    label: "Offline",
    className: "bg-red-500/15 text-red-700 dark:text-red-400 border-red-500/25",
  },
  unknown: {
    label: "Unknown",
    className: "bg-zinc-500/15 text-zinc-700 dark:text-zinc-400 border-zinc-500/25",
  },
};

interface StatusBadgeProps {
  status: string;
  className?: string;
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const config = statusConfig[status.toLowerCase()] ?? {
    label: status,
    className: "bg-zinc-500/15 text-zinc-700 dark:text-zinc-400 border-zinc-500/25",
  };

  return (
    <Badge
      variant="outline"
      className={cn(
        "text-xs font-medium capitalize",
        config.className,
        className
      )}
    >
      {config.label}
    </Badge>
  );
}
