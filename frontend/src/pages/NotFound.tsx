import { Link } from "react-router";

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center py-20 space-y-4">
      <h1 className="text-4xl font-bold text-muted-foreground">404</h1>
      <p className="text-muted-foreground">Page not found.</p>
      <Link
        to="/"
        className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground"
      >
        Back to Home
      </Link>
    </div>
  );
}
