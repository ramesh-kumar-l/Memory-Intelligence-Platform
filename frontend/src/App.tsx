import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Navigate, Route, BrowserRouter as Router, Routes } from "react-router-dom";

import { Layout } from "./components/Layout";
import { IntelligencePage } from "./pages/IntelligencePage";
import { MemoriesPage } from "./pages/MemoriesPage";
import { SearchPage } from "./pages/SearchPage";
import { SettingsPage } from "./pages/SettingsPage";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Navigate to="/memories" replace />} />
            <Route path="memories" element={<MemoriesPage />} />
            <Route path="search" element={<SearchPage />} />
            <Route path="intelligence" element={<IntelligencePage />} />
            <Route path="settings" element={<SettingsPage />} />
          </Route>
        </Routes>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
