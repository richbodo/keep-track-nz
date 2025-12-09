import { Header } from '@/components/Header';
import { Footer } from '@/components/Footer';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

const Help = () => {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex-1">
        <div className="container mx-auto max-w-3xl px-4 py-8">
          <h2 className="font-serif text-3xl font-bold">Help & Documentation</h2>
          <p className="mt-2 text-muted-foreground">
            Learn how to use KeepTrack.nz to stay informed about NZ Government actions.
          </p>

          <div className="mt-8 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="font-serif">What is KeepTrack.nz?</CardTitle>
              </CardHeader>
              <CardContent className="prose prose-sm max-w-none text-muted-foreground">
                <p>
                  KeepTrack.nz is a chronological record of all official actions taken by the
                  New Zealand Government. We aggregate data from four primary sources:
                </p>
                <ul className="mt-4 space-y-2">
                  <li>
                    <strong>Parliament</strong> (bills.parliament.nz) — Bills and their progress through Parliament
                  </li>
                  <li>
                    <strong>Legislation</strong> (legislation.govt.nz) — Enacted laws and amendments
                  </li>
                  <li>
                    <strong>Gazette</strong> (gazette.govt.nz) — Official notices and appointments
                  </li>
                  <li>
                    <strong>Beehive</strong> (beehive.govt.nz) — Press releases and speeches
                  </li>
                </ul>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="font-serif">Using the RSS Feed</CardTitle>
              </CardHeader>
              <CardContent className="prose prose-sm max-w-none text-muted-foreground">
                <p>
                  Our RSS feed allows you to subscribe to government actions using any feed reader.
                  You can subscribe to all actions or filter by source or label.
                </p>
                <h4 className="mt-4 font-semibold text-foreground">Example RSS URLs:</h4>
                <ul className="mt-2 space-y-1 font-mono text-xs">
                  <li>All actions: <code>/rss</code></li>
                  <li>Parliament only: <code>/rss?source=PARLIAMENT</code></li>
                  <li>By label: <code>/rss?label=Housing</code></li>
                  <li>Combined: <code>/rss?source=BEEHIVE&label=Health</code></li>
                </ul>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="font-serif">For Journalists & Researchers</CardTitle>
              </CardHeader>
              <CardContent className="prose prose-sm max-w-none text-muted-foreground">
                <p>
                  KeepTrack.nz is designed to be a neutral, factual resource. We aim to provide
                  a complete record of government actions without editorial commentary.
                </p>
                <p className="mt-4">
                  Each action links directly to its official source, allowing you to verify
                  information and access full documents. Labels are applied to help with
                  categorisation but the underlying data is always from official sources.
                </p>
                <p className="mt-4">
                  A future API is planned for more flexible data access. If you have specific
                  needs, please get in touch.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="font-serif">About Election Cycles</CardTitle>
              </CardHeader>
              <CardContent className="prose prose-sm max-w-none text-muted-foreground">
                <p>
                  Actions are organised by election cycle. Currently tracking the 54th Parliament
                  under the National-led coalition government (2023–present).
                </p>
                <p className="mt-4">
                  Historical data from previous parliaments may be added in future.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default Help;
