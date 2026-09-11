import type { CSSProperties } from "react";
import type { SiteContent } from "../content/types";
import { Header, Footer } from "./Navigation";
import { Hero, About, Plans, Services, FAQ } from "./Sections";
import { InquiryProvider } from "./InquiryState";
import { Inquiry } from "./Inquiry";
import { ContactForm } from "./ContactForm";
import { DemoChat } from "./DemoChat";
import s from "./Site.module.css";
export function CorporateSite({ content }: { content: SiteContent }) {
  const tokens = { "--brand-navy": content.brand.navy, "--brand-blue": content.brand.blue,
    "--brand-cyan": content.brand.cyan } as CSSProperties;
  return <InquiryProvider content={content}><div className={s.site} style={tokens}>
    <a className={s.skip} href="#contenido">Saltar al contenido</a>
    <Header brand={content.brand.name} hasPlans={content.plans.length > 0} />
    <main id="contenido">
      <noscript>Las interacciones locales necesitan JavaScript. No se envía información.</noscript>
      <Hero content={content.hero} />
      <About content={content.about} />
      {content.plans.length > 0 && <Plans plans={content.plans} />}
      <Services services={content.services} />
      <FAQ entries={content.faq} />
      <Inquiry />
      <ContactForm />
      <DemoChat />
    </main>
    <Footer brand={content.brand.name} />
  </div></InquiryProvider>;
}
