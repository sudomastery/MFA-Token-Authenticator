import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import AuthLayout from "@/components/AuthLayout";
import { api } from "@/lib/api";
import { useAuth } from "@/stores/authStore";
import { useToast } from "@/hooks/use-toast";
import { Loader2, Copy, Check, QrCode } from "lucide-react";

const MfaSetup = () => {
  const [qrCode, setQrCode] = useState<string | null>(null);
  const [secret, setSecret] = useState("");
  const [backupCodes, setBackupCodes] = useState<string[]>([]);
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
        setBackupCodes(res.backup_codes || []);
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
      // Ensure token is exactly 6 digits and trimmed
      const cleanToken = token.trim();
      console.log('Verifying MFA with token:', cleanToken, 'length:', cleanToken.length);
      
      if (cleanToken.length !== 6 || !/^\d{6}$/.test(cleanToken)) {
        toast({ 
          title: "Invalid code", 
          description: "Please enter a valid 6-digit code", 
          variant: "destructive" 
        });
        setLoading(false);
        return;
      }
      
      console.log('Sending verify request with payload:', { token: cleanToken });
      await api.mfaVerify({ token: cleanToken }, authToken!);
      
      // Update user in auth context to reflect MFA is now enabled and store backup codes
      if (user) {
        setAuth(authToken!, { ...user, mfa_enabled: true }, backupCodes);
      }
      
      toast({ title: "MFA Enabled!", description: "Your account is now secured with 2FA. Save your backup codes!" });
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
      </div>
    </AuthLayout>
  );
};

export default MfaSetup;
