// URL slug: lowercase, runs of non-alphanumerics become a single dash, no dashes at the ends.
export function slugify(s) {
  return s.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
}
