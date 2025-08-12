# React Dashboard Integration - Complete Rebuild Guide

## Overview
This guide provides the complete process to rebuild the React + Vite + TypeScript + Tailwind dashboard preview integration with the Flask MediFly application, including all critical fixes for proper functionality.

## Phase 1: Initial Setup

### 1. Create React Application Structure
```bash
# Create the dashboard sandbox directory
mkdir medifly-dashboard-sandbox
cd medifly-dashboard-sandbox

# Initialize with package.json
npm init -y
```

### 2. Install Dependencies
```bash
# Core React dependencies
npm install react react-dom react-router-dom

# Development dependencies  
npm install -D @types/react @types/react-dom @vitejs/plugin-react typescript vite

# Tailwind CSS setup
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

### 3. Configure Package.json Scripts
```json
{
  "name": "medifly-dashboard-sandbox",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "preview": "vite preview"
  }
}
```

## Phase 2: Core Configuration Files

### 4. TypeScript Configuration (tsconfig.json)
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

### 5. Vite Configuration (vite.config.ts)
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
    assetsDir: 'assets'
  }
})
```

### 6. Tailwind Configuration (tailwind.config.js)
```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

### 7. PostCSS Configuration (postcss.config.js)
```javascript
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

## Phase 3: React Application Structure

### 8. HTML Entry Point (index.html)
```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>MediFly Dashboard Preview</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

### 9. Main Entry (src/main.tsx)
```typescript
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
```

### 10. Global Styles (src/index.css)
```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

### 11. App Component (src/App.tsx)
```typescript
import { RouterProvider } from 'react-router-dom';
import { router } from './router';

function App() {
  return <RouterProvider router={router} />;
}

export default App;
```

### 12. Router Configuration (src/router.tsx) - CRITICAL FLASK INTEGRATION FIX
```typescript
import { createBrowserRouter } from 'react-router-dom';
import Home from './pages/Home';
import PhaseOne from './pages/PhaseOne';

export const router = createBrowserRouter([
  {
    path: '/dashboard-preview',
    element: <Home />,
  },
  {
    path: '/dashboard-preview/phase-1',
    element: <PhaseOne />,
  },
  {
    path: '/',
    element: <Home />,
  },
  {
    path: '/phase-1',
    element: <PhaseOne />,
  },
]);
```
**Key Fix:** Routes MUST include `/dashboard-preview` paths to match Flask integration.

## Phase 4: Data Types and Structures

### 13. TypeScript Types (src/data/types.ts)
```typescript
export interface QuoteData {
  id: string;
  provider: string;
  price: string;
  estimatedTime: string;
  aircraftType: string;
  capabilities: string[];
  certifications: string[];
  priority?: boolean;
  incentive?: string;
}

export type UserRole = 'Affiliate' | 'Provider' | 'Individual';

export interface FilterState {
  search: string;
  timeRange: string;
  priceRange: string;
  aircraftType: string;
  capabilities: string[];
}
```

### 14. Sample Data (src/data/sampleData.ts)
```typescript
import { QuoteData } from './types';

export const affiliateQuotes: QuoteData[] = [
  {
    id: 'A001',
    provider: 'AirMed Partners',
    price: '$12,500',
    estimatedTime: '45 mins',
    aircraftType: 'Helicopter',
    capabilities: ['ICU', 'Ventilator', 'ECMO'],
    certifications: ['CAMTS', 'EURAMI'],
    priority: true,
    incentive: 'Priority Partner - 5% bonus'
  },
  // Add more sample data...
];

export const providerQuotes: QuoteData[] = [
  // Provider-specific data...
];

export const individualQuotes: QuoteData[] = [
  // Individual-specific data...
];
```

## Phase 5: React Components

### 15. Home Page (src/pages/Home.tsx)
```typescript
import { Link } from 'react-router-dom';

export default function Home() {
  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <header className="text-center mb-8">
          <h1 className="text-4xl font-bold text-blue-600 mb-4">
            MediFly Dashboard Preview
          </h1>
          <p className="text-gray-600 text-lg">
            Phase 1 demonstration of the MediFly dashboard interface
          </p>
        </header>
        
        <div className="bg-white rounded-lg shadow-md p-6 text-center">
          <h2 className="text-2xl font-semibold mb-4">Ready to explore?</h2>
          <p className="text-gray-600 mb-6">
            Experience the split-screen interface with role-based data switching
          </p>
          <Link
            to="/dashboard-preview/phase-1"
            className="inline-block bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Test Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}
```

