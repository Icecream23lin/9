import AppRoute from "./AppRoute.jsx";
import { BrowserRouter } from "react-router-dom";

function App() {
  if (window.electronAPI) {
    window.electronAPI
      .invoke("backend-port-channel")
      .then((port) => {
        localStorage.setItem("WIL_BACKEND_PORT", port);
      })
      .catch(() => {
        localStorage.setItem("WIL_BACKEND_PORT", 5050);
      });
  } else {
    localStorage.setItem("WIL_BACKEND_PORT", 5050);
  }

  return (
    <>
      <BrowserRouter basename="/">
        <AppRoute />
      </BrowserRouter>
    </>
  );
}

export default App;
