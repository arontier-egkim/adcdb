import { Link, Outlet } from "react-router";

const navLinks = [
  { to: "/browse", label: "Browse" },
  { to: "/search", label: "Search" },
  { to: "/about", label: "About" },
];

export default function Layout() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border sticky top-0 bg-background/95 backdrop-blur z-50">
        <nav className="max-w-6xl mx-auto flex items-center gap-4 sm:gap-6 px-4 h-14">
          <Link to="/" className="font-bold text-lg text-primary shrink-0">
            ADCDB
          </Link>
          {navLinks.map((link) => (
            <Link
              key={link.to}
              to={link.to}
              className="text-sm hover:text-primary transition-colors"
            >
              {link.label}
            </Link>
          ))}
        </nav>
      </header>
      <main className="max-w-6xl mx-auto px-4 py-6">
        <Outlet />
      </main>
      <footer className="border-t border-border mt-12">
        <div className="max-w-6xl mx-auto px-4 py-6 text-center text-xs text-muted-foreground">
          ADCDB — Antibody-Drug Conjugate Database. 3D structures are
          predicted/modeled and should not be used for quantitative analysis.
        </div>
      </footer>
    </div>
  );
}