### 16. Phase One Dashboard (src/pages/PhaseOne.tsx)
```typescript
import { useState } from 'react';
import DashboardFull from '../components/DashboardFull';
import DashboardSimplified from '../components/DashboardSimplified';
import { UserRole } from '../data/types';

export default function PhaseOne() {
  const [currentRole, setCurrentRole] = useState<UserRole>('Affiliate');

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header with role toggle */}
      <header className="bg-white border-b border-gray-200 p-4">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-bold text-blue-600">MediFly Dashboard - Phase 1</h1>
          
          <div className="flex items-center space-x-4">
            <label className="text-sm font-medium text-gray-700">View as:</label>
            <select
              value={currentRole}
              onChange={(e) => setCurrentRole(e.target.value as UserRole)}
              className="border border-gray-300 rounded-md px-3 py-2 text-sm"
            >
              <option value="Affiliate">Affiliate</option>
              <option value="Provider">Provider</option>
              <option value="Individual">Individual</option>
            </select>
          </div>
        </div>
      </header>

      {/* Split-screen layout */}
      <div className="flex h-screen">
        <div className="w-1/2 border-r border-gray-200">
          <DashboardFull role={currentRole} />
        </div>
        <div className="w-1/2">
          <DashboardSimplified role={currentRole} />
        </div>
      </div>
    </div>
  );
}
```

### 17. Full Dashboard Component (src/components/DashboardFull.tsx)
```typescript
import { useState, useEffect } from 'react';
import { UserRole, QuoteData, FilterState } from '../data/types';
import { affiliateQuotes, providerQuotes, individualQuotes } from '../data/sampleData';

interface DashboardFullProps {
  role: UserRole;
}

export default function DashboardFull({ role }: DashboardFullProps) {
  const [quotes, setQuotes] = useState<QuoteData[]>([]);
  const [filteredQuotes, setFilteredQuotes] = useState<QuoteData[]>([]);
  const [filters, setFilters] = useState<FilterState>({
    search: '',
    timeRange: 'all',
    priceRange: 'all',
    aircraftType: 'all',
    capabilities: []
  });
  const [showAcceptModal, setShowAcceptModal] = useState(false);
  const [selectedQuote, setSelectedQuote] = useState<QuoteData | null>(null);

  useEffect(() => {
    // Load data based on role
    switch (role) {
      case 'Affiliate':
        setQuotes(affiliateQuotes);
        break;
      case 'Provider':
        setQuotes(providerQuotes);
        break;
      case 'Individual':
        setQuotes(individualQuotes);
        break;
    }
  }, [role]);

  const handleAccept = (quote: QuoteData) => {
    setSelectedQuote(quote);
    setShowAcceptModal(true);
  };

  const confirmAccept = () => {
    if (selectedQuote) {
      // Show toast notification
      const toast = document.createElement('div');
      toast.className = 'fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-50';
      toast.textContent = `Quote ${selectedQuote.id} accepted successfully!`;
      document.body.appendChild(toast);
      
      setTimeout(() => {
        document.body.removeChild(toast);
      }, 3000);
    }
    setShowAcceptModal(false);
    setSelectedQuote(null);
  };

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 bg-blue-50">
        <h2 className="text-xl font-semibold text-blue-800">
          Full View Dashboard ({role})
        </h2>
        <p className="text-sm text-blue-600">
          Advanced filtering and detailed quote management
        </p>
      </div>

      {/* Filters */}
      <div className="p-4 border-b border-gray-200 bg-gray-50">
        <div className="grid grid-cols-2 gap-4">
          <input
            type="text"
            placeholder="Search quotes..."
            value={filters.search}
            onChange={(e) => setFilters({...filters, search: e.target.value})}
            className="border border-gray-300 rounded-md px-3 py-2 text-sm"
          />
          <select
            value={filters.timeRange}
            onChange={(e) => setFilters({...filters, timeRange: e.target.value})}
            className="border border-gray-300 rounded-md px-3 py-2 text-sm"
          >
            <option value="all">All Time</option>
            <option value="today">Today</option>
            <option value="week">This Week</option>
            <option value="month">This Month</option>
          </select>
        </div>
      </div>

      {/* Quotes List */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="space-y-4">
          {quotes.map((quote) => (
            <div key={quote.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <h3 className="font-semibold text-lg">{quote.provider}</h3>
                  <p className="text-2xl font-bold text-green-600">{quote.price}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-600">ETA: {quote.estimatedTime}</p>
                  <p className="text-sm font-medium">{quote.aircraftType}</p>
                </div>
              </div>
              
              <div className="mb-3">
                <div className="flex flex-wrap gap-2 mb-2">
                  {quote.capabilities.map((cap) => (
                    <span key={cap} className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
                      {cap}
                    </span>
                  ))}
                </div>
                <div className="flex flex-wrap gap-2">
                  {quote.certifications.map((cert) => (
                    <span key={cert} className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded">
                      {cert}
                    </span>
                  ))}
                </div>
              </div>

              {quote.incentive && (
                <div className="bg-yellow-50 border border-yellow-200 rounded p-2 mb-3">
                  <p className="text-yellow-800 text-sm font-medium">{quote.incentive}</p>
                </div>
              )}

              <div className="flex justify-between items-center">
                <button
                  onClick={() => handleAccept(quote)}
                  className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition-colors"
                >
                  Accept Quote
                </button>
                <button className="text-blue-600 hover:text-blue-800 text-sm">
                  View Details
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Accept Modal */}
      {showAcceptModal && selectedQuote && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">Confirm Quote Acceptance</h3>
            <p className="text-gray-600 mb-4">
              Are you sure you want to accept the quote from {selectedQuote.provider} for {selectedQuote.price}?
            </p>
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowAcceptModal(false)}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
              >
                Cancel
              </button>
              <button
                onClick={confirmAccept}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Confirm Accept
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
```

