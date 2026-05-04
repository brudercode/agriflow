/**
 * Minimal landing page placeholder.
 * Week 1 deliverable will replace this with a localised marketing page.
 */
export default function Home() {
  return (
    <main className="mx-auto max-w-2xl px-6 py-16 font-sans">
      <h1 className="text-4xl font-bold tracking-tight">🌾 AgriFlow</h1>
      <p className="mt-4 text-lg text-neutral-600">
        Honest price transparency, voluntary provenance, and warm introductions for
        European farmers and buyers. <strong>Informational middleware only.</strong>
      </p>
      <ul className="mt-6 list-disc space-y-1 pl-5 text-neutral-700">
        <li>Daily MercaBarna · POOLRED · ISMEA · BLE reference prices</li>
        <li>PostcardSSL — voluntary EUDR preparation aid (not a DDS)</li>
        <li>Multilingual producer profiles (EN / ES / IT / DE)</li>
      </ul>
      <p className="mt-8 text-sm text-neutral-500">
        Beta · GDPR-first · EU-hosted · AGPL-3.0
      </p>
    </main>
  );
}
