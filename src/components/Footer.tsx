export function Footer() {
  return (
    <footer className="border-t bg-card py-8">
      <div className="container mx-auto px-4 text-center">
        <p className="text-sm text-muted-foreground">
          KeepTrack.nz — Tracking official actions of the New Zealand Government
        </p>
        <p className="mt-2 text-xs text-muted-foreground">
          Data sourced from{' '}
          <a href="https://bills.parliament.nz" className="underline hover:text-foreground" target="_blank" rel="noopener noreferrer">
            Parliament
          </a>
          ,{' '}
          <a href="https://www.legislation.govt.nz" className="underline hover:text-foreground" target="_blank" rel="noopener noreferrer">
            Legislation
          </a>
          ,{' '}
          <a href="https://gazette.govt.nz" className="underline hover:text-foreground" target="_blank" rel="noopener noreferrer">
            Gazette
          </a>
          , and{' '}
          <a href="https://www.beehive.govt.nz" className="underline hover:text-foreground" target="_blank" rel="noopener noreferrer">
            Beehive
          </a>
        </p>
        <p className="mt-4 text-xs text-muted-foreground">
          54th Parliament · National-led Coalition (2023–present)
        </p>
      </div>
    </footer>
  );
}