### 18. Simplified Dashboard Component (src/components/DashboardSimplified.tsx)
```typescript
import { useState, useEffect } from 'react';
import { UserRole, QuoteData } from '../data/types';
import { affiliateQuotes, providerQuotes, individualQuotes } from '../data/sampleData';

interface DashboardSimplifiedProps {
  role: UserRole;
}

export default function DashboardSimplified({ role }: DashboardSimplifiedProps) {
  const [quotes, setQuotes] = useState<QuoteData[]>([]);

  useEffect(() => {
    switch (role) {
      case 'Affiliate':
        setQuotes(affiliateQuotes.slice(0, 3)); // Show fewer items
        break;
      case 'Provider':
        setQuotes(providerQuotes.slice(0, 3));
        break;
      case 'Individual':
        setQuotes(individualQuotes.slice(0, 3));
        break;
    }
  }, [role]);

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 bg-green-50">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-xl font-semibold text-green-800">
              Simplified View ({role})
            </h2>
            <p className="text-sm text-green-600">
              Streamlined interface for quick decisions
            </p>
          </div>
          <button
            onClick={handlePrint}
            className="bg-green-600 text-white px-3 py-2 rounded text-sm hover:bg-green-700"
          >
            Print
          </button>
        </div>
      </div>

      {/* Simplified Quotes */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="space-y-3">
          {quotes.map((quote) => (
            <div key={quote.id} className="border border-gray-200 rounded-lg p-3 bg-gray-50">
              <div className="flex justify-between items-center mb-2">
                <h3 className="font-medium">{quote.provider}</h3>
                <span className="text-lg font-bold text-green-600">{quote.price}</span>
              </div>
              <div className="flex justify-between items-center text-sm text-gray-600 mb-2">
                <span>ETA: {quote.estimatedTime}</span>
                <span>{quote.aircraftType}</span>
              </div>
              <button className="w-full bg-green-600 text-white py-2 rounded hover:bg-green-700 transition-colors">
                Quick Accept
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
```

## Phase 6: Flask Integration - CRITICAL FIXES

