import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import { CheckCircle2, Circle } from "lucide-react";

const About = () => {
  return (
    <div className="min-h-screen bg-background flex flex-col">
      <Header />
      
      <main className="flex-1 container mx-auto px-4 py-8 max-w-3xl">
        <article className="prose prose-slate dark:prose-invert max-w-none">
          <h1 className="font-serif text-3xl font-bold text-foreground mb-6">About KeepTrack.nz</h1>
          
          <p className="text-lg text-muted-foreground mb-8">
            <a href="https://keeptrack.nz" className="text-primary hover:underline">KeepTrack.nz</a> was created to display the documented actions of the NZ government.
          </p>

          <div className="bg-muted/50 border border-border rounded-lg p-4 mb-8 inline-block">
            <span className="text-sm font-medium text-muted-foreground">Status:</span>
            <span className="ml-2 text-foreground font-semibold">Experiment - we are using fixture data - not real data at this point</span>
          </div>

          <h2 className="font-serif text-2xl font-semibold text-foreground mt-8 mb-4">Roadmap</h2>

          <h3 className="font-serif text-xl font-medium text-foreground mt-6 mb-3">Minimum Useful</h3>
          
          <ul className="space-y-3 list-none pl-0">
            <li className="flex items-start gap-3">
              <CheckCircle2 className="h-5 w-5 text-green-600 dark:text-green-500 mt-0.5 flex-shrink-0" />
              <span className="text-foreground">Static Site with working UI bits.</span>
            </li>
            <li className="flex items-start gap-3">
              <Circle className="h-5 w-5 text-muted-foreground mt-0.5 flex-shrink-0" />
              <span className="text-muted-foreground">Scraper script to scrape all documented action data nightly into action files by source</span>
            </li>
            <li className="flex items-start gap-3">
              <Circle className="h-5 w-5 text-muted-foreground mt-0.5 flex-shrink-0" />
              <span className="text-muted-foreground">Action De-Duper - checks to make sure that there are no duplicate actions in the action files</span>
            </li>
            <li className="flex items-start gap-3">
              <Circle className="h-5 w-5 text-muted-foreground mt-0.5 flex-shrink-0" />
              <span className="text-muted-foreground">Move hosting to github</span>
            </li>
            <li className="flex items-start gap-3">
              <Circle className="h-5 w-5 text-muted-foreground mt-0.5 flex-shrink-0" />
              <span className="text-muted-foreground">Python script to publish action files nightly to both github and IPFS</span>
            </li>
            <li className="flex items-start gap-3">
              <Circle className="h-5 w-5 text-muted-foreground mt-0.5 flex-shrink-0" />
              <span className="text-muted-foreground">Augment scraper script with TSL-cert and MD5 DLT nightly pegs</span>
            </li>
            <li className="flex items-start gap-3">
              <Circle className="h-5 w-5 text-muted-foreground mt-0.5 flex-shrink-0" />
              <span className="text-muted-foreground">RSS feeds work for all action data - no missing data.</span>
            </li>
          </ul>

          <h3 className="font-serif text-xl font-medium text-foreground mt-8 mb-3">Future Directions/Ideas</h3>
          
          <ul className="space-y-3 list-none pl-0">
            <li className="flex items-start gap-3">
              <Circle className="h-5 w-5 text-muted-foreground mt-0.5 flex-shrink-0" />
              <span className="text-muted-foreground">
                <strong className="text-foreground">LLM summary comparator script</strong> - grabs any action from the site db, runs it against all the LLMs that you have an URL/API-key for, generates summaries, then, once all summaries are in, compares them to identify relative bias.
              </span>
            </li>
            <li className="flex items-start gap-3">
              <Circle className="h-5 w-5 text-muted-foreground mt-0.5 flex-shrink-0" />
              <span className="text-muted-foreground">
                <strong className="text-foreground">LLM futurism script</strong> - summarize one action, and have a guess at its likely effects.
              </span>
            </li>
            <li className="flex items-start gap-3">
              <Circle className="h-5 w-5 text-muted-foreground mt-0.5 flex-shrink-0" />
              <span className="text-muted-foreground">
                <strong className="text-foreground">LLM links</strong> - Next to each action, add links to generate a summary - on the site of any LLM service.
              </span>
            </li>
            <li className="flex items-start gap-3">
              <Circle className="h-5 w-5 text-muted-foreground mt-0.5 flex-shrink-0" />
              <span className="text-muted-foreground">
                <strong className="text-foreground">LLM news source bias search</strong> - For each news source, grab the news for a given time period, and note what actions they reported on and guess as to how biased they were and why.
              </span>
            </li>
          </ul>

          <div className="mt-10 pt-6 border-t border-border">
            <a 
              href="https://github.com/richbodo/keep-track-nz" 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-primary hover:underline font-medium"
            >
              GitHub project →
            </a>
          </div>
        </article>
      </main>

      <Footer />
    </div>
  );
};

export default About;
