// The working draft stays at deepcode-code:<slug> for backwards compatibility.
// Saved versions are immutable and never evicted to make space for newer work.
export function codeVersionsKey(slug) {
  return `deepcode-code-versions:${slug}`;
}

export function loadCodeVersions(storage, slug) {
  const raw = storage.getItem(codeVersionsKey(slug));
  if (raw === null) return [];
  const data = JSON.parse(raw);
  if (data?.schemaVersion !== 1 || !Array.isArray(data.versions) || data.versions.some((version) =>
    !version || typeof version.id !== "string" || typeof version.name !== "string" ||
    typeof version.code !== "string" || typeof version.createdAt !== "string"
  )) {
    throw new Error("Saved version history could not be read. It has been left unchanged.");
  }
  return data.versions;
}

export function saveCodeVersion(storage, slug, code, name, { onlyIfChanged = false } = {}) {
  const versions = loadCodeVersions(storage, slug);
  if (onlyIfChanged && versions.some((version) => version.code === code)) return versions;
  const version = {
    id: globalThis.crypto.randomUUID(),
    name: name.trim() || `Version ${versions.length + 1}`,
    code,
    createdAt: new Date().toISOString(),
  };
  storage.setItem(codeVersionsKey(slug), JSON.stringify({ schemaVersion: 1, versions: [version, ...versions] }));
  return [version, ...versions];
}