### 19. Flask Routes (Add to consumer_main_final.py)
```python
import os
from flask import send_file
import logging

# Dashboard Preview Routes
@consumer_app.route('/dashboard-preview')
def dashboard_preview():
    """Serve the React dashboard preview application"""
    try:
        # Serve the built React app's index.html with corrected asset paths
        dashboard_path = os.path.join(os.getcwd(), 'medifly-dashboard-sandbox', 'dist', 'index.html')
        if os.path.exists(dashboard_path):
            with open(dashboard_path, 'r') as f:
                content = f.read()
            # Fix asset paths to work with Flask routing
            content = content.replace('src="/assets/', 'src="/dashboard-preview/assets/')
            content = content.replace('href="/assets/', 'href="/dashboard-preview/assets/')
            return content
        else:
            return f"""
            <div style="padding: 2rem; text-align: center; font-family: system-ui;">
                <h2>Dashboard Preview Not Available</h2>
                <p>The React dashboard preview application needs to be built first.</p>
                <p>Location checked: {dashboard_path}</p>
                <a href="/" style="padding: 0.5rem 1rem; background: #007bff; color: white; text-decoration: none; border-radius: 5px;">Return to Home</a>
            </div>
            """
    except Exception as e:
        return f"""
        <div style="padding: 2rem; text-align: center; font-family: system-ui;">
            <h2>Error Loading Dashboard Preview</h2>
            <p>Error: {str(e)}</p>
            <a href="/" style="padding: 0.5rem 1rem; background: #007bff; color: white; text-decoration: none; border-radius: 5px;">Return to Home</a>
        </div>
        """

@consumer_app.route('/dashboard-preview/assets/<path:filename>')
def dashboard_assets(filename):
    """Serve React dashboard assets"""
    try:
        assets_path = os.path.join(os.getcwd(), 'medifly-dashboard-sandbox', 'dist', 'assets')
        file_path = os.path.join(assets_path, filename)
        if os.path.exists(file_path):
            return send_file(file_path)
        else:
            return f"Asset not found: {filename}", 404
    except Exception as e:
        logging.error(f"Error serving asset {filename}: {e}")
        return f"Error serving asset: {e}", 500
```

### 20. Test Dashboard Button (Add to Flask template)
```html
<!-- Add this button to your main Flask template -->
<a href="/dashboard-preview" 
   class="btn btn-info mb-3" 
   target="_blank" 
   style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border: none;">
    <i class="fas fa-chart-line me-2"></i>Test Dashboard
</a>
```

## Phase 7: Build and Deployment

### 21. Build the React Application
```bash
cd medifly-dashboard-sandbox
npm run build
```

### 22. Verify Integration
1. Start Flask application: `gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app`
2. Test dashboard button in Flask app
3. Verify `/dashboard-preview` loads React home page
4. Test navigation to `/dashboard-preview/phase-1`
5. Test role switching functionality
6. Test Accept buttons and modals
7. Test print functionality

## Critical Fixes Summary

### Fix 1: React Router Configuration
- **Problem**: React Router routes didn't match Flask paths
- **Solution**: Added `/dashboard-preview` and `/dashboard-preview/phase-1` routes alongside original routes

### Fix 2: Asset Path Correction
- **Problem**: Built HTML referenced `/assets/` which Flask couldn't serve
- **Solution**: Python string replacement to rewrite paths to `/dashboard-preview/assets/`

### Fix 3: Flask Asset Serving
- **Problem**: React assets not accessible through Flask
- **Solution**: Added `/dashboard-preview/assets/<path:filename>` route with proper file serving

### Fix 4: Error Handling
- **Problem**: Missing error states for missing files
- **Solution**: Added comprehensive try-catch blocks with user-friendly error messages

## Testing Checklist

- [ ] React app builds without errors
- [ ] Dashboard button opens `/dashboard-preview` route
- [ ] Home page displays with proper styling
- [ ] "Test Dashboard" button navigates to Phase 1
- [ ] Split-screen layout renders correctly
- [ ] Role toggle switches data sets
- [ ] Accept buttons trigger modals
- [ ] Modal confirmation shows toast notifications
- [ ] Print button functions (window.print)
- [ ] All assets load without 404 errors
- [ ] Navigation works between routes

## File Structure
```
medifly-dashboard-sandbox/
├── dist/                    # Built React app (auto-generated)
├── src/
│   ├── components/
│   │   ├── DashboardFull.tsx
│   │   └── DashboardSimplified.tsx
│   ├── data/
│   │   ├── types.ts
│   │   └── sampleData.ts
│   ├── pages/
│   │   ├── Home.tsx
│   │   └── PhaseOne.tsx
│   ├── App.tsx
│   ├── index.css
│   ├── main.tsx
│   └── router.tsx
├── index.html
├── package.json
├── postcss.config.js
├── tailwind.config.js
├── tsconfig.json
├── tsconfig.node.json
└── vite.config.ts
```

This guide ensures complete functionality of the React dashboard integration with Flask, including all critical fixes for routing, asset serving, and user interaction features.