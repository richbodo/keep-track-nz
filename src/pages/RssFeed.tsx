import { Header } from '@/components/Header';
import { Footer } from '@/components/Footer';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Copy, Rss } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { labels } from '@/data/actions';

const RssFeed = () => {
  const { toast } = useToast();

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast({
      title: 'Copied!',
      description: 'RSS URL copied to clipboard',
    });
  };

  const baseUrl = 'https://keeptrack.nz/feed.xml';

  const feedExamples = [
    { label: 'All actions', url: baseUrl },
    { label: 'Parliament bills', url: `${baseUrl}?source=PARLIAMENT` },
    { label: 'New legislation', url: `${baseUrl}?source=LEGISLATION` },
    { label: 'Gazette notices', url: `${baseUrl}?source=GAZETTE` },
    { label: 'Beehive releases', url: `${baseUrl}?source=BEEHIVE` },
  ];

  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex-1">
        <div className="container mx-auto max-w-3xl px-4 py-8">
          <div className="mb-8 flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-accent text-accent-foreground">
              <Rss className="h-6 w-6" />
            </div>
            <div>
              <h2 className="font-serif text-3xl font-bold">RSS Feed</h2>
              <p className="text-muted-foreground">
                Subscribe to government actions in your feed reader
              </p>
            </div>
          </div>

          <Card className="mb-8">
            <CardHeader>
              <CardTitle className="font-serif">Main Feed</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex gap-2">
                <Input value={baseUrl} readOnly className="font-mono text-sm" />
                <Button variant="outline" onClick={() => copyToClipboard(baseUrl)}>
                  <Copy className="h-4 w-4" />
                </Button>
              </div>
              <p className="mt-2 text-sm text-muted-foreground">
                Subscribe to this feed to receive all government actions.
              </p>
            </CardContent>
          </Card>

          <Card className="mb-8">
            <CardHeader>
              <CardTitle className="font-serif">Filtered Feeds</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground">
                You can filter the feed by source or label using URL parameters.
              </p>
              <div className="space-y-3">
                {feedExamples.map((example) => (
                  <div key={example.label} className="flex items-center gap-2">
                    <span className="w-32 shrink-0 text-sm font-medium">
                      {example.label}
                    </span>
                    <Input
                      value={example.url}
                      readOnly
                      className="font-mono text-xs"
                    />
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => copyToClipboard(example.url)}
                    >
                      <Copy className="h-3 w-3" />
                    </Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="font-serif">Filter by Label</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="mb-4 text-sm text-muted-foreground">
                Add <code className="rounded bg-muted px-1">?label=</code> to filter by topic:
              </p>
              <div className="flex flex-wrap gap-2">
                {labels.map((label) => (
                  <Button
                    key={label}
                    variant="outline"
                    size="sm"
                    className="text-xs"
                    onClick={() => copyToClipboard(`${baseUrl}?label=${encodeURIComponent(label)}`)}
                  >
                    {label}
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default RssFeed;
