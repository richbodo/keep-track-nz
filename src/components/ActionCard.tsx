import { ExternalLink } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import type { GovernmentAction, SourceSystem } from '@/data/fixtureData';
import { cn } from '@/lib/utils';

const sourceConfig: Record<SourceSystem, { label: string; className: string }> = {
  PARLIAMENT: { label: 'Parliament', className: 'bg-source-parliament text-primary-foreground' },
  LEGISLATION: { label: 'Legislation', className: 'bg-source-legislation text-primary-foreground' },
  GAZETTE: { label: 'Gazette', className: 'bg-source-gazette text-primary-foreground' },
  BEEHIVE: { label: 'Beehive', className: 'bg-source-beehive text-primary-foreground' },
};

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('en-NZ', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
}

interface ActionCardProps {
  action: GovernmentAction;
}

export function ActionCard({ action }: ActionCardProps) {
  const source = sourceConfig[action.source_system];

  return (
    <Card className="transition-shadow hover:shadow-md">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <Badge className={cn('text-xs font-medium', source.className)}>
                {source.label}
              </Badge>
              <span className="text-sm text-muted-foreground">
                {formatDate(action.date)}
              </span>
            </div>
            <h3 className="text-lg font-semibold leading-tight">
              <a
                href={action.url}
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-primary hover:underline"
              >
                {action.title}
              </a>
            </h3>
          </div>
          <a
            href={action.url}
            target="_blank"
            rel="noopener noreferrer"
            className="shrink-0 text-muted-foreground transition-colors hover:text-primary"
            aria-label="View source"
          >
            <ExternalLink className="h-4 w-4" />
          </a>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-sm text-muted-foreground">{action.summary}</p>
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-medium text-foreground">
            {action.primary_entity}
          </span>
          <span className="text-muted-foreground">·</span>
          {action.labels.map((label) => (
            <Badge key={label} variant="secondary" className="text-xs">
              {label}
            </Badge>
          ))}
        </div>
        {action.metadata.document_type && (
          <p className="text-xs text-muted-foreground">
            {action.metadata.document_type}
            {action.metadata.portfolio && ` · ${action.metadata.portfolio}`}
          </p>
        )}
        {action.metadata.act_number && (
          <p className="text-xs text-muted-foreground">
            {action.metadata.act_number}
          </p>
        )}
        {action.metadata.bill_number && action.metadata.stage_history && (
          <p className="text-xs text-muted-foreground">
            Bill {action.metadata.bill_number} · Latest: {action.metadata.stage_history[action.metadata.stage_history.length - 1]?.stage}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
