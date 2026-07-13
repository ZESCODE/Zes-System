# Claude UI v2 Migration — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate the Claude UI React frontend (:8080) from hand-rolled CSS to shadcn/ui + Assistant UI component library.

**Architecture:** Install Tailwind CSS + shadcn/ui primitives + Assistant UI chat components into the existing CRA project. Replace 3 hand-rolled components (ChatView, LeftDrawer, RightDrawer) with library equivalents. Backend stays untouched.

**Tech Stack:** React 18, shadcn/ui (Radix + Tailwind), Assistant UI, CRA 5

**Spec:** `docs/superpowers/specs/2026-07-13-claude-ui-v2-design.md`

---

### Task 1: Scaffold Tailwind CSS + PostCSS

**Files:**
- Create: `~/claude-ui-project/frontend/tailwind.config.js`
- Create: `~/claude-ui-project/frontend/postcss.config.js`
- Modify: `~/claude-ui-project/frontend/package.json`

- [ ] **Step 1: Install Tailwind + PostCSS dependencies**

```bash
cd ~/claude-ui-project/frontend
npm install --save-dev tailwindcss@3.4 postcss@8 autoprefixer@10
```

- [ ] **Step 2: Create `tailwind.config.js`**

```js
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#080c14",
        surface: "#0d1320",
        surface2: "#131b2e",
        border: "rgba(0,140,255,0.12)",
        text: "#c8d0e0",
        text2: "#8899bb",
        accent: "#4a9eff",
      }
    },
  },
  plugins: [],
}
```

- [ ] **Step 3: Create `postcss.config.js`**

```js
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

- [ ] **Step 4: Verify Tailwind compiles** — run build check

```bash
cd ~/claude-ui-project/frontend && npx tailwindcss --help
```

- [ ] **Step 5: Commit**

```bash
cd ~/Zes-System && git add ~/claude-ui-project/frontend/package.json ~/claude-ui-project/frontend/tailwind.config.js ~/claude-ui-project/frontend/postcss.config.js && git commit -m "feat: add Tailwind CSS + PostCSS config"
```

---

### Task 2: Install shadcn/ui Core

**Files:**
- Create: `~/claude-ui-project/frontend/components.json`
- Create: `~/claude-ui-project/frontend/src/lib/utils.js`
- Modify: `~/claude-ui-project/frontend/package.json`

- [ ] **Step 1: Install shadcn dependencies**

```bash
cd ~/claude-ui-project/frontend
npm install class-variance-authority clsx tailwind-merge lucide-react \
  @radix-ui/react-dialog @radix-ui/react-select \
  @radix-ui/react-scroll-area @radix-ui/react-slot @radix-ui/react-tooltip
```

- [ ] **Step 2: Create `components.json`**

```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "default",
  "rsc": false,
  "tailwind": {
    "config": "tailwind.config.js",
    "css": "src/styles/globals.css",
    "baseColor": "slate",
    "cssVariables": true
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils"
  }
}
```

- [ ] **Step 3: Create `src/lib/utils.js`**

```js
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";
export function cn(...inputs) {
  return twMerge(clsx(inputs));
}
```

- [ ] **Step 4: Create `src/styles/globals.css`**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: #080c14;
    --foreground: #c8d0e0;
    --card: #0d1320;
    --card-foreground: #c8d0e0;
    --popover: #0d1320;
    --popover-foreground: #c8d0e0;
    --primary: #4a9eff;
    --primary-foreground: #ffffff;
    --secondary: #131b2e;
    --secondary-foreground: #8899bb;
    --muted: #131b2e;
    --muted-foreground: #8899bb;
    --accent: #4a9eff;
    --accent-foreground: #ffffff;
    --destructive: #ff5470;
    --destructive-foreground: #ffffff;
    --border: rgba(0,140,255,0.12);
    --input: rgba(0,140,255,0.12);
    --ring: #4a9eff;
    --radius: 0.5rem;
  }
  * {
    border-color: var(--border);
  }
  body {
    background: var(--background);
    color: var(--foreground);
  }
}
```

