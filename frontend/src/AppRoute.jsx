import { Route, Routes, useLocation } from "react-router-dom";
import HomePage from "./Pages/HomePage";
import ReportPage from "./Pages/ReportPage";
import UploadPage from "./Pages/UploadPage";
import DisplayPage from "./Pages/DisplayPage";
import { AnimatePresence } from "framer-motion";
import Background from "./Components/Background";
import YoYUploadPage from "./Pages/YoYUploadPage";
function AppRoute() {
  const location = useLocation();
  return (
    <>
      <Background />
      <AnimatePresence mode="wait">
        <Routes key={location.pathname} location={location}>
          <Route path="/" element={<HomePage />} />
          <Route path="/report" element={<ReportPage />}>
            <Route index element={<UploadPage />} />
            <Route path="yoy" element={<YoYUploadPage />} />
            <Route path="display" element={<DisplayPage />} />
          </Route>
        </Routes>
      </AnimatePresence>
    </>
  );
}

export default AppRoute;
