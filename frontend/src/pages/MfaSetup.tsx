import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import AuthLayout from "@/components/AuthLayout";
// 🧪 TEST MODE — swap `mockApi` back to `api` from "@/lib/api" during integration
import { mockApi as api } from "@/lib/mock-api";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/hooks/use-toast";
import { Loader2, Copy, Check, QrCode } from "lucide-react";

const MfaSetup = () => {
  const [qrCode, setQrCode] = useState<string | null>(null);
  const [secret, setSecret] = useState("");
  const [token, setToken] = useState("");
  const [loading, setLoading] = useState(false);
  const [setupLoading, setSetupLoading] = useState(true);
  const [copied, setCopied] = useState(false);
  const { token: authToken, user, setAuth } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();

  useEffect(() => {
    if (!authToken) {
      navigate("/login");
      return;
    }
    const setup = async () => {
      try {
        const res = await api.mfaSetup(authToken);
        setQrCode(res.qr_code);
        setSecret(res.secret);
      } catch (err: any) {
        toast({ title: "MFA Setup failed", description: err.message, variant: "destructive" });
      } finally {
        setSetupLoading(false);
      }
    };
    setup();
  }, [authToken, navigate, toast]);

  const handleCopy = () => {
    navigator.clipboard.writeText(secret);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await api.mfaVerify({ token }, authToken!);
      setAuth(res.access_token, res.user);
      toast({ title: "MFA Enabled!", description: "Your account is now secured with 2FA." });
      navigate("/dashboard");
    } catch (err: any) {
      toast({ title: "Verification failed", description: err.message, variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout title="Set Up MFA" subtitle="Scan the QR code with your authenticator app">
      <div className="space-y-6">
        {/* QR Code display */}
        <div className="flex flex-col items-center p-6 rounded-xl bg-card border border-border auth-card-shadow">
          {setupLoading ? (
            <div className="flex flex-col items-center gap-3 py-8">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
              <p className="text-sm text-muted-foreground">Generating QR code...</p>
            </div>
          ) : qrCode ? (
            <img
              src={qrCode}
              alt="MFA QR Code"
              className="w-48 h-48 rounded-lg bg-white p-2"
            />
          ) : (
            <div className="flex flex-col items-center gap-3 py-8">
              <QrCode className="h-12 w-12 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">QR code unavailable</p>
            </div>
          )}
        </div>

        {/* Secret key */}
        {secret && (
          <div className="space-y-2">
            <Label className="text-xs text-muted-foreground">Or enter this key manually</Label>
            <div className="flex items-center gap-2">
              <code className="flex-1 px-3 py-2 rounded-lg bg-muted text-sm font-mono text-foreground truncate">
                {secret}
              </code>
              <Button type="button" variant="outline" size="icon" onClick={handleCopy}>
                {copied ? <Check className="h-4 w-4 text-primary" /> : <Copy className="h-4 w-4" />}
              </Button>
            </div>
          </div>
        )}

        {/* Token verification */}
        <form onSubmit={handleVerify} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="token">Enter 6-digit code</Label>
            <Input
              id="token"
              placeholder="000000"
              value={token}
              onChange={(e) => setToken(e.target.value.replace(/\D/g, "").slice(0, 6))}
              className="text-center text-lg tracking-[0.5em] font-mono"
              maxLength={6}
              required
            />
          </div>
          <Button type="submit" className="w-full" disabled={loading || token.length !== 6}>
            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Verify & Enable MFA
          </Button>
        </form>

        <Button variant="ghost" className="w-full text-muted-foreground" onClick={() => navigate("/dashboard")}>
          Skip for now
        </Button>
      </div>
    </AuthLayout>
  );
};

export default MfaSetup;
