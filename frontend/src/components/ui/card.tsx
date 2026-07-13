import * as React from "react"

import { cn } from "@/lib/cn"

const Card = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      // VOCABULARY.md §5.1 H1~H4 — 외곽 카드 hover (v2 2026-06-10 lift 강화: 2px → 4px):
      //  ring (외곽선 굵음) + bg-primary/4 (옅은 옥스블러드 tint) + -translate-y-1 (4px lift)
      // 'transition' (Tailwind default, 다중 property) — MOTION M3 (transition-all 회피) 정합
      // Meta 카드 — rounded-card(32px) + flat(shadow-card=none) + hairline. no-hover-lift, 보더 강조만.
      "rounded-card border border-border bg-card text-card-foreground shadow-card transition-colors duration-200 hover:bg-muted/40 hover:ring-1 hover:ring-border",
      className
    )}
    {...props}
  />
))
Card.displayName = "Card"

const CardHeader = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex flex-col space-y-2 p-6", className)}
    {...props}
  />
))
CardHeader.displayName = "CardHeader"

const CardTitle = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      // TYPOGRAPHY.md §5 — Card title default = text-base font-semibold (Section title 결).
      // 큰 글자가 필요한 곳은 호출처에서 className 으로 override (예: Hero 의 text-lg).
      "text-base font-semibold leading-tight tracking-tight",
      className
    )}
    {...props}
  />
))
CardTitle.displayName = "CardTitle"

const CardDescription = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("text-sm text-muted-foreground", className)}
    {...props}
  />
))
CardDescription.displayName = "CardDescription"

const CardContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("p-6 pt-0", className)} {...props} />
))
CardContent.displayName = "CardContent"

const CardFooter = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex items-center p-6 pt-0", className)}
    {...props}
  />
))
CardFooter.displayName = "CardFooter"

export { Card, CardHeader, CardFooter, CardTitle, CardDescription, CardContent }
