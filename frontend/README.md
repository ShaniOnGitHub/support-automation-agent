# Support Automation Agent Frontend

Modern React frontend for the Support Automation Agent system.

## Tech Stack
- **React** (Vite)
- **Tailwind CSS**
- **Lucide React** (Icons)
- **Axios** (API Client)
- **React Router**

## Getting Started

### Prerequisites
- Node.js (v18 or higher)
- Backend running at `http://localhost:8000` (default)

### Installation
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```

### Configuration
Create a `.env` file in the `frontend` folder if you need to change the API URL:
```env
VITE_API_URL=http://your-backend-api.com/api/v1
```

### Running Locally
Start the development server:
```bash
npm run dev
```

## Features
- **Multi-tenant**: Dashboard to switch between workspaces.
- **AI Co-pilot**: sidebar for triage, suggested replies, and tool execution.
- **Role-based Access**: Admin-only member management and audit logs.
- **Knowledge Base**: Ingest and manage grounding documents for RAG.
- **Responsive Design**: Dark mode support and mobile-aware layout.
