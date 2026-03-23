import { Routes, Route } from "react-router";
import Layout from "./components/Layout";
import Home from "./pages/Home";
import Browse from "./pages/Browse";
import Search from "./pages/Search";
import About from "./pages/About";
import ADCDetail from "./pages/ADCDetail";
import AntibodyDetail from "./pages/AntibodyDetail";
import AntigenDetail from "./pages/AntigenDetail";
import LinkerDetail from "./pages/LinkerDetail";
import PayloadDetail from "./pages/PayloadDetail";
import NotFound from "./pages/NotFound";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Home />} />
        <Route path="browse" element={<Browse />} />
        <Route path="search" element={<Search />} />
        <Route path="about" element={<About />} />
        <Route path="adc/:id" element={<ADCDetail />} />
        <Route path="antibody/:id" element={<AntibodyDetail />} />
        <Route path="antigen/:id" element={<AntigenDetail />} />
        <Route path="linker/:id" element={<LinkerDetail />} />
        <Route path="payload/:id" element={<PayloadDetail />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}
