import { BrowserRouter, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { Layout } from "./components/Layout";
import { HomePage } from "./pages/HomePage";
import { CoachesPage } from "./pages/CoachesPage";
import { CoachDetailPage } from "./pages/CoachDetailPage";
import { ListingPage } from "./pages/ListingPage";
import { RequestsPage } from "./pages/RequestsPage";

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<HomePage />} />
            <Route path="/coaches" element={<CoachesPage />} />
            <Route path="/coaches/:id" element={<CoachDetailPage />} />
            <Route path="/listing" element={<ListingPage />} />
            <Route path="/requests" element={<RequestsPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
