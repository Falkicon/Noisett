# Frontend Implementation

**Status:** Reference

**Framework:** React 18 + TypeScript

**Build Tool:** Vite

---

## Project Setup

```bash
# Initialize
npm create vite@latest frontend -- --template react-ts
cd frontend

# Install dependencies
npm install react-router-dom @tanstack/react-query axios
npm install @azure/msal-browser @azure/msal-react
npm install tailwindcss postcss autoprefixer
```

---

## Project Structure

```
src/
├── components/
│   ├── common/
│   │   ├── Button/
│   │   ├── Input/
│   │   ├── Spinner/
│   │   └── Toast/
│   ├── generation/
│   │   ├── PromptInput.tsx
│   │   ├── ImageGrid.tsx
│   │   ├── ImageCard.tsx
│   │   └── ProgressBar.tsx
│   └── layout/
│       ├── Header.tsx
│       └── PageContainer.tsx
├── pages/
│   ├── GeneratePage.tsx
│   ├── HistoryPage.tsx        # v2.1
│   └── SettingsPage.tsx       # v2.1
├── hooks/
│   ├── useGenerate.ts
│   ├── useJobStatus.ts
│   └── useAuth.ts
├── services/
│   └── api.ts
├── types/
│   └── job.ts
├── styles/
│   └── tokens.css
├── config/
│   └── msalConfig.ts
├── App.tsx
└── main.tsx
```

---

## Key Implementation

### MSAL Configuration

```tsx
// src/config/msalConfig.ts
import { Configuration, PublicClientApplication } from '@azure/msal-browser';

const msalConfig: Configuration = {
  auth: {
    clientId: import.meta.env.VITE_AZURE_CLIENT_ID,
    authority: `[https://login.microsoftonline.com/${import.meta.env.VITE_AZURE_TENANT_ID}`](https://login.microsoftonline.com/${import.meta.env.VITE_AZURE_TENANT_ID}`),
    redirectUri: window.location.origin,
  },
  cache: {
    cacheLocation: 'sessionStorage',
  },
};

export const msalInstance = new PublicClientApplication(msalConfig);

export const loginRequest = {
  scopes: [`api://${import.meta.env.VITE_AZURE_CLIENT_ID}/access_as_user`],
};
```

### API Service

```tsx
// src/services/api.ts
import axios from 'axios';
import { msalInstance } from '../config/msalConfig';

const API_BASE = import.meta.env.VITE_API_URL;

async function getAccessToken(): Promise<string> {
  const accounts = msalInstance.getAllAccounts();
  const response = await msalInstance.acquireTokenSilent({
    scopes: [`api://${import.meta.env.VITE_AZURE_CLIENT_ID}/access_as_user`],
    account: accounts[0],
  });
  return response.accessToken;
}

export const api = {
  async generate(request: GenerateRequest): Promise<Job> {
    const token = await getAccessToken();
    const { data } = await [axios.post](http://axios.post)(`${API_BASE}/generate`, request, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return data;
  },

  async getJobStatus(jobId: string): Promise<JobStatus> {
    const token = await getAccessToken();
    const { data } = await axios.get(`${API_BASE}/jobs/${jobId}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return data;
  },
};
```

### Generation Hook

```tsx
// src/hooks/useGenerate.ts
import { useState, useCallback } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { api } from '../services/api';

export function useGenerate() {
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);

  const generateMutation = useMutation({
    mutationFn: (request: GenerateRequest) => api.generate(request),
    onSuccess: (job) => setCurrentJobId(job.job_id),
  });

  const jobStatusQuery = useQuery({
    queryKey: ['job', currentJobId],
    queryFn: () => api.getJobStatus(currentJobId!),
    enabled: !!currentJobId,
    refetchInterval: (query) => {
      const status = [query.state.data](http://query.state.data)?.status;
      if (status === 'complete' || status === 'failed') return false;
      return 2000; // Poll every 2 seconds
    },
  });

  return {
    generate: (prompt: string) => generateMutation.mutate({ prompt }),
    reset: () => { setCurrentJobId(null); generateMutation.reset(); },
    isGenerating: generateMutation.isPending || 
      [jobStatusQuery.data](http://jobStatusQuery.data)?.status === 'processing',
    progress: [jobStatusQuery.data](http://jobStatusQuery.data)?.progress ?? 0,
    images: [jobStatusQuery.data](http://jobStatusQuery.data)?.images ?? [],
    error: generateMutation.error,
  };
}
```

---

## TypeScript Types

```tsx
// src/types/job.ts
export type JobStatus = 'queued' | 'processing' | 'complete' | 'failed';
export type AssetType = 'icons' | 'product' | 'logo' | 'premium';
export type ModelId = 'hidream' | 'flux' | 'sd35';

export interface GenerateRequest {
  prompt: string;
  asset_type?: AssetType;
  model?: ModelId;
  count?: number;
}

export interface GeneratedImage {
  index: number;
  url: string;
  width: number;
  height: number;
}

export interface Job {
  job_id: string;
  status: JobStatus;
  progress?: number;
  created_at: string;
  images?: GeneratedImage[];
  error?: { code: string; message: string };
}
```

---

## Design Token Integration

```css
/* src/styles/tokens.css */
:root {
  --color-primary: #0078D4;
  --color-primary-hover: #106EBE;
  --color-error: #D13438;
  --color-gray-900: #201F1E;
  --color-gray-100: #F3F2F1;
  --bg-page: #FAF9F8;
  
  --font-family: 'Segoe UI', -apple-system, sans-serif;
  --font-size-base: 15px;
  
  --space-4: 16px;
  --radius-md: 8px;
  --shadow-md: 0 4px 6px rgba(0,0,0,0.07);
}
```

---

## Environment Variables

```bash
# .env.local
VITE_API_URL=[http://localhost:8000/api/v1](http://localhost:8000/api/v1)
VITE_AZURE_CLIENT_ID=your-client-id
VITE_AZURE_TENANT_ID=your-tenant-id
```

---

## Build & Deploy

```bash
# Development
npm run dev

# Production build
npm run build

# Deploy to Azure Static Web Apps
swa deploy ./dist --env production
```