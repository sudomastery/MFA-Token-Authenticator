import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/context/AuthContext";
import { ShieldCheck, LogOut, Settings } from "lucide-react";

const Dashboard = () => {
  const { user, token, logout } = useAuth();
  const navigate = useNavigate();

  if (!token || !user) {
    navigate("/login");
    return null;
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-6">
      <div className="w-full max-w-lg">
        <div className="rounded-2xl border border-border bg-card p-8 sm:p-10 auth-card-shadow text-center">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-accent glow mb-6">
            <ShieldCheck className="w-10 h-10 text-primary" />
          </div>

          <h1 className="text-2xl sm:text-3xl font-bold text-foreground mb-2">
            Welcome, {user.username}!
          </h1>
          <p className="text-muted-foreground mb-6">
            You have successfully logged in.
          </p>

          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-accent text-accent-foreground text-sm font-medium mb-8">
            <ShieldCheck className="w-4 h-4" />
            {user.mfa_enabled ? "MFA Enabled" : "MFA Not Enabled"}
          </div>

          <div className="flex flex-col sm:flex-row gap-3">
            {!user.mfa_enabled && (
              <Button
                className="flex-1"
                onClick={() => navigate("/mfa-setup")}
              >
                <Settings className="mr-2 h-4 w-4" />
                Enable MFA
              </Button>
            )}
            <Button
              variant="outline"
              className="flex-1"
              onClick={() => {
                logout();
                navigate("/login");
              }}
            >
              <LogOut className="mr-2 h-4 w-4" />
              Sign Out
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
