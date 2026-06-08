import { createRoot } from "react-dom/client";
import App from "./app/App.tsx";
import { OperatorSessionProvider } from "./app/components/OperatorSessionContext";
import "./styles/index.css";

createRoot(document.getElementById("root")!).render(
  <OperatorSessionProvider>
    <App />
  </OperatorSessionProvider>,
);