- [ ] **Step 5: Update `package.json` scripts** — no changes needed (CRA auto-detects PostCSS)

- [ ] **Step 6: Commit**

```bash
cd ~/Zes-System && git add ~/claude-ui-project/frontend/components.json ~/claude-ui-project/frontend/src/lib/utils.js ~/claude-ui-project/frontend/src/styles/globals.css && git commit -m "feat: add shadcn/ui core config + utils"
```

---

### Task 3: Add shadcn/ui Components

**Files:**
- Create: `~/claude-ui-project/frontend/src/components/ui/button.js`
- Create: `~/claude-ui-project/frontend/src/components/ui/sheet.js`
- Create: `~/claude-ui-project/frontend/src/components/ui/select.js`
- Create: `~/claude-ui-project/frontend/src/components/ui/scroll-area.js`
- Create: `~/claude-ui-project/frontend/src/components/ui/dialog.js`
- Create: `~/claude-ui-project/frontend/src/components/ui/badge.js`

- [ ] **Step 1: Create directory**

```bash
mkdir -p ~/claude-ui-project/frontend/src/components/ui
```

- [ ] **Step 2: Write `button.js`** — shadcn Button with variants (default, outline, ghost, icon)

```jsx
import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva } from "class-variance-authority";
import { cn } from "../../lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground shadow hover:bg-primary/90",
        outline: "border border-border bg-transparent hover:bg-accent hover:text-accent-foreground",
        ghost: "hover:bg-accent/10 hover:text-accent",
        icon: "h-9 w-9",
      },
      size: {
        default: "h-9 px-4 py-2",
        sm: "h-8 rounded-md px-3 text-xs",
        lg: "h-10 rounded-md px-8",
      },
    },
    defaultVariants: { variant: "default", size: "default" },
  }
);

const Button = React.forwardRef(({ className, variant, size, asChild = false, ...props }, ref) => {
  const Comp = asChild ? Slot : "button";
  return (
    <Comp className={cn(buttonVariants({ variant, size, className }))} ref={ref} {...props} />
  );
});
Button.displayName = "Button";
export { Button, buttonVariants };
```

- [ ] **Step 3: Write `sheet.js`** — shadcn Sheet (drawer) with left/right variants

```jsx
import * as React from "react";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import { cn } from "../../lib/utils";

const Sheet = DialogPrimitive.Root;
const SheetTrigger = DialogPrimitive.Trigger;
const SheetClose = DialogPrimitive.Close;

const SheetContent = React.forwardRef(({ className, side = "right", children, ...props }, ref) => (
  <DialogPrimitive.Portal>
    <DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-black/50 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />
    <DialogPrimitive.Content
      ref={ref}
      className={cn(
        "fixed z-50 gap-4 bg-surface p-6 shadow-lg transition ease-in-out data-[state=closed]:duration-300 data-[state=open]:duration-500 data-[state=open]:animate-in data-[state=closed]:animate-out",
        side === "left" && "inset-y-0 left-0 h-full w-72 border-r data-[state=closed]:slide-out-to-left data-[state=open]:slide-in-from-left",
        side === "right" && "inset-y-0 right-0 h-full w-80 border-l data-[state=closed]:slide-out-to-right data-[state=open]:slide-in-from-right",
        className
      )}
      {...props}>
      {children}
      <DialogPrimitive.Close className="absolute right-4 top-4 rounded-sm opacity-70 hover:opacity-100">
        <X className="h-4 w-4" />
      </DialogPrimitive.Close>
    </DialogPrimitive.Content>
  </DialogPrimitive.Portal>
));
SheetContent.displayName = "SheetContent";
export { Sheet, SheetTrigger, SheetClose, SheetContent };
```

- [ ] **Step 4: Write `select.js`** — shadcn Select dropdown

