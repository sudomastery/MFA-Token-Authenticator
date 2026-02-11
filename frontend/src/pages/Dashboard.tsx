import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/stores/authStore";
import { 
  ShieldCheck, 
  LogOut, 
  Download, 
  Copy,
  Check,
  ChevronDown,
  ChevronUp,
  Key,
  Shield
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";

const Dashboard = () => {
  const { user, token, logout, backupCodes } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();
  
  const [showBackupCodes, setShowBackupCodes] = useState(false);
  const [copiedCode, setCopiedCode] = useState<string | null>(null);

  if (!token || !user) {
    navigate("/login");
    return null;
  }

  const handleCopyCode = (code: string) => {
    navigator.clipboard.writeText(code);
    setCopiedCode(code);
    toast({ title: "Copied!", description: "Backup code copied to clipboard" });
    setTimeout(() => setCopiedCode(null), 2000);
  };

  const handleDownloadBackupCodes = () => {
    if (!backupCodes || backupCodes.length === 0) {
      toast({ 
        title: "No backup codes", 
        description: "Backup codes are only available immediately after MFA setup",
        variant: "destructive" 
      });
      return;
    }

    const content = `MFA Backup Codes for ${user.username}
Generated: ${new Date().toLocaleString()}

IMPORTANT: Save these codes in a secure location. Each code can only be used once.

${backupCodes.map((code, i) => `${i + 1}. ${code}`).join('\n')}

---
These codes allow you to recover access if you lose your authenticator device.
Keep them safe and never share them with anyone.
`;

    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `mfa-backup-codes-${user.username}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    toast({ title: "Downloaded!", description: "Backup codes saved to file" });
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-6">
      <div className="w-full max-w-2xl">
        <div className="rounded-2xl border border-border bg-card p-8 sm:p-10 auth-card-shadow">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-accent glow mb-6">
              <Shield className="w-10 h-10 text-primary" />
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold text-foreground mb-2">
              Security Dashboard
            </h1>
            <p className="text-muted-foreground mb-2">
              Welcome, {user.username}!
            </p>
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-accent text-accent-foreground text-sm font-medium">
              <ShieldCheck className="w-4 h-4" />
              {user.mfa_enabled ? "MFA Enabled" : "MFA Not Enabled"}
            </div>
          </div>

          {/* Backup Codes Section */}
          {user.mfa_enabled && backupCodes && backupCodes.length > 0 && (
            <div className="mb-6">
              <div 
                className="flex items-center justify-between p-4 rounded-lg border border-border bg-muted/50 cursor-pointer hover:bg-muted transition-colors"
                onClick={() => setShowBackupCodes(!showBackupCodes)}
              >
                <div className="flex items-center gap-3">
                  <Key className="w-5 h-5 text-primary" />
                  <div>
                    <h3 className="font-semibold text-foreground">Backup Recovery Codes</h3>
                    <p className="text-sm text-muted-foreground">
                      {backupCodes.length} codes available
                    </p>
                  </div>
                </div>
                {showBackupCodes ? (
                  <ChevronUp className="w-5 h-5 text-muted-foreground" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-muted-foreground" />
                )}
              </div>

              {showBackupCodes && (
                <div className="mt-4 p-4 rounded-lg border border-border bg-card space-y-4">
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-muted-foreground">
                      Save these codes in a secure location. Each can only be used once.
                    </p>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleDownloadBackupCodes}
                      className="gap-2"
                    >
                      <Download className="w-4 h-4" />
                      Download
                    </Button>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-2">
                    {backupCodes.map((code, index) => (
                      <div
                        key={index}
                        className="flex items-center justify-between p-3 rounded-lg bg-muted font-mono text-sm"
                      >
                        <span>{code}</span>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-6 w-6"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleCopyCode(code);
                          }}
                        >
                          {copiedCode === code ? (
                            <Check className="h-3 w-3 text-primary" />
                          ) : (
                            <Copy className="h-3 w-3" />
                          )}
                        </Button>
                      </div>
                    ))}
                  </div>

                  <div className="p-3 rounded-lg bg-accent/50 border border-border">
                    <p className="text-xs text-muted-foreground">
                      ⚠️ <strong>Important:</strong> These codes are shown only once after MFA setup. 
                      Download and store them securely. You'll need them if you lose access to your authenticator app.
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* No Backup Codes Warning */}
          {user.mfa_enabled && (!backupCodes || backupCodes.length === 0) && (
            <div className="mb-6 p-4 rounded-lg border border-border bg-muted/50">
              <div className="flex items-start gap-3">
                <Key className="w-5 h-5 text-muted-foreground flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="font-semibold text-foreground mb-1">Backup Codes Not Available</h3>
                  <p className="text-sm text-muted-foreground mb-3">
                    Backup codes are only shown once during MFA setup. If you need new codes, you'll need to reset and re-setup MFA.
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Tip: If you lose access to your authenticator, use the "Lost MFA?" option on the login page with your saved backup codes.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Account Info */}
          <div className="mb-6 p-4 rounded-lg border border-border bg-muted/50">
            <h3 className="font-semibold text-foreground mb-3">Account Information</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Username:</span>
                <span className="font-medium text-foreground">{user.username}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Email:</span>
                <span className="font-medium text-foreground">{user.email}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Two-Factor Auth:</span>
                <span className={`font-medium ${user.mfa_enabled ? 'text-green-600' : 'text-yellow-600'}`}>
                  {user.mfa_enabled ? 'Enabled' : 'Not Enabled'}
                </span>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex flex-col sm:flex-row gap-3">
            {!user.mfa_enabled && (
              <Button
                className="flex-1"
                onClick={() => navigate("/mfa-setup")}
              >
                <ShieldCheck className="mr-2 h-4 w-4" />
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
