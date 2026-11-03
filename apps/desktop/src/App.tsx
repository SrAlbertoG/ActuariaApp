import { BrowserRouter, Route, Routes } from "react-router-dom";
import { LoginPage } from "./features/auth/LoginPage";
import { RedirectIfConnected, RequireConnection } from "./features/auth/RouteGuards";
import { SessionGate } from "./features/auth/SessionGate";
import { HomePage } from "./features/home/HomePage";

/** Raíz de la interfaz: arranque con reconexión + rutas protegidas. */
export default function App() {
  return (
    <SessionGate>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<RedirectIfConnected><LoginPage /></RedirectIfConnected>} />
          <Route path="/" element={<RequireConnection><HomePage /></RequireConnection>} />
        </Routes>
      </BrowserRouter>
    </SessionGate>
  );
}