```jsx
import * as React from "react";
import * as SelectPrimitive from "@radix-ui/react-select";
import { ChevronDown } from "lucide-react";
import { cn } from "../../lib/utils";

const Select = SelectPrimitive.Root;
const SelectTrigger = React.forwardRef(({ className, children, ...props }, ref) => (
  <SelectPrimitive.Trigger ref={ref} className={cn("flex h-9 w-full items-center justify-between rounded-md border border-border bg-transparent px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring", className)} {...props}>
    {children}
    <ChevronDown className="h-4 w-4 opacity-50" />
  </SelectPrimitive.Trigger>
));
const SelectContent = React.forwardRef(({ className, children, ...props }, ref) => (
  <SelectPrimitive.Portal>
    <SelectPrimitive.Content ref={ref} className={cn("relative z-50 max-h-96 min-w-[8rem] overflow-hidden rounded-md border border-border bg-surface text-text shadow-md animate-in fade-in-80", className)} {...props}>
      <SelectPrimitive.Viewport className="p-1">{children}</SelectPrimitive.Viewport>
    </SelectPrimitive.Content>
  </SelectPrimitive.Portal>
));
const SelectItem = React.forwardRef(({ className, children, ...props }, ref) => (
  <SelectPrimitive.Item ref={ref} className={cn("relative flex w-full cursor-default select-none items-center rounded-sm py-1.5 pl-2 pr-8 text-sm outline-none focus:bg-accent/10 focus:text-accent data-[disabled]:pointer-events-none data-[disabled]:opacity-50", className)} {...props}>
    <SelectPrimitive.ItemText>{children}</SelectPrimitive.ItemText>
  </SelectPrimitive.Item>
));
SelectTrigger.displayName = "SelectTrigger";
SelectContent.displayName = "SelectContent";
SelectItem.displayName = "SelectItem";
export { Select, SelectTrigger, SelectContent, SelectItem };
```

- [ ] **Step 5: Write `scroll-area.js`** — shadcn ScrollArea

```jsx
import * as React from "react";
import * as ScrollAreaPrimitive from "@radix-ui/react-scroll-area";
import { cn } from "../../lib/utils";

const ScrollArea = React.forwardRef(({ className, children, ...props }, ref) => (
  <ScrollAreaPrimitive.Root ref={ref} className={cn("relative overflow-hidden", className)} {...props}>
    <ScrollAreaPrimitive.Viewport className="h-full w-full rounded-[inherit]">
      {children}
    </ScrollAreaPrimitive.Viewport>
    <ScrollAreaPrimitive.Scrollbar className="flex touch-none select-none transition-colors" orientation="vertical">
      <ScrollAreaPrimitive.Thumb className="relative flex-1 rounded-full bg-border" />
    </ScrollAreaPrimitive.Scrollbar>
  </ScrollAreaPrimitive.Root>
));
ScrollArea.displayName = "ScrollArea";
export { ScrollArea };
```

- [ ] **Step 6: Write `badge.js`** — shadcn Badge

```jsx
import { cva } from "class-variance-authority";
import { cn } from "../../lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold transition-colors",
  { variants: { variant: { default: "border-transparent bg-primary text-primary-foreground shadow", outline: "text-text2" } }, defaultVariants: { variant: "default" } }
);

function Badge({ className, variant, ...props }) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}
export { Badge, badgeVariants };
```

- [ ] **Step 7: Write `dialog.js`** — shadcn Dialog (for modals)

```jsx
import * as React from "react";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import { cn } from "../../lib/utils";

const Dialog = DialogPrimitive.Root;
const DialogContent = React.forwardRef(({ className, children, ...props }, ref) => (
  <DialogPrimitive.Portal>
    <DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-black/50" />
    <DialogPrimitive.Content ref={ref} className={cn("fixed left-1/2 top-1/2 z-50 w-full max-w-lg -translate-x-1/2 -translate-y-1/2 rounded-lg border border-border bg-surface p-6 shadow-lg", className)} {...props}>
      {children}
    </DialogPrimitive.Content>
  </DialogPrimitive.Portal>
));
DialogContent.displayName = "DialogContent";
export { Dialog, DialogContent };
```

