// Deterministic, SSR-stable pseudo-random in [0,1). Pure (Math.sin only), so it
// satisfies react-hooks/purity inside useMemo and avoids server/client hydration
// drift that Math.random() would cause for the decorative particle scatter.
export function rand(n: number): number {
  const x = Math.sin(n * 12.9898 + 78.233) * 43758.5453;
  return x - Math.floor(x);
}
