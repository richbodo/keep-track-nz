import { Rss, HelpCircle, Info } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Link } from 'react-router-dom';

export function Header() {
  return (
    <>
      {/* Blue accent bar */}
      <div className="h-2 bg-bar-accent" />
      
      <header className="border-b bg-card">
        <div className="container mx-auto flex items-center justify-between px-4 py-4">
          <Link to="/" className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded bg-primary text-primary-foreground">
              <span className="text-lg font-bold">K</span>
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight">
                KeepTrack<span className="text-primary">.nz</span>
              </h1>
              <p className="text-xs text-muted-foreground">
                NZ Government Actions
              </p>
            </div>
          </Link>
          <nav className="flex items-center gap-2">
            <Button variant="ghost" size="sm" asChild>
              <Link to="/about">
                <Info className="mr-1 h-4 w-4" />
                About
              </Link>
            </Button>
            <Button variant="ghost" size="sm" asChild>
              <Link to="/help">
                <HelpCircle className="mr-1 h-4 w-4" />
                Help
              </Link>
            </Button>
            <Button variant="outline" size="sm" asChild>
              <Link to="/rss">
                <Rss className="mr-1 h-4 w-4" />
                RSS
              </Link>
            </Button>
          </nav>
        </div>
      </header>
    </>
  );
}