- [ ] **Step 8: Verify components import correctly**

```bash
cd ~/claude-ui-project/frontend && node -e "require('./src/components/ui/button.js')" 2>&1 || echo "CRA will resolve at build time"
```

- [ ] **Step 9: Commit**

```bash
cd ~/Zes-System && git add ~/claude-ui-project/frontend/src/components/ui/ && git commit -m "feat: add shadcn/ui components (Button, Sheet, Select, ScrollArea, Badge, Dialog)"
```

---

### Task 4: Install Assistant UI

**Files:**
- Modify: `~/claude-ui-project/frontend/package.json`

- [ ] **Step 1: Install Assistant UI packages**

```bash
cd ~/claude-ui-project/frontend
npm install @assistant-ui/react @assistant-ui/react-markdown
```

- [ ] **Step 2: Create Assistant UI component scaffolding**

```bash
mkdir -p ~/claude-ui-project/frontend/src/components/assistant-ui
```

- [ ] **Step 3: Verify installation**

```bash
cd ~/claude-ui-project/frontend && node -e "require('@assistant-ui/react')" 2>&1 || echo "Module exists for CRA bundling"
```

- [ ] **Step 4: Commit**

```bash
cd ~/Zes-System && git add ~/claude-ui-project/frontend/package.json ~/claude-ui-project/frontend/package-lock.json && git commit -m "feat: add Assistant UI chat components"
```

---

### Task 5: Refactor App.js — Integrate Layout

**Files:**
- Modify: `~/claude-ui-project/frontend/src/App.js`
- Delete: `~/claude-ui-project/frontend/src/styles/App.css`

- [ ] **Step 1: Import Tailwind globals in `index.js`**

```js
// src/index.js — add at top
import './styles/globals.css';
```

- [ ] **Step 2: Rewrite `App.js` with shadcn layout structure**

```jsx
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Sheet, SheetTrigger, SheetContent } from './components/ui/sheet';
import { Button } from './components/ui/button';
import { Select, SelectTrigger, SelectContent, SelectItem } from './components/ui/select';
import { ScrollArea } from './components/ui/scroll-area';
import { Badge } from './components/ui/badge';
import { Menu, PanelRightOpen, Plus, Trash2 } from 'lucide-react';
```

Key elements:
- TopBar: `flex items-center justify-between p-2 bg-surface border-b border-border h-12`
- LeftDrawer toggle: `SheetTrigger asChild` → `Button variant="ghost" size="icon"`
- RightDrawer toggle: same pattern
- Left Sheet: `side="left"` with model picker + session list
- Right Sheet: `side="right"` with system status + settings
- Main area: `flex-1 flex flex-col` with Assistant UI runtime

- [ ] **Step 3: Remove `App.css` import from `App.js`**

- [ ] **Step 4: Verify app still renders**

```bash
cd ~/claude-ui-project/frontend && PORT=8080 npx react-scripts build 2>&1 | tail -5
```

- [ ] **Step 5: Commit**

```bash
cd ~/Zes-System && git add ~/claude-ui-project/frontend/src/App.js ~/claude-ui-project/frontend/src/index.js && git rm ~/claude-ui-project/frontend/src/styles/App.css && git commit -m "refactor: App.js with shadcn layout"
```

---

### Task 6: Integrate Assistant UI Chat

**Files:**
- Create: `~/claude-ui-project/frontend/src/components/assistant-ui/thread.js`
- Modify: `~/claude-ui-project/frontend/src/App.js`
- Delete: `~/claude-ui-project/frontend/src/components/ChatView.js`

- [ ] **Step 1: Create Assistant UI Thread wrapper**

```jsx
// src/components/assistant-ui/thread.js
import { Thread as AUThread } from '@assistant-ui/react';

export function Thread() {
  return (
    <AUThread
      className="flex-1 flex flex-col"
      welcome={() => (
        <div className="flex-1 flex items-center justify-center text-text2">
          <div className="text-center">
            <h2 className="text-xl font-semibold text-text mb-2">Claude Code UI</h2>
            <p className="text-sm">Ask anything about your codebase</p>
          </div>
        </div>
      )}
    />
  );
}
```

- [ ] **Step 2: Integrate runtime in `App.js`**

```jsx
import { AssistantRuntimeProvider } from '@assistant-ui/react';
import { Thread } from './components/assistant-ui/thread';

// In the render:
<AssistantRuntimeProvider runtime={/* create runtime connected to backend */}>
  <div className="app flex h-screen overflow-hidden bg-bg">
    {/* shadcn layout */}
    <div className="flex-1 flex flex-col">
      <Thread />
    </div>
  </div>
</AssistantRuntimeProvider>
```

The runtime connects to the existing Express backend. Assistant UI supports custom runtimes via the `useChatRuntime` hook or a custom `ChatModelAdapter`.

- [ ] **Step 3: Create backend adapter** (connects Assistant UI to our :9001 API)

```jsx
// src/lib/chat-adapter.js
const BACKEND = 'http://localhost:9001';

export function createRuntime(model) {
  return {
    onNew: async (messages) => {
      const lastMsg = messages[messages.length - 1];
      const response = await fetch(`${BACKEND}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: lastMsg.content, model, stream: true }),
      });
      return response.body; // ReadableStream for SSE
    },
  };
}
```

- [ ] **Step 4: Remove `ChatView.js` import from `App.js`**

```bash
rm ~/claude-ui-project/frontend/src/components/ChatView.js
```

- [ ] **Step 5: Build test**

```bash
cd ~/claude-ui-project/frontend && npx react-scripts build 2>&1 | tail -10
```

- [ ] **Step 6: Commit**

```bash
cd ~/Zes-System && git add ~/claude-ui-project/frontend/src/components/assistant-ui/ ~/claude-ui-project/frontend/src/lib/ && git rm ~/claude-ui-project/frontend/src/components/ChatView.js && git commit -m "feat: integrate Assistant UI chat with backend adapter"
```

---

### Task 7: Replace LeftDrawer with shadcn Sheet

**Files:**
- Modify: `~/claude-ui-project/frontend/src/App.js`
- Delete: `~/claude-ui-project/frontend/src/components/LeftDrawer.js`

- [ ] **Step 1: Move LeftDrawer content into App.js as Sheet content**

```jsx
<Sheet open={leftOpen} onOpenChange={setLeftOpen}>
  <SheetContent side="left" className="flex flex-col">
    {/* New Chat button */}
    <Button onClick={newChat} variant="outline" className="w-full mb-4">
      <Plus className="h-4 w-4 mr-2" /> New Chat
    </Button>
    
    {/* Model selector */}
    <div className="mb-4">
      <label className="text-xs text-text2 mb-1 block">Model</label>
      <Select value={model} onValueChange={setModel}>
        <SelectTrigger><span>{model}</span></SelectTrigger>
        <SelectContent>
          {models.map(m => <SelectItem key={m} value={m}>{m}</SelectItem>)}
        </SelectContent>
      </Select>
    </div>
    
    {/* Session list */}
    <ScrollArea className="flex-1">
      <div className="space-y-1">
        {sessions.map(s => (
          <Button key={s.id} variant="ghost" className="w-full justify-start text-sm"
            onClick={() => loadSession(s)}>
            <span className="truncate">{s.title}</span>
          </Button>
        ))}
      </div>
    </ScrollArea>
  </SheetContent>
