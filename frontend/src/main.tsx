import { createRoot } from "react-dom/client";
import { RouterProvider } from "@tanstack/react-router";

import "./styles.css";
import { getRouter } from "./router";

const rootElement = document.getElementById("root");

if (!rootElement) throw new Error("NexusAI root element is missing");

createRoot(rootElement).render(<RouterProvider router={getRouter()} />);
