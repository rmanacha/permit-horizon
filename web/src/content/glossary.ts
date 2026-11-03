import data from './glossary.json';

export interface GlossaryTerm {
  id: string;
  term: string;
  definition: string;
  section: string;
}

export const GLOSSARY: GlossaryTerm[] = data.terms;
const BY_ID = new Map(GLOSSARY.map((t) => [t.id, t]));

export function glossaryTerm(id: string): GlossaryTerm | undefined {
  return BY_ID.get(id);
}