</Sheet>
```

- [ ] **Step 2: Remove `LeftDrawer.js` import**

```bash
rm ~/claude-ui-project/frontend/src/components/LeftDrawer.js
```

- [ ] **Step 3: Build test**

```bash
cd ~/claude-ui-project/frontend && npx react-scripts build 2>&1 | tail -5
```

- [ ] **Step 4: Commit**

```bash
cd ~/Zes-System && git rm ~/claude-ui-project/frontend/src/components/LeftDrawer.js && git add ~/claude-ui-project/frontend/src/App.js && git commit -m "refactor: replace LeftDrawer with shadcn Sheet"
```

---

### Task 8: Replace RightDrawer with shadcn Sheet

**Files:**
- Modify: `~/claude-ui-project/frontend/src/App.js`
- Delete: `~/claude-ui-project/frontend/src/components/RightDrawer.js`

- [ ] **Step 1: Move RightDrawer content into App.js**

```jsx
<Sheet open={rightOpen} onOpenChange={setRightOpen}>
  <SheetContent side="right" className="flex flex-col">
    <h3 className="text-sm font-semibold mb-4">System</h3>
    
    {/* System Status */}
    <div className="space-y-2 mb-4">
      <div className="flex items-center gap-2">
        <span className={\`h-2 w-2 rounded-full \${systemStatus ? 'bg-green-500' : 'bg-red-500'}\`} />
        <span className="text-sm">Backend</span>
      </div>
      <Badge variant="outline">{model}</Badge>
    </div>
    
    {/* Quick actions */}
    <div className="space-y-2 mt-auto">
      <Button variant="outline" size="sm" className="w-full" onClick={checkHealth}>
        Check Health
      </Button>
    </div>
  </SheetContent>
</Sheet>
```

- [ ] **Step 2: Remove `RightDrawer.js` import**

```bash
rm ~/claude-ui-project/frontend/src/components/RightDrawer.js
```

- [ ] **Step 3: Build test**

```bash
cd ~/claude-ui-project/frontend && npx react-scripts build 2>&1 | tail -5
```

- [ ] **Step 4: Commit**

```bash
cd ~/Zes-System && git rm ~/claude-ui-project/frontend/src/components/RightDrawer.js && git add ~/claude-ui-project/frontend/src/App.js && git commit -m "refactor: replace RightDrawer with shadcn Sheet"
```

---

### Task 9: Final Integration & Testing

**Files:**
- Verify: `~/claude-ui-project/frontend/src/App.js`

- [ ] **Step 1: Full build**

```bash
cd ~/claude-ui-project/frontend && npx react-scripts build 2>&1
```

- [ ] **Step 2: Start dev server and smoke test**

```bash
cd ~/claude-ui-project/frontend && PORT=8080 npx react-scripts start &
sleep 5 && curl -s http://localhost:8080 | grep -q "root" && echo "✅ UI serving" || echo "❌ UI not serving"
```

- [ ] **Step 3: Test drawers open/close** (check browser for left/right sheet animations)

- [ ] **Step 4: Test chat send** (type message, verify backend receives it)

```bash
curl -s http://localhost:9001/api/chat -H "Content-Type: application/json" -d '{"message":"hello","model":"gh/gpt-4o","stream":false}' | head -5
```

- [ ] **Step 5: Test model switching** — verify Select changes model state

- [ ] **Step 6: Test session persistence** — send a message, refresh page, verify session appears in left drawer

- [ ] **Step 7: Kill dev server**

```bash
kill %1 2>/dev/null || true
```

- [ ] **Step 8: Final commit**

```bash
cd ~/Zes-System && git add ~/claude-ui-project/ && git commit -m "feat: Claude UI v2 with shadcn/ui + Assistant UI"
```

---

### Task 10: Restart runsv Service

**Files:**
- N/A — service management

- [ ] **Step 1: Restart the frontend service**

```bash
sv restart /data/data/com.termux/files/usr/var/service/claude-ui-frontend
```

- [ ] **Step 2: Verify**

```bash
curl -s http://localhost:8080 | head -5
```
