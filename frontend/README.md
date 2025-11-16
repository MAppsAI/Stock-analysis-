# Stock Analysis Frontend

React + TypeScript frontend for the Stock Analysis application.

## Quick Start

```bash
# Install dependencies
npm install

# Run development server
npm run dev
```

App runs on `http://localhost:3000`

## Build for Production

```bash
npm run build
npm run preview
```

## Project Structure

- `src/components/` - React components
  - `ControlPanel.tsx` - Ticker and date input
  - `ResultsTable.tsx` - Strategy results display
  - `StrategyDrilldown.tsx` - Chart modal
- `src/api.ts` - API client
- `src/types.ts` - TypeScript interfaces
- `src/App.tsx` - Main app component
- `src/main.tsx` - Entry point

## Key Libraries

- **Material-UI**: UI components
- **TanStack Query**: Data fetching and caching
- **Lightweight Charts**: Candlestick charts
- **Axios**: HTTP client
