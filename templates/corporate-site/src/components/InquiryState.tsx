"use client";
import { createContext, useContext, useState, useEffect, type ReactNode } from "react";
import type { Interest } from "../services/interactions";
import type { SiteContent } from "../content/types";
type Store = { ready: boolean; interest: Interest; content: SiteContent; setPlan: (id: string) => void; toggleService: (title: string) => void; setDomain: (domain: string) => void };
const Context = createContext<Store | null>(null);
export function InquiryProvider({ content, children }: { content: SiteContent; children: ReactNode }) {
  const [ready,setReady]=useState(false);
  useEffect(()=>setReady(true),[]);
  const [interest, set] = useState<Interest>({ planId: "", services: [], domain: "" });
  return <Context.Provider value={{ ready, interest, content,
    setPlan: id => set(v => ({ ...v, planId: content.plans.some(p => p.id === id) ? id : "" })),
    toggleService: title => { if (content.services.some(s => s.title === title)) set(v => ({ ...v, services: v.services.includes(title) ? v.services.filter(s => s !== title) : [...v.services, title] })); },
    setDomain: domain => set(v => ({ ...v, domain })),
  }}>{children}</Context.Provider>;
}
export function useInquiry() { const value = useContext(Context); if (!value) throw new Error("InquiryProvider required"); return value; }
