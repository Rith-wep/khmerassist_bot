import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";
import { useAuth } from "./context/AuthContext";
import KnowledgeEditor from "./pages/KnowledgeEditor";
import SignIn from "./pages/SignIn";
import SignUp from "./pages/SignUp";

function App() {
  const { isAuthenticated } = useAuth();

  return (
    <Layout>
      <Routes>
        <Route
          path="/signup"
          element={isAuthenticated ? <Navigate to="/knowledge" replace /> : <SignUp />}
        />
        <Route
          path="/signin"
          element={isAuthenticated ? <Navigate to="/knowledge" replace /> : <SignIn />}
        />
        <Route
          path="/knowledge"
          element={
            <ProtectedRoute>
              <KnowledgeEditor />
            </ProtectedRoute>
          }
        />
        <Route
          path="*"
          element={<Navigate to={isAuthenticated ? "/knowledge" : "/signin"} replace />}
        />
      </Routes>
    </Layout>
  );
}

export default App;
