"use client";
import { useInquiry } from "./InquiryState";
import s from "./Site.module.css";
export function PlanButton({ id, name }: { id: string; name: string }) {
  const { interest, setPlan } = useInquiry(); const selected = interest.planId === id;
  return <button className={s.button} aria-pressed={selected} onClick={() => setPlan(selected ? "" : id)}>{selected ? `Quitar plan ${name}` : `Seleccionar plan ${name}`}</button>;
}
export function ServiceButton({ title }: { title: string }) {
  const { interest, toggleService } = useInquiry(); const selected = interest.services.includes(title);
  return <button className={s.lightButton} aria-pressed={selected} onClick={() => toggleService(title)}>{selected ? `Quitar servicio ${title}` : `Seleccionar servicio ${title}`}</button>;
}
