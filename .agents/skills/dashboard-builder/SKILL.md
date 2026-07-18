---
category: Frontend

name: dashboard-builder
description: "Build production dashboards with React 19 + shadcn/ui + Tailwind CSS v4 + Vite 8 + Lucide Icons. Use when creating new dashboard UIs, adding dashboard pages (kanban, chat, system monitor, service grid), or implementing mobile-responsive layouts with bottom navigation. Covers the full stack: setup, hash-based routing, mobile optimization, shadcn primitives, data-fetching hooks, and all component patterns (kanban board with drag-and-drop, chat interface, service grid with controls, theme designer, iframe pages, summary cards, process lists, system info, network info, web service cards)."
---


# Dashboard Builder

Build production dashboards with React 19 + shadcn/ui + Tailwind CSS v4 + Vite 8.

## Quick Start

```bash
npm create vite@latest my-dash -- --template react
cd my-dash
npm install react react-dom lucide-react class-variance-authority clsx tailwind-merge
npm install -D vite @vitejs/plugin-react tailwindcss @tailwindcss/vite
```

Then copy the shadcn primitive components into `src/components/ui/` from a reference project.

## Vite Config

```js
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "path";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: { alias: { "@": path.resolve(__dirname, "./src") } },
  server: {
    port: 5173,
    host: "127.0.0.1",
    watch: { usePolling: true, interval: 1000 },
    proxy: { "/api": { target: "http://localhost:5002", changeOrigin: true } },
  },
});
```

## Architecture Pattern

### Hash-Based Routing (no react-router)

Use `window.location.hash` for tab state.

```jsx
const VALID_TABS = ["overview", "services", "kanban", "settings"];

function DashboardLayout() {
  const [activeTab, setActiveTab] = useState(() => {
    const hash = window.location.hash.slice(1);
    return VALID_TABS.includes(hash) ? hash : "overview";
  });

  const handleTabChange = useCallback((tab) => {
    setActiveTab(tab);
    window.location.hash = tab;
  }, []);

  useEffect(() => {
    const onHashChange = () => {
      const hash = window.location.hash.slice(1);
      if (VALID_TABS.includes(hash) && hash !== activeTab) setActiveTab(hash);
    };
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, [activeTab]);
}
```

### Tab to Component Map

```jsx
const tabs = {
  overview: { title: "Overview", component: SummaryCards },
  services: { title: "Services", component: ServiceGrid },
  kanban:   { title: "Kanban",  component: KanbanBoard, noPadding: true },
};
```

## Mobile Optimization

### Desktop to Mobile Switching

```jsx
const [isMobile, setIsMobile] = useState(false);
useEffect(() => {
  const check = () => setIsMobile(window.innerWidth < 768);
  check();
  window.addEventListener("resize", check);
  return () => window.removeEventListener("resize", check);
}, []);

if (isMobile) {
  return (
    <div className="flex flex-col h-screen bg-background">
      <main className="flex-1 overflow-auto p-3 pb-20">
        <Content />
      </main>
      <MobileNav activeTab={activeTab} onTabChange={handleTabChange} />
    </div>
  );
}
return (
  <div className="flex h-screen bg-background">
    <Sidebar ... />
    <main className="flex-1 overflow-auto p-6">
      <Content />
    </main>
  </div>
);
```

### Mobile Bottom Nav

```jsx
export function MobileNav({ activeTab, onTabChange }) {
  return (
    <nav className="fixed bottom-0 z-40 border-t bg-background md:hidden">
      <div className="flex justify-around items-center h-14 px-1 overflow-x-auto">
        {ITEMS.map((item) => (
          <button key={item.id} onClick={() => onTabChange(item.id)}
            className={cn("flex flex-col items-center gap-0.5 px-2 py-1.5",
              activeTab === item.id ? "text-primary" : "text-muted-foreground"
            )}>
            <Icon className="h-5 w-5" />
            <span className="text-[9px] font-medium">{item.label}</span>
          </button>
        ))}
      </div>
    </nav>
  );
}
```

### Responsive CSS Patterns

```jsx
<div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 md:gap-4" />
<CardHeader className="px-3 pt-3 md:px-6 md:pt-6" />
<CardTitle className="text-xs md:text-sm" />
```

## shadcn/ui Primitives

Copy into `src/components/ui/`:

- **button.jsx** - cva() with: default, secondary, ghost, destructive, outline, link
- **card.jsx** - Card, CardHeader, CardTitle, CardContent, CardFooter
- **tabs.jsx** - Radix Tabs (TabsList, TabsTrigger, TabsContent)
- **sheet.jsx** - Radix Dialog (slide-in panel)
- **separator.jsx** - Radix Separator
- **badge.jsx** - default, secondary, outline, destructive
- **skeleton.jsx** - Loading placeholder
- **input.jsx** - Styled input

### cn() Utility

```js
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";
export function cn(...inputs) { return twMerge(clsx(inputs)); }
```

## Data Fetching Pattern

```js
export function useServices() {
  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(true);
  const fetch = async () => {
    try {
      const res = await fetch("/api/services");
      setServices(await res.json());
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };
  useEffect(() => {
    fetch();
    const interval = setInterval(fetch, 5000);
    return () => clearInterval(interval);
  }, []);
  return { services, loading, controlService: async (name, action) => {
    await fetch(`/api/services/${name}/${action}`, { method: "POST" });
    await fetch();
  }};
}
```

## Component Reference

- **SummaryCards** - 4 stats cards: Services, Memory, CPU, Uptime. Grid: 2/3/4 cols. Polls `GET /api/summary`
- **ServiceGrid + ServiceCard** - 3-col grid. Status badge + start/stop/restart. Polls 5s. `POST /api/services/:name/:action`
- **ProcessList** - Top processes table. `GET /api/processes`
- **SystemInfo** - 2 cols: system details + memory/disk. `GET /api/system`
- **WebServices** - URL cards with online badge. `GET /api/web-services`
- **NetworkInfo** - Interface list. `GET /api/network`
- **IFramePage** - Generic iframe embed with URL bar + external link
- **HermesChat** - Full chat: sessions sidebar, messages, auto-resize input
- **DesignStudio** - Theme designer: color pickers, preview, CSS export
- **KanbanBoard** - 8-column workflow, native HTML5 DnD, mobile list view

### Data Flow

```
Component -> custom hook -> fetch(/api/...) -> setState -> render
                        <-> polling every 5-30s
                 user action -> POST /api/... -> refetch
```

## Termux Notes

- `usePolling: true` in vite.config.js to avoid ENOSPC
- No Docker, no shadcn CLI, no React Query
- Use `setsid` to persist background processes
- `pb-20` on main content to prevent bottom nav overlap

## Build

```bash
npx vite --port 5173 --host 127.0.0.1   # dev
npm run build                              # production -> dist/
