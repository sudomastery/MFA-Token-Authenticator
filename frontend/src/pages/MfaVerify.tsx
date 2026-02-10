import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import AuthLayout from "@/components/AuthLayout";
// 🧪 TEST MODE — swap `mockApi` back to `api` from "@/lib/api" during integration
import { mockApi as api } from "@/lib/mock-api";
import TestBanner from "@/components/TestBanner";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/hooks/use-toast";
import { Loader2, ShieldCheck } from "lucide-react";

const MfaVerify = () => {
  const [token, setToken] = useState("");
  const [loading, setLoading] = useState(false);
  const { tempToken, user, completeMfa } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();

  if (!tempToken) {
    navigate("/login");
    return null;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await api.mfaVerify({ token }, tempToken);
      completeMfa(res.access_token, res.user);
      toast({ title: "Verified!", description: "Welcome back." });
      navigate("/dashboard");
    } catch (err: any) {
      toast({ title: "Invalid code", description: err.message, variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout title="Two-Factor Authentication" subtitle="Enter the code from your authenticator app">
      <div className="flex flex-col items-center mb-8">
        <div className="w-16 h-16 rounded-2xl bg-accent flex items-center justify-center glow mb-4">
          <ShieldCheck className="w-8 h-8 text-primary" />
        </div>
        {user && (
          <p className="text-sm text-muted-foreground">
            Signing in as <span className="font-medium text-foreground">{user.email}</span>
          </p>
        )}
      </div>

      {/* 🧪 TEST MODE — Remove <TestBanner /> during integration */}
      <TestBanner />
      <form onSubmit={handleSubmit} className="space-y-5">
        <div className="space-y-2">
          <Label htmlFor="mfa-token">6-digit code</Label>
          <Input
            id="mfa-token"
            placeholder="000000"
            value={token}
            onChange={(e) => setToken(e.target.value.replace(/\D/g, "").slice(0, 6))}
            className="text-center text-2xl tracking-[0.6em] font-mono h-14"
            maxLength={6}
            autoFocus
            required
          />
        </div>
        <Button type="submit" className="w-full" disabled={loading || token.length !== 6}>
          {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          Verify
        </Button>
      </form>
    </AuthLayout>
  );
};

export default MfaVerify;
