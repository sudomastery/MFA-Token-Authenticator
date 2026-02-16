import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import AuthLayout from "@/components/AuthLayout";
import { api } from "@/lib/api";
import { useAuth } from "@/stores/authStore";
import { useToast } from "@/hooks/use-toast";
import { Loader2, KeyRound } from "lucide-react";

const Login = () => {
  const [form, setForm] = useState({ username: "", password: "", mfa_token: "" });
  const [showMfaInput, setShowMfaInput] = useState(false);
  const [loading, setLoading] = useState(false);
  const [showBackupCodeModal, setShowBackupCodeModal] = useState(false);
  const [backupCodeForm, setBackupCodeForm] = useState({ username: "", backupCode: "" });
  const [backupCodeLoading, setBackupCodeLoading] = useState(false);
  const navigate = useNavigate();
  const { setAuth } = useAuth();
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const payload: any = {
        username: form.username,
        password: form.password,
      };
      
      // Include MFA token if provided
      if (form.mfa_token) {
        payload.mfa_token = form.mfa_token;
        console.log('[LOGIN] Sending MFA token:', form.mfa_token, 'Type:', typeof form.mfa_token, 'Length:', form.mfa_token.length);
      }
      
      console.log('[LOGIN] Full payload:', JSON.stringify(payload));
      console.log('[LOGIN] Calling API login...');
      
      const res = await api.login(payload);
      console.log('[LOGIN] Login response:', res);
      
      // Validate response has required fields
      if (!res || !res.access_token || !res.user) {
        throw new Error('Invalid response from server');
      }
      
      setAuth(res.access_token, res.user);
      
      // Check if user has incomplete MFA setup
      if (res.user.incomplete_mfa) {
        toast({ 
          title: "MFA Setup Incomplete", 
          description: "Please complete your MFA setup.", 
          variant: "default" 
        });
        navigate("/mfa-setup");
        return;
      }
      
      toast({ title: "Welcome back!", description: "Login successful." });
      navigate("/dashboard");
    } catch (err: any) {
      const errorMessage = err.message || "Login failed";
      
      // Check if MFA token is required
      if (errorMessage.includes("MFA token required")) {
        setShowMfaInput(true);
        toast({ 
          title: "MFA Required", 
          description: "Please enter your 6-digit authentication code.", 
          variant: "default" 
        });
      } else {
        toast({ title: "Login failed", description: errorMessage, variant: "destructive" });
      }
    } finally {
      setLoading(false);
    }
  };

  const handleBackupCodeSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBackupCodeLoading(true);
    try {
      // Verify the backup code
      const res = await api.verifyBackupCode(backupCodeForm.username, backupCodeForm.backupCode);
      
      toast({ 
        title: "Backup code verified!", 
        description: "You can now reset your MFA.", 
        variant: "default" 
      });

      // Reset MFA with the temp token
      await api.resetMfa(res.temp_token);

      toast({ 
        title: "MFA Reset Complete", 
        description: "Please set up MFA again.", 
        variant: "default" 
      });

      // Set temp token and user in auth to allow access to MFA setup page
      setAuth(res.temp_token, res.user);

      // Close modal and navigate directly to MFA setup
      setShowBackupCodeModal(false);
      setBackupCodeForm({ username: "", backupCode: "" });
      navigate("/mfa-setup");
    } catch (err: any) {
      const errorMessage = err.message || "Backup code verification failed";
      toast({ title: "Error", description: errorMessage, variant: "destructive" });
    } finally {
      setBackupCodeLoading(false);
    }
  };

  return (
    <AuthLayout title="Welcome back" subtitle="Sign in to your account">
      <form onSubmit={handleSubmit} className="space-y-5">
        <div className="space-y-2">
          <Label htmlFor="username">Username</Label>
          <Input
            id="username"
            placeholder="Enter your username"
            value={form.username}
            onChange={(e) => setForm((f) => ({ ...f, username: e.target.value }))}
            required
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="password">Password</Label>
          <Input
            id="password"
            type="password"
            placeholder="••••••••"
            value={form.password}
            onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
            required
          />
        </div>
        {showMfaInput && (
          <div className="space-y-2">
            <Label htmlFor="mfa-token">6-digit MFA Code</Label>
            <Input
              id="mfa-token"
              placeholder="000000"
              value={form.mfa_token}
              onChange={(e) => setForm((f) => ({ ...f, mfa_token: e.target.value.replace(/\D/g, "").slice(0, 6) }))}
              className="text-center text-lg tracking-[0.5em] font-mono"
              maxLength={6}
              autoFocus
            />
            <Button
              type="button"
              variant="link"
              className="w-full text-sm text-muted-foreground hover:text-primary"
              onClick={() => setShowBackupCodeModal(true)}
            >
              <KeyRound className="mr-2 h-3 w-3" />
              Lost MFA device? Use backup code
            </Button>
          </div>
        )}
        <Button type="submit" className="w-full" disabled={loading}>
          {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          Sign In
        </Button>
        <p className="text-center text-sm text-muted-foreground">
          Don't have an account?{" "}
          <Link to="/register" className="text-primary font-medium hover:underline">
            Sign up
          </Link>
        </p>
      </form>

      {/* Backup Code Recovery Modal */}
      <Dialog open={showBackupCodeModal} onOpenChange={setShowBackupCodeModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <KeyRound className="h-5 w-5" />
              Recover with Backup Code
            </DialogTitle>
            <DialogDescription>
              Enter one of your backup codes to reset MFA. Each code can only be used once.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleBackupCodeSubmit}>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="backup-username">Username</Label>
                <Input
                  id="backup-username"
                  placeholder="johndoe"
                  value={backupCodeForm.username}
                  onChange={(e) => setBackupCodeForm((f) => ({ ...f, username: e.target.value }))}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="backup-code">Backup Code</Label>
                <Input
                  id="backup-code"
                  placeholder="ABCD1234"
                  value={backupCodeForm.backupCode}
                  onChange={(e) => setBackupCodeForm((f) => ({ ...f, backupCode: e.target.value.toUpperCase() }))}
                  className="text-center text-lg tracking-widest font-mono"
                  maxLength={8}
                  required
                />
                <p className="text-xs text-muted-foreground">
                  Enter the 8-character backup code from your saved codes
                </p>
              </div>
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setShowBackupCodeModal(false);
                  setBackupCodeForm({ username: "", backupCode: "" });
                }}
                disabled={backupCodeLoading}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={backupCodeLoading}>
                {backupCodeLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Verify & Reset MFA
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </AuthLayout>
  );
};

export default Login;
