# Community Solutions design system: component props (reference)

`index.d.ts` is the design system's own declaration of its React components' props (2026 brand
refresh, Community Solutions Comms team; copied from `planning/research/design_system/components/`,
decision 76). The site ports the components it uses to TypeScript in `web/src/components/ds/`
with CSS classes on the tokens instead of inline style objects. `scripts/ds_props.test.mjs`
checks that every prop declared here exists on the port, with one deliberate change: `style`
becomes `className`, because the site keeps all styling in stylesheets